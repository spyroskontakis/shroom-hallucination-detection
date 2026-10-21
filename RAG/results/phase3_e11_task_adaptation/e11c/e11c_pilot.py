"""Isolated 300-key operational pilot; reuses frozen request/Batch/parser helpers.

No teacher settings change. API calls require --execute-api. Never submits the
full pool. Reusable labels retain the original full-pool custom IDs/provenance.
"""
import argparse
import statistics
from collections import Counter
from contextlib import contextmanager
import e11c_common as c
import e11c_batch as batch
import build_e11c_requests as requests
import parse_e11c_results as results

EXPECTED='792bbe4ef1d0752e606c81dc511684f7bb0a051b2a5c24a937c49d7cb928f818'
PILOT=c.PRIVATE/'pilot_300'
MANIFEST=c.HERE/'E11C_PILOT_SELECTION_MANIFEST.json'


def protocol():
    spec=c.load_protocol()
    c.require(spec['protocol_sha256']==EXPECTED,'pilot frozen protocol SHA mismatch')
    c.require(spec['prompt_sha256']==c.digest(c.PROMPT.encode()),'prompt SHA mismatch')
    return spec


def choose():
    protocol()
    pool=c.load_candidates()
    rows=[]
    for task in c.POLICY:
        rows.extend(sorted((r for r in pool if r['task']==task),key=c.rank)[:100])
    c.require(len(rows)==len({r['sample_key'] for r in rows})==300,'pilot count/uniqueness')
    c.require(Counter(r['task'] for r in rows)=={'DM':100,'MT':100,'PG':100},'pilot quotas')
    return rows


def candidates():
    rows=c.read_rows(PILOT/'candidates.jsonl')
    manifest=c.read_json(MANIFEST)
    c.require(rows==choose(),'pilot selection replay')
    c.require(c.sha(PILOT/'candidates.jsonl')==manifest['candidate_sha256'],'pilot candidate SHA')
    c.require(manifest['protocol_sha256']==EXPECTED and manifest['selected_sample_keys']==
              [r['sample_key'] for r in rows],'pilot manifest drift')
    return rows


@contextmanager
def scope():
    """Bind existing helpers to validated pilot inputs; always restore on exit.

    Common protocol and request formatting remain untouched. This is a local,
    single-process execution context, not a protocol override.
    """
    protocol(); candidates()
    saved=[]
    try:
        for module in (batch,requests,results):
            for name,value in [('PRIVATE',PILOT),('load_candidates',candidates),('load_protocol',protocol)]:
                saved.append((module,name,getattr(module,name)))
                setattr(module,name,value)
        yield
    finally:
        for module,name,value in reversed(saved): setattr(module,name,value)


def prepare():
    spec=protocol(); rows=choose()
    c.write_once(PILOT/'candidates.jsonl',c.rows_bytes(rows))
    c.save(MANIFEST,{'protocol_sha256':EXPECTED,'prompt_sha256':spec['prompt_sha256'],
        'teacher_model':spec['teacher']['model'],'rows':300,'tasks':{'DM':100,'MT':100,'PG':100},
        'selection':'First 100/task in the original E11-C stable hash order; no new hash salt',
        'candidate_pool_sha256':spec['candidates']['sha256'],
        'candidate_path':str((PILOT/'candidates.jsonl').relative_to(c.HERE)),
        'candidate_sha256':c.sha(PILOT/'candidates.jsonl'),
        'selected_sample_keys':[r['sample_key'] for r in rows],
        'selected_keys_sha256':c.digest(c.encoded([r['sample_key'] for r in rows])),
        'reuse':'Original custom IDs; preserve definitive and uncertain results; never relabel valid answers.'})
    with scope(): manifest=requests.build(1)
    c.require(manifest['rows']==300 and len(manifest['shards'])==1,'pilot single batch')
    expected=[c.request(r,spec) for r in rows]
    c.require(c.read_rows(PILOT/'round_1/requests.jsonl')==expected,'frozen request replay')
    for req in expected:
        c.require(set(c.strict_json(req['body']['input'][0]['content']))==
                  {'task','reference','hypothesis'},'input allowlist')
    c.save(c.HERE/'E11C_PILOT_LOCAL_VALIDATION.json',{
        'status':'PASS','rows':300,'unique_keys':300,'tasks':{'DM':100,'MT':100,'PG':100},
        'membership':'PASS','reference_policy':'PASS','prompt_schema_model':'PASS',
        'input_allowlist':'PASS','protocol_sha256':EXPECTED,
        'requests_sha256':c.sha(PILOT/'round_1/requests.jsonl'),
        'request_bodies':'Identical to corresponding frozen full-pool requests',
        'selection_manifest_sha256':c.sha(MANIFEST)})
    print('Pilot preparation PASS: 300 unique keys, 100 per task; frozen request bodies unchanged')


def run_action(action,attempt,execute=False):
    with scope():
        if action=='submit':
            batch.submit(attempt,1,execute)
        elif action=='download':
            batch.download(attempt,1,execute)
        elif action=='parse':
            report,_=results.parse_round(attempt)
            print(c.json.dumps(report,indent=2))
        elif action=='prepare-retry':
            c.require(attempt in (2,3),'retry round')
            prior,_=results.parse_round(attempt-1,write=False)
            c.require(prior['retryable']>0,'no retryable rows; do not create another round')
            requests.build(attempt)
        else: raise ValueError('unknown action')


def audit(attempt):
    spec=protocol()
    by_key={r['sample_key']:r for r in candidates()}
    with scope(): report,ledger=results.parse_round(attempt,write=False)
    c.require(report['retryable']==0,'pilot not final; frozen operational retries remain')
    inputs=[]; outputs=[]; reasoning=[]; cached=[]; missing_usage=0; attempted=0
    timings=[]; raw_files={}; submitted_ids=set()
    for n in range(1,attempt+1):
        folder=PILOT/f'round_{n}'; reqs=c.read_rows(folder/'requests.jsonl')
        attempted+=len(reqs)
        for req in reqs:
            c.require(req['custom_id'] not in submitted_ids,'duplicate attempt identity')
            submitted_ids.add(req['custom_id'])
        receipt=c.read_json(folder/'batch_001/download_receipt.json'); b=receipt['batch']
        timings.append({k:b.get(k) for k in ('id','status','created_at','in_progress_at',
            'finalizing_at','completed_at','expired_at','cancelled_at','request_counts')})
        for entry in receipt['files']:
            path=folder/'batch_001'/entry['path']; raw_files[str(path.relative_to(c.HERE))]=c.sha(path)
            for raw in c.read_rows(path):
                body=(raw.get('response') or {}).get('body') or {}
                usage=body.get('usage')
                if not usage: missing_usage+=1; continue
                for key in ('input_tokens','output_tokens'):
                    c.require(type(usage.get(key)) is int and usage[key]>=0,'invalid usage')
                inputs.append(usage['input_tokens']); outputs.append(usage['output_tokens'])
                reasoning.append((usage.get('output_tokens_details') or {}).get('reasoning_tokens'))
                cached.append((usage.get('input_tokens_details') or {}).get('cached_tokens'))
    missing_usage=attempted-len(inputs)
    semantic=sum(r['outcome'] in c.LABELS for r in ledger)
    by_task={task:{label:sum(r['task']==task and r['outcome']==label for r in ledger)
                   for label in c.LABELS} for task in c.POLICY}
    counts={label:sum(r['outcome']==label for r in ledger) for label in c.LABELS}
    price=spec['pricing']
    standard=(sum(inputs)*price['standard_input_per_million']+
              sum(outputs)*price['standard_output_per_million'])/1e6
    cost=standard*price['batch_discount']
    labels=[]
    for row in ledger:
        if row['outcome'] not in c.LABELS: continue
        history=row['history'][-1]
        raw_path=c.HERE/history['raw_response_path']
        raw=c.strict_json(raw_path.read_bytes().splitlines()[history['raw_response_line']-1])
        _,_,answer=results.classify(raw,spec['teacher']['model'])
        original=by_key[row['sample_key']]
        labels.append({'sample_key':row['sample_key'],'task':row['task'],
            'label':answer['label'],'reason':answer['reason'],'accepted':row['accepted'],
            'teacher_model_id':raw['response']['body']['model'],
            'response_id':raw['response']['body']['id'],'protocol_sha256':EXPECTED,
            'prompt_sha256':spec['prompt_sha256'],'candidate_pool_sha256':spec['candidates']['sha256'],
            'reference_field':c.POLICY[row['task']],
            'reference_text_sha256':c.digest(original['reference_text'].encode()),
            'hypothesis_text_sha256':c.digest(original['whole_hypothesis'].encode()),
            **history,**({'synthetic':row['synthetic']} if row['accepted'] else {})})
    c.write_once(PILOT/'parsed_labels.jsonl',c.rows_bytes(labels))
    metrics={'status':'PASS' if semantic==300 and not missing_usage else 'FAIL',
        'model':spec['teacher']['model'],'protocol_sha256':EXPECTED,
        'pilot_samples':300,'attempted_requests':attempted,'successful_schema_valid_samples':semantic,
        'failed_samples':300-semantic,'retries':attempted-300,
        'schema_failures':sum(h['outcome']=='invalid_schema' for r in ledger for h in r['history']),
        'labels':counts,'by_task':by_task,'uncertain_percent':100*counts['uncertain']/300,
        'usage_records':len(inputs),'missing_usage_records':missing_usage,
        'input_tokens':sum(inputs),'output_tokens':sum(outputs),
        'reasoning_tokens':sum(reasoning) if reasoning and all(x is not None for x in reasoning) else None,
        'cached_input_tokens':sum(cached) if cached and all(x is not None for x in cached) else None,
        'input_mean_per_attempt':sum(inputs)/attempted,'input_median_reported_requests':statistics.median(inputs) if inputs else None,
        'output_mean_per_attempt':sum(outputs)/attempted,'output_median_reported_requests':statistics.median(outputs) if outputs else None,
        'output_max_reported_requests':max(outputs) if outputs else None,
        'pilot_batch_cost_estimate_usd':cost,'full_12000_batch_extrapolation_usd':cost*40,
        'cost_basis':'Returned usage; frozen $4/M input, $20/M output, Batch 50%; no cache discount; not invoice verified. Extrapolation includes observed retries, not guaranteed.',
        'timings':timings,'per_request_latency':'Not exposed by Batch; batch lifecycle timestamps recorded',
        'protocol_tuned':False,'training':False,'development_evaluation':False,
        'official_test_access':False,'commit':False,'push':False}
    c.save(c.HERE/'E11C_PILOT_AUDIT.json',metrics)
    manifest={'protocol_sha256':EXPECTED,'selection_manifest_sha256':c.sha(MANIFEST),
        'candidate_list_sha256':c.sha(PILOT/'candidates.jsonl'),
        'request_files':{str((PILOT/f'round_{n}/requests.jsonl').relative_to(c.HERE)):
                         c.sha(PILOT/f'round_{n}/requests.jsonl') for n in range(1,attempt+1)},
        'raw_response_files':raw_files,'parsed_labels_sha256':c.sha(PILOT/'parsed_labels.jsonl'),
        'audit_sha256':c.sha(c.HERE/'E11C_PILOT_AUDIT.json'),
        'reuse':'Import this validated pilot ledger into eventual full-pool results; exclude terminal semantic answers from future submissions.'}
    c.save(c.HERE/'E11C_PILOT_MANIFEST.json',manifest)
    c.write_once(c.HERE/'E11C_PILOT_MANIFEST.sha256',(c.sha(c.HERE/'E11C_PILOT_MANIFEST.json')+'\n').encode())
    print(c.json.dumps(metrics,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('prepare','submit','download','parse','prepare-retry','audit'))
    p.add_argument('--attempt',type=int,choices=(1,2,3),default=1)
    p.add_argument('--execute-api',action='store_true')
    a=p.parse_args()
    if a.action=='prepare': prepare()
    elif a.action=='audit': audit(a.attempt)
    else: run_action(a.action,a.attempt,a.execute_api)
