"""Offline parsing/replay of archived Responses Batch results; no API calls."""
import argparse
from collections import Counter
from e11c_common import *


def classify(raw,model):
    """Return outcome, retryability, optional strict semantic label."""
    error=raw.get('error')
    if error:
        code=error.get('code')
        retry=code in {'batch_expired','batch_cancelled','request_timeout','server_error',
                       'rate_limit_exceeded','internal_error','transport_error'}
        return 'api_failure:'+str(code),retry,None
    response=raw.get('response')
    if not response:
        return 'missing_output',True,None
    status=response.get('status_code')
    if status != 200:
        return 'http_'+str(status),status in (408,429) or (type(status) is int and 500<=status<600),None
    body=response.get('body')
    if not isinstance(body,dict):
        return 'missing_output',True,None
    require(body.get('model')==model,'response model mismatch: quarantine and stop')
    require(isinstance(body.get('id'),str) and body['id'],'response identity missing')
    if body.get('status')!='completed':
        return 'incomplete_output',True,None
    output=body.get('output',[])
    if not isinstance(output,list) or not all(isinstance(x,dict) for x in output):
        return 'invalid_schema',True,None
    messages=[x for x in output if x.get('type')=='message']
    if any(not isinstance(m.get('content'),list) or
           not all(isinstance(c,dict) for c in m['content']) for m in messages):
        return 'invalid_schema',True,None
    if any(c.get('type')=='refusal' for m in messages for c in m.get('content',[])):
        return 'refusal',False,None
    texts=[c.get('text') for m in messages if m.get('role')=='assistant'
           for c in m.get('content',[]) if c.get('type')=='output_text']
    if not texts:
        return 'missing_output',True,None
    try:
        require(len(messages)==1 and len(texts)==1,'multiple answers')
        obj=strict_json(texts[0])
        require(isinstance(obj,dict) and set(obj)=={'label','reason'},'strict output fields')
        require(obj['label'] in LABELS and type(obj['reason']) is str and
                1<=len(obj['reason'])<=240 and obj['reason'].strip(),'strict output values')
    except (ValueError,TypeError,KeyError):
        return 'invalid_schema',True,None
    return obj['label'],False,obj


def parse_round(attempt,write=True):
    require(attempt in (1,2,3),'attempt range')
    spec=load_protocol()
    candidates=load_candidates()
    by_key={r['sample_key']:r for r in candidates}
    prior={}
    if attempt>1:
        _,previous=parse_round(attempt-1,write=False)
        prior={r['sample_key']:r for r in previous}
    wanted=[r for r in candidates if not prior or prior[r['sample_key']]['retryable']]
    folder=PRIVATE/f'round_{attempt}'
    manifest=read_json(folder/'request_manifest.json')
    requests=read_rows(folder/'requests.jsonl')
    require(manifest['protocol_sha256']==spec['protocol_sha256'] and
            sha(folder/'requests.jsonl')==manifest['requests_sha256'] and
            requests==[request(r,spec,attempt) for r in wanted], 'request replay integrity')
    expected={r['custom_id']:r for r in requests}
    require(len(expected)==len(requests),'duplicate custom IDs')
    records={}
    response_ids=set()
    provenance={}
    terminal_times=[]
    seen_shard_ids=[]
    for i,shard in enumerate(manifest['shards'],1):
        require(shard['path']==f'batch_{i:03d}.jsonl','shard path')
        path=folder/shard['path']
        require(sha(path)==shard['sha256'],'shard hash')
        shard_rows=read_rows(path)
        require(shard_rows==requests[(i-1)*500:i*500],'shard coverage/order')
        ids={r['custom_id'] for r in shard_rows}
        seen_shard_ids.extend(r['custom_id'] for r in shard_rows)
        state=folder/f'batch_{i:03d}'
        submission=read_json(state/'submission.json')
        receipt=read_json(state/'download_receipt.json')
        batch=receipt['batch']
        require(batch['status'] in ('completed','expired','cancelled') and
                batch['id']==submission['batch_id'] and
                batch['input_file_id']==submission['input_file_id'] and
                batch['endpoint']=='/v1/responses' and
                receipt['request_sha256']==submission['request_sha256']==sha(path) and
                receipt['protocol_sha256']==submission['protocol_sha256']==spec['protocol_sha256'],
                'terminal receipt mismatch')
        metadata=read_json(state/'model_metadata.json')
        require(metadata['id']==spec['teacher']['model'],'metadata model')
        terminal_times.append(receipt['terminal_observed_utc'])
        file_ids=set()
        for entry in receipt['files']:
            require(entry['path'] in ('output_file.jsonl','error_file.jsonl'),'raw path allowlist')
            field=entry['path'].replace('.jsonl','_id')
            require(entry['file_id']==batch.get(field) and entry['file_id'] not in file_ids,'raw file ID')
            file_ids.add(entry['file_id'])
            raw_path=state/entry['path']
            require(sha(raw_path)==entry['sha256'],'raw file hash')
            lines=raw_path.read_bytes().splitlines()
            for line_no,line in enumerate(lines,1):
                raw=strict_json(line)
                cid=raw.get('custom_id')
                require(cid in ids and cid not in records,'foreign/duplicate response custom ID')
                body=(raw.get('response') or {}).get('body')
                if isinstance(body,dict) and body.get('id'):
                    require(body['id'] not in response_ids,'duplicate response identity')
                    response_ids.add(body['id'])
                records[cid]=raw
                provenance[cid]={'raw_response_path':str(raw_path.relative_to(HERE)),
                                 'raw_response_file_sha256':entry['sha256'],
                                 'raw_response_line':line_no,'raw_response_line_sha256':digest(line),
                                 'batch_id':batch['id']}
        require(file_ids=={batch[f] for f in ('output_file_id','error_file_id') if batch.get(f)},
                'missing raw result file')
        if batch['status']=='completed':
            require(ids<=records.keys(),'completed batch missing rows: do not silently retry')
    require(seen_shard_ids==list(expected),'missing/extra request shard')
    ledger=dict(prior)
    for row in wanted:
        cid=request(row,spec,attempt)['custom_id']
        raw=records.get(cid)
        if raw is None:
            outcome,retry,label='missing_output',True,None
        else:
            outcome,retry,label=classify(raw,spec['teacher']['model'])
        entry={'sample_key':row['sample_key'],'task':row['task'],'attempt':attempt,
               'request_custom_id':cid,'outcome':outcome,'retryable':bool(retry and attempt<3),
               'accepted':outcome in LABELS[:2],
               'history':prior.get(row['sample_key'],{}).get('history',[])+[
                   {'attempt':attempt,'request_custom_id':cid,'outcome':outcome,
                    **provenance.get(cid,{})}]}
        if label and entry['accepted']:
            body=raw['response']['body']
            entry['synthetic']={'source':'llm_synthetic','sample_key':row['sample_key'],
               'task':row['task'],'reference_field':POLICY[row['task']],
               'reference_text':row['reference_text'],'whole_hypothesis':row['whole_hypothesis'],
               'reference_text_sha256':digest(row['reference_text'].encode()),
               'hypothesis_text_sha256':digest(row['whole_hypothesis'].encode()),
               'llm_label':label['label'],'llm_reason':label['reason'],
               'label':int(label['label']=='hallucination'),'teacher_model_id':body['model'],
               'prompt_sha256':spec['prompt_sha256'],'request_custom_id':cid,
               'response_id':body['id'],'candidate_pool_sha256':spec['candidates']['sha256'],
               **provenance[cid]}
        ledger[row['sample_key']]=entry
    require(set(ledger)==set(by_key),'global ledger must account for all 12000 candidates')
    ordered=[ledger[r['sample_key']] for r in candidates]
    report={'status':'PASS','attempt':attempt,'protocol_sha256':spec['protocol_sha256'],
            'rows':len(ordered),'accepted':sum(r['accepted'] for r in ordered),
            'retryable':sum(r['retryable'] for r in ordered),
            'outcomes':dict(Counter(r['outcome'] for r in ordered)),
            'terminal_observed_utc':max(terminal_times) if terminal_times else
                read_json(PRIVATE/f'round_{attempt-1}/parse_report.json')['terminal_observed_utc']}
    if write:
        write_once(folder/'ledger.jsonl',rows_bytes(ordered))
        save(folder/'parse_report.json',report)
    return report,ordered


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--attempt',type=int,choices=(1,2,3),required=True)
    print(json.dumps(parse_round(parser.parse_args().attempt)[0],indent=2))
