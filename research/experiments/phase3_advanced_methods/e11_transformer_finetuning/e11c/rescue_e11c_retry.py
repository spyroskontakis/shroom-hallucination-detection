"""Alternate billing transport for the existing four-request closure.

No request regeneration or protocol changes. Credentials exist only in the
outgoing authorization header; persisted API metadata uses field allowlists.
"""
import argparse
import os
import urllib.error
import urllib.request
import uuid
import close_e11c_retry as r

c=r.c
p=r.p
STATE=r.STATE
PREFIX='E11C_RESCUE'
FACT='final rescue retry executed with alternate API billing project/account'
BATCH_FIELDS=('id','input_file_id','endpoint','completion_window','status',
              'output_file_id','error_file_id','created_at','in_progress_at',
              'finalizing_at','completed_at','failed_at','expired_at','cancelled_at','request_counts')


def api(method, endpoint, data=None, content_type='application/json'):
    c.require(endpoint.startswith(('/models/','/files','/batches')),'endpoint allowlist')
    # Never inspect or serialize the credential, HTTP headers, or exception repr.
    req=urllib.request.Request('https://api.openai.com/v1'+endpoint,data=data,method=method,
        headers={'Authorization':'Bearer '+os.environ['OPENAI_API_KEY'],'Content-Type':content_type})
    try:
        with urllib.request.urlopen(req,timeout=120) as response:return response.read()
    except urllib.error.HTTPError as exc:
        code=None
        try:code=c.strict_json(exc.read()).get('error',{}).get('code')
        except (ValueError,TypeError):pass
        safe_code=code if code in ('billing_hard_limit_reached','insufficient_quota','model_not_found') else 'other_http_error'
        raise RuntimeError(f'HTTP {exc.code}: {safe_code}') from None
    except (urllib.error.URLError,TimeoutError):
        raise RuntimeError('API transport failure; reconcile before repeating any POST') from None


def preserve():
    r.preserve()
    p.check_hashes(c.HERE,c.read_json(c.HERE/'E11C_CLOSURE_ATTEMPT_MANIFEST.json')['files_sha256'])
    baseline=c.HERE/f'{PREFIX}_PRESERVATION_BASELINE.json'
    if baseline.exists():p.check_hashes(c.HERE,c.read_json(baseline)['files_sha256'])


def preflight():
    preserve()
    pending,requests=r.reconcile_local()
    c.require(len(pending)==len(requests)==4,'rescue quota')
    c.require(not (STATE/'submission.json').exists(),'retry already submitted')
    for name in ('closure_creation_error.json','reconciled_creation_error.json'):
        c.require(c.read_json(STATE/name)['error']['code']=='billing_hard_limit_reached',
                  'prior creation failure is not reconciled billing rejection')
    paths=[x for x in c.HERE.rglob('*') if x.is_file() and '__pycache__' not in x.parts
           and not x.name.startswith(PREFIX)]
    c.save(c.HERE/f'{PREFIX}_PRESERVATION_BASELINE.json',
           {'files_sha256':{str(x.relative_to(c.HERE)):c.sha(x) for x in sorted(paths)}})
    tests=p.tests('RESCUE_PREFLIGHT')
    preserve()
    c.save(c.HERE/f'{PREFIX}_PREFLIGHT.json',{'status':'PASS','protocol_sha256':p.pilot.EXPECTED,
        'pending':4,'task':'PG','prior_terminal_outcomes':11996,'prior_success_overlap':0,
        'prepared_requests_sha256':c.sha(p.PRIVATE/'round_2/requests.jsonl'),
        'existing_closure_reused':True,'test_suites':tests})
    print('Rescue preflight PASS: four PG requests, identical frozen bytes, prior outcomes unchanged.')


def submit():
    gate=c.read_json(c.HERE/f'{PREFIX}_PREFLIGHT.json')
    c.require(gate['status']=='PASS','rescue preflight gate')
    preserve();r.reconcile_local()
    c.require(not (STATE/'submission.json').exists(),'retry already submitted')
    c.require(not (STATE/'rescue_upload_intent.json').exists(),'rescue POST already attempted; reconcile first')
    path=p.PRIVATE/'round_2/batch_001.jsonl'
    data=path.read_bytes()
    c.require(c.digest(data)==gate['prepared_requests_sha256'],'request bytes drift')
    model=c.strict_json(api('GET','/models/gpt-5.6-sol'))
    c.require(model['id']=='gpt-5.6-sol','teacher unavailable; no substitution')
    c.save(STATE/'rescue_model_metadata.json',{'id':model['id']})
    matches=[];after='';listed=0
    while True:
        page=c.strict_json(api('GET','/batches?limit=100'+after))
        listed+=len(page['data'])
        for batch in page['data']:
            metadata=batch.get('metadata') or {}
            if metadata.get('protocol')==p.pilot.EXPECTED and metadata.get('attempt')=='2':
                matches.append(batch['id'])
        if not page.get('has_more'):break
        c.require(bool(page['data']),'empty pagination')
        after='&after='+page['data'][-1]['id']
    c.save(STATE/'rescue_remote_reconciliation.json',{'listed_count':listed,
        'matching_retry_batch_ids':matches,'checked_utc':p.pilot.batch.now()})
    c.require(not matches,'existing retry Batch in current project: reconcile before spending')
    c.save(STATE/'rescue_upload_intent.json',{'created_utc':p.pilot.batch.now(),
        'requests':4,'request_sha256':c.digest(data),'billing_provenance':FACT})
    boundary='e11c-'+uuid.uuid4().hex
    multipart=(f'--{boundary}\r\nContent-Disposition: form-data; name="purpose"\r\n\r\nbatch\r\n'
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        'Content-Type: application/jsonl\r\n\r\n').encode()+data+f'\r\n--{boundary}--\r\n'.encode()
    try:
        uploaded=c.strict_json(api('POST','/files',multipart,'multipart/form-data; boundary='+boundary))
        c.save(STATE/'rescue_uploaded_file.json',{k:uploaded.get(k) for k in ('id','purpose','bytes','status')})
        remote=api('GET','/files/'+uploaded['id']+'/content')
        c.require(remote==data,'uploaded bytes mismatch')
        intent={'created_utc':p.pilot.batch.now(),'attempt':2,'shard':1,
            'request_sha256':c.digest(data),'protocol_sha256':p.pilot.EXPECTED,'billing_provenance':FACT}
        c.save(STATE/'rescue_creation_intent.json',{'input_file_id':uploaded['id'],**intent})
        body={'input_file_id':uploaded['id'],'endpoint':'/v1/responses','completion_window':'24h',
            'metadata':{'experiment':'E11-C','protocol':p.pilot.EXPECTED,'attempt':'2','shard':'1'}}
        batch=c.strict_json(api('POST','/batches',c.encoded(body)))
        c.save(STATE/'submission.json',{'batch_id':batch['id'],'input_file_id':uploaded['id'],
            **intent,'api_batch':{k:batch.get(k) for k in BATCH_FIELDS}})
        print('Submitted four PG requests:',batch['id'])
    except RuntimeError as exc:
        c.save(STATE/'rescue_submission_failure.json',{'error':str(exc),
            'created_utc':p.pilot.batch.now(),'do_not_repeat_without_reconciliation':True})
        raise


def download():
    with p.scope():_,path=p.pilot.batch.checked_shard(2,1)
    c.require(not (STATE/'download_receipt.json').exists(),'already downloaded')
    submission=c.read_json(STATE/'submission.json')
    batch=c.strict_json(api('GET','/batches/'+submission['batch_id']))
    c.require(batch['id']==submission['batch_id'] and batch['input_file_id']==submission['input_file_id']
              and batch['endpoint']=='/v1/responses','remote batch identity')
    if batch['status'] not in p.pilot.batch.TERMINAL:
        print('Retry Batch status:',batch['status']);return
    c.require(batch['status']!='failed','Batch validation failed; stop')
    files=[]
    for field in ('output_file_id','error_file_id'):
        if batch.get(field):
            name=field.replace('_id','.jsonl')
            c.write_once(STATE/name,api('GET','/files/'+batch[field]+'/content'))
            files.append({'path':name,'file_id':batch[field],'sha256':c.sha(STATE/name)})
    c.save(STATE/'download_receipt.json',{'batch':{k:batch.get(k) for k in BATCH_FIELDS},
        'files':files,'request_sha256':c.sha(path),'protocol_sha256':p.pilot.EXPECTED,
        'terminal_observed_utc':p.pilot.batch.now(),'billing_provenance':FACT})
    print('Downloaded terminal retry Batch:',batch['id'])


def finalize():
    preserve()
    r.finalize()
    # Extend only the newly created closed audit, keeping all earlier artifacts intact.
    audit_path=c.HERE/'E11C_PRODUCTION_CLOSED_AUDIT.json'
    audit=c.read_json(audit_path)
    audit['billing_provenance']=FACT
    audit['rescue_preflight']=str((c.HERE/f'{PREFIX}_PREFLIGHT.json').relative_to(c.HERE))
    audit_path.write_text(c.json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    md=c.HERE/'E11C_PRODUCTION_CLOSED_AUDIT.md'
    md.write_text('# E11-C closed production audit\n\nAll 12,000 candidates have terminal labels.\n\n'+FACT+
                  '.\n\n```json\n'+c.json.dumps(audit,indent=2)+'\n```\n',encoding='utf-8')
    manifest_path=c.HERE/'E11C_PRODUCTION_CLOSED_MANIFEST.json'
    manifest=c.read_json(manifest_path)
    paths=[audit_path,md,c.HERE/'rescue_e11c_retry.py',c.HERE/f'{PREFIX}_PREFLIGHT.json',
           c.HERE/f'{PREFIX}_PRESERVATION_BASELINE.json']
    manifest['files_sha256'].update({str(x.relative_to(c.HERE)):c.sha(x) for x in paths})
    manifest['billing_provenance']=FACT
    manifest_path.write_text(c.json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    preserve()
    p.check_hashes(c.HERE,manifest['files_sha256'])
    print('Closed audit and manifest verified; alternate billing provenance recorded without account identifiers.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('preflight','submit','download','finalize'))
    args=parser.parse_args()
    try:globals()[args.action]()
    except RuntimeError as exc:
        print(str(exc));raise SystemExit(2)
