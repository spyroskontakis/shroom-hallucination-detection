"""Reconcile and close only the four already-prepared PG retries.

Preserves blocked audit and all earlier files; final exports use closed/ paths.
"""
import argparse
from collections import Counter
import statistics
import subprocess
import sys
import os
import urllib.request
import urllib.error
import e11c_common as c
import e11c_production as p

STATE=p.PRIVATE/'round_2/batch_001'
BASELINE=c.HERE/'E11C_CLOSURE_PRESERVATION_BASELINE.json'
PREFLIGHT=c.HERE/'E11C_CLOSURE_PREFLIGHT.json'
OLD_AUDIT_SHA='c10f573df6c6040e7139167530e192b8fe90e8a2da4ef07a27e6cdf6c3c6ec53'


def preserve():
    p.preservation()
    c.require(c.sha(c.HERE/'E11C_PRODUCTION_AUDIT.json')==OLD_AUDIT_SHA,'blocked audit anchor')
    p.check_hashes(c.HERE,c.read_json(c.HERE/'E11C_PRODUCTION_STOP_REPORT.json')['artifact_sha256'])
    p.check_hashes(c.HERE,c.read_json(c.HERE/'E11C_PRODUCTION_MANIFEST.json')['files_sha256'])
    if BASELINE.exists():
        p.check_hashes(c.HERE,c.read_json(BASELINE)['files_sha256'])
    p.ignored()


def reconcile_local():
    c.require(p.pilot.protocol()['protocol_sha256']==p.pilot.EXPECTED,'protocol anchor')
    with p.scope():
        report,ledger=p.pilot.results.parse_round(1,write=False)
        _,shard=p.pilot.batch.checked_shard(2,1)
    pending=[r for r in ledger if r['retryable']]
    c.require(len(pending)==4 and all(r['task']=='PG' and r['outcome']=='http_429'
                                    and len(r['history'])==1 for r in pending),'four pending PG 429s')
    keys={r['sample_key'] for r in pending}
    requests=c.read_rows(shard)
    wanted=[r for r in p.candidates() if r['sample_key'] in keys]
    c.require(len(keys)==len(requests)==4 and requests==[c.request(r,p.pilot.protocol(),2) for r in wanted],
              'retry request replay')
    successes=set()
    # Inspect only archived teacher results; no development/gold data involved.
    for base in (p.pilot.PILOT,p.PRIVATE):
        for path in base.glob('round_*/batch_*/*file.jsonl'):
            for raw in c.read_rows(path):
                cid=raw.get('custom_id','')
                outcome,_,_=p.pilot.results.classify(raw,'gpt-5.6-sol')
                if outcome in c.LABELS:
                    successes.add(cid.rsplit('-a',1)[0])
    c.require(not successes & {r['custom_id'].rsplit('-a',1)[0] for r in requests},
              'pending candidate already has successful archived response')
    old=c.read_rows(p.PRIVATE/'full_audit_ledger.jsonl')
    c.require(len(old)==len({r['sample_key'] for r in old})==12000,'old full coverage')
    c.require({r['sample_key'] for r in old if r['retryable']}==keys,'old pending identity')
    return pending,requests


def preflight():
    preserve()
    pending,requests=reconcile_local()
    if not BASELINE.exists():
        paths=[x for x in c.HERE.rglob('*') if x.is_file() and '__pycache__' not in x.parts
               and not x.name.startswith('E11C_CLOSURE_')]
        c.save(BASELINE,{'files_sha256':{str(x.relative_to(c.HERE)):c.sha(x) for x in sorted(paths)}})
    suites=p.tests('CLOSURE_PREFLIGHT')
    preserve()
    # Candidate identities stay in ignored row-level evidence.
    c.save(STATE/'closure_pending_identity.json',{
        'sample_keys':[r['sample_key'] for r in pending],
        'custom_ids':[r['custom_id'] for r in requests]})
    c.save(PREFLIGHT,{'status':'PASS','protocol_sha256':p.pilot.EXPECTED,
        'blocked_audit_sha256':OLD_AUDIT_SHA,'pending':4,'task':'PG',
        'successful_prior_response_overlap':0,'requests_sha256':c.sha(p.PRIVATE/'round_2/requests.jsonl'),
        'preservation_baseline_sha256':c.sha(BASELINE),'test_suites':suites})
    print('Closure preflight PASS: exactly four PG technical failures; no prior successful response overlap.')


def submit():
    c.require(c.read_json(PREFLIGHT)['status']=='PASS','closure preflight required')
    preserve();reconcile_local()
    c.require(not (STATE/'submission.json').exists(),'retry already submitted; download only')
    c.require(not (STATE/'closure_creation_intent.json').exists(),'ambiguous closure POST: reconcile before any action')
    call=p.pilot.batch.api_client(True)
    uploaded=c.read_json(STATE/'uploaded_file.json')
    spec=p.pilot.protocol()
    model=c.strict_json(call('GET','/models/'+spec['teacher']['model']))
    c.require(model['id']==spec['teacher']['model'],'live model mismatch')
    c.save(STATE/'closure_model_metadata.json',model)
    remote=[];after=''
    while True:
        page=c.strict_json(call('GET','/batches?limit=100'+after))
        remote.extend(page['data'])
        if not page.get('has_more'):break
        c.require(bool(page['data']),'empty paginated batch listing')
        after='&after='+page['data'][-1]['id']
    matches=[b for b in remote if b['input_file_id']==uploaded['id']]
    # A foreign upload with the same frozen round metadata also requires reconciliation.
    aliases=[b for b in remote if (b.get('metadata') or {}).get('protocol')==p.pilot.EXPECTED
             and (b.get('metadata') or {}).get('attempt')=='2']
    c.save(STATE/'closure_remote_reconciliation.json',{
        'checked_utc':p.pilot.batch.now(),'listed_count':len(remote),
        'matching_file_batches':matches,'matching_round_batches':aliases})
    c.require(not matches and not aliases,'existing remote retry Batch; STOP to reconcile, do not resubmit')
    file_info=c.strict_json(call('GET','/files/'+uploaded['id']))
    c.require(file_info['purpose']=='batch' and file_info.get('status')=='processed','remote file not processed')
    remote_bytes=call('GET','/files/'+uploaded['id']+'/content')
    c.require(remote_bytes==(p.PRIVATE/'round_2/batch_001.jsonl').read_bytes(),'remote uploaded request bytes drift')
    c.save(STATE/'closure_creation_intent.json',{'created_utc':p.pilot.batch.now(),
        'input_file_id':uploaded['id'],'request_sha256':c.digest(remote_bytes),
        'prior_remote_matches':0,'requests':4})
    body={'input_file_id':uploaded['id'],'endpoint':'/v1/responses','completion_window':'24h',
          'metadata':{'experiment':'E11-C','protocol':p.pilot.EXPECTED,'attempt':'2','shard':'1'}}
    req=urllib.request.Request('https://api.openai.com/v1/batches',data=c.encoded(body),method='POST',
        headers={'Authorization':'Bearer '+os.environ['OPENAI_API_KEY'],'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=120) as reply: batch=c.strict_json(reply.read())
    except urllib.error.HTTPError as exc:
        data=exc.read();c.write_once(STATE/'closure_creation_error.json',data)
        error=c.strict_json(data).get('error',{})
        print(c.json.dumps({'http_status':exc.code,'code':error.get('code'),'message':error.get('message')}))
        raise SystemExit(2)
    intent=c.read_json(STATE/'submission_intent.json')
    c.save(STATE/'submission.json',{'batch_id':batch['id'],'input_file_id':uploaded['id'],
                                    **intent,'api_batch':batch})
    print('Submitted exactly four PG retries:',batch['id'])


def finalize():
    preserve()
    with p.scope():
        report,production=p.pilot.results.parse_round(2,write=True)
    c.require(report['retryable']==0 and all(r['outcome'] in c.LABELS for r in production),
              'four retry responses must all be terminal semantic answers')
    pool,_,pilot=p.partition()
    by_key={r['sample_key']:r for r in pilot+production}
    c.require(len(by_key)==12000 and set(by_key)=={r['sample_key'] for r in pool},'final coverage')
    full=[by_key[r['sample_key']] for r in pool]
    old=c.read_rows(p.PRIVATE/'full_audit_ledger.jsonl')
    pending={r['sample_key'] for r in old if r['retryable']}
    changed={a['sample_key'] for a,b in zip(old,full) if a!=b}
    c.require(changed==pending and len(changed)==4,'only four pending outcomes may change')
    for a,b in zip(old,full):
        if a['sample_key'] in pending:
            c.require(b['history'][:-1]==a['history'] and len(b['history'])==2,'retry history preservation')
    closed=p.PRIVATE/'closed'
    c.write_once(closed/'full_audit_ledger.jsonl',c.rows_bytes(full))
    binary=[r['synthetic'] for r in full if r['accepted']]
    c.require(all(r['llm_label'] in c.LABELS[:2] for r in binary),'binary label allowlist')
    c.write_once(closed/'future_binary_supervision.jsonl',c.rows_bytes(binary))
    prior_labels=c.read_rows(p.PRIVATE/'parsed_labels.jsonl')
    raw_path=STATE/'output_file.jsonl'; raws=c.read_rows(raw_path)
    answers=[]
    for row in full:
        if row['sample_key'] not in pending:continue
        h=row['history'][-1]
        raw=c.strict_json((c.HERE/h['raw_response_path']).read_bytes().splitlines()[h['raw_response_line']-1])
        outcome,retry,answer=p.pilot.results.classify(raw,'gpt-5.6-sol')
        c.require(outcome==row['outcome'] and not retry,'retry answer replay')
        answers.append({'sample_key':row['sample_key'],'task':row['task'],'label':answer['label'],
                        'reason':answer['reason'],'accepted':row['accepted'],
                        'protocol_sha256':p.pilot.EXPECTED,**h})
    all_labels={r['sample_key']:r for r in prior_labels+answers}
    c.require(len(all_labels)==12000,'all labels exactly once')
    c.write_once(closed/'parsed_labels.jsonl',c.rows_bytes([all_labels[r['sample_key']] for r in pool]))
    c.write_once(closed/'four_retry_labels.jsonl',c.rows_bytes(answers))
    old_audit=c.read_json(c.HERE/'E11C_PRODUCTION_AUDIT.json')
    usages=[];models=set();batches=[];stage_usage={'pilot':[],'original_production':[],'retry':[]}
    for stage,base,n in [('pilot',p.pilot.PILOT,1),('original_production',p.PRIVATE,1),('retry',p.PRIVATE,2)]:
        folder=base/f'round_{n}'
        for i,_ in enumerate(c.read_json(folder/'request_manifest.json')['shards'],1):
            receipt=c.read_json(folder/f'batch_{i:03d}/download_receipt.json');batch=receipt['batch']
            batches.append({'stage':stage,'round':n,**{k:batch.get(k) for k in
                ('id','status','request_counts','created_at','completed_at')}})
            for entry in receipt['files']:
                for raw in c.read_rows(folder/f'batch_{i:03d}'/entry['path']):
                    body=(raw.get('response') or {}).get('body') or {}
                    if body.get('model'):models.add(body['model'])
                    u=body.get('usage')
                    if u:stage_usage[stage].append({'input':u['input_tokens'],'output':u['output_tokens'],
                        'reasoning':u['output_tokens_details']['reasoning_tokens'],
                        'cached':u['input_tokens_details']['cached_tokens']})
    def metrics(rows):
        totals={k:sum(r[k] for r in rows) for k in ('input','output','reasoning','cached')}
        tokens=[r['input']+r['output'] for r in rows]
        price=p.pilot.protocol()['pricing']
        return {**totals,'usage_records':len(rows),'total_tokens':sum(tokens),
            'mean_tokens_per_request':statistics.mean(tokens),'median_tokens_per_request':statistics.median(tokens),
            'max_output_tokens_per_request':max(r['output'] for r in rows),
            'estimated_cost_usd':(totals['input']*price['standard_input_per_million']+
                                  totals['output']*price['standard_output_per_million'])/1e6*price['batch_discount']}
    stats={stage:metrics(rows) for stage,rows in stage_usage.items()}
    stats['combined']=metrics(sum(stage_usage.values(),[]))
    c.require(stats['retry']['usage_records']==4 and stats['combined']['usage_records']==12000,'usage coverage')
    c.require(models=={'gpt-5.6-sol'},'returned models')
    suites=p.tests('CLOSURE_FINAL')
    preserve()
    counts=Counter(r['outcome'] for r in full)
    histories=[h for r in full for h in r['history']]
    audit={'status':'PASS','closed':True,'protocol_sha256':p.pilot.EXPECTED,
        'requested_teacher_model':'gpt-5.6-sol','returned_model_ids':sorted(models),'reasoning_effort':'medium',
        'pilot_count':300,'production_count':11700,'total_coverage':12000,'duplicates':0,'missing':0,
        'production_rounds':2,'batches':batches,'retry_batch_id':c.read_json(STATE/'submission.json')['batch_id'],
        'retry_labels_in_frozen_candidate_order':[r['label'] for r in answers],
        'per_task_counts':dict(Counter(r['task'] for r in full)),
        'by_task':{t:{label:sum(r['task']==t and r['outcome']==label for r in full) for label in c.LABELS} for t in c.POLICY},
        'labels':dict(counts),'uncertain_percent':100*counts['uncertain']/12000,'pending':0,
        'successful_structured_responses':12000,'definitive_labels':len(binary),
        'request_failures':sum(h['outcome'] not in c.LABELS for h in histories),'retry_count':4,
        'schema_failures':sum(h['outcome']=='invalid_schema' for h in histories),'terminal_failures':0,
        'usage':stats,'cost_basis':old_audit['cost_basis'],
        'preservation':{**old_audit['preservation'],'original_production_artifacts_unchanged':True,
            'prior_successful_labels_unchanged':True,'only_four_pending_outcomes_changed':True},
        'actions':{**old_audit['actions'],'contrastive_learning':False},'test_suites':suites,
        'previous_blocked_audit_sha256':OLD_AUDIT_SHA,
        'git_status_short':subprocess.run(['git','status','--short'],capture_output=True,text=True,check=True).stdout.splitlines()}
    c.save(c.HERE/'E11C_PRODUCTION_CLOSED_AUDIT.json',audit)
    c.write_once(c.HERE/'E11C_PRODUCTION_CLOSED_AUDIT.md',
        ('# E11-C closed production audit\n\nAll four pending PG requests completed. All 12,000 candidates have terminal labels.\n\n```json\n'+c.json.dumps(audit,indent=2)+'\n```\n').encode())
    paths=[c.HERE/'E11C_PRODUCTION_CLOSED_AUDIT.json',c.HERE/'E11C_PRODUCTION_CLOSED_AUDIT.md',
           BASELINE,PREFLIGHT,c.HERE/'close_e11c_retry.py',c.HERE/'test_e11c_closure.py']
    paths+=list(closed.glob('*'))
    paths+=[x for x in (p.PRIVATE/'round_2').rglob('*') if x.is_file()]
    c.save(c.HERE/'E11C_PRODUCTION_CLOSED_MANIFEST.json',{'protocol_sha256':p.pilot.EXPECTED,
        'files_sha256':{str(x.relative_to(c.HERE)):c.sha(x) for x in paths},
        'original_production_manifest_sha256':c.sha(c.HERE/'E11C_PRODUCTION_MANIFEST.json')})
    print(c.json.dumps({k:v for k,v in audit.items() if k not in ('batches','test_suites')},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('preflight','submit','finalize'))
    args=parser.parse_args()
    {'preflight':preflight,'submit':submit,'finalize':finalize}[args.action]()
