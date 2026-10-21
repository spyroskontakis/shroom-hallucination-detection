"""Prepared submit/download commands. Network requires --execute-api explicitly.

Not executed during protocol preparation. Credentials are read only after the guard.
Ambiguous POST failures are never retried automatically.
"""
import argparse
import datetime as dt
import os
import urllib.error
import urllib.request
import uuid
from e11c_common import *

TERMINAL = {'completed','expired','cancelled','failed'}


def api_client(execute):
    require(execute, 'API execution disabled; --execute-api and later user authorization required')
    key = os.environ.get('OPENAI_API_KEY')
    require(bool(key), 'OPENAI_API_KEY is missing')
    def call(method, endpoint, data=None, content_type='application/json'):
        require(endpoint.startswith(('/models/','/files','/batches')), 'API endpoint allowlist')
        req = urllib.request.Request('https://api.openai.com/v1'+endpoint,
                                     data=data, method=method,
                                     headers={'Authorization':'Bearer '+key,
                                              'Content-Type':content_type})
        try:
            with urllib.request.urlopen(req,timeout=120) as reply:
                return reply.read()
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f'API HTTP {exc.code}; details omitted to avoid credential/text logs') from None
        except (urllib.error.URLError, TimeoutError):
            raise RuntimeError('API transport failure; do not repeat an ambiguous POST') from None
    return call


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def checked_shard(attempt,index):
    spec=load_protocol()
    candidates=load_candidates()
    manifest=read_json(PRIVATE/f'round_{attempt}/request_manifest.json')
    require(manifest['attempt']==attempt and manifest['protocol_sha256']==spec['protocol_sha256'],
            'request manifest identity')
    path=PRIVATE/f'round_{attempt}/requests.jsonl'
    require(sha(path)==manifest['requests_sha256'],'request SHA')
    rows=read_rows(path)
    wanted=candidates
    if attempt>1:
        from parse_e11c_results import parse_round
        previous,ledger=parse_round(attempt-1,write=False)
        retry_keys={r['sample_key'] for r in ledger if r['retryable']}
        wanted=[r for r in candidates if r['sample_key'] in retry_keys]
    require(rows==[request(r,spec,attempt) for r in wanted],'request body/coverage drift')
    require(1<=index<=len(manifest['shards']),'shard index')
    shard=manifest['shards'][index-1]
    require(shard['path']==f'batch_{index:03d}.jsonl','shard path')
    shard_path=path.parent/shard['path']
    require(sha(shard_path)==shard['sha256'] and
            read_rows(shard_path)==rows[(index-1)*500:index*500] and
            shard['custom_ids']==[r['custom_id'] for r in read_rows(shard_path)],'shard integrity')
    return spec,shard_path


def submit(attempt,index,execute=False):
    require(execute,'API execution disabled')
    spec,path=checked_shard(attempt,index)
    state=path.parent/f'batch_{index:03d}'
    require(not (state/'submission_intent.json').exists(),
            'submission already attempted; reconcile receipt/remote state, never blindly resubmit')
    if attempt>1:
        previous=read_json(PRIVATE/f'round_{attempt-1}/parse_report.json')
        elapsed=(dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(previous['terminal_observed_utc'])).total_seconds()
        require(elapsed>=spec['retry']['minimum_round_delays_seconds'][str(attempt)],'retry delay')
    call=api_client(execute)
    metadata=strict_json(call('GET','/models/'+spec['teacher']['model']))
    require(metadata['id']==spec['teacher']['model'],'model metadata mismatch; no alias replacement')
    save(state/'model_metadata.json',metadata)
    intent={'attempt':attempt,'shard':index,'request_sha256':sha(path),
            'protocol_sha256':spec['protocol_sha256'],'created_utc':now()}
    save(state/'submission_intent.json',intent)
    boundary='e11c-'+uuid.uuid4().hex
    content=(f'--{boundary}\r\nContent-Disposition: form-data; name="purpose"\r\n\r\nbatch\r\n'
             f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
             'Content-Type: application/jsonl\r\n\r\n').encode()+path.read_bytes()+f'\r\n--{boundary}--\r\n'.encode()
    try:
        uploaded=strict_json(call('POST','/files',content,'multipart/form-data; boundary='+boundary))
        save(state/'uploaded_file.json',uploaded)
        batch=strict_json(call('POST','/batches',encoded({
            'input_file_id':uploaded['id'],'endpoint':'/v1/responses','completion_window':'24h',
            'metadata':{'experiment':'E11-C','protocol':spec['protocol_sha256'],
                        'attempt':str(attempt),'shard':str(index)}})))
        save(state/'submission.json',{'batch_id':batch['id'],'input_file_id':uploaded['id'],
                                    **intent,'api_batch':batch})
        print('Submitted',batch['id'],'rows',len(read_rows(path)))
    except Exception as exc:
        save(state/'submission_failure.json',{'error_type':type(exc).__name__,
             'created_utc':now(),'ambiguous_post_do_not_repeat':True})
        raise


def download(attempt,index,execute=False):
    require(execute,'API execution disabled')
    spec,path=checked_shard(attempt,index)
    state=path.parent/f'batch_{index:03d}'
    receipt=read_json(state/'submission.json')
    require(receipt['request_sha256']==sha(path),'submission provenance')
    require(not (state/'download_receipt.json').exists(),'already downloaded; parse existing raw files')
    call=api_client(execute)
    batch=strict_json(call('GET','/batches/'+receipt['batch_id']))
    require(batch['id']==receipt['batch_id'] and batch['input_file_id']==receipt['input_file_id']
            and batch['endpoint']=='/v1/responses','batch identity mismatch')
    if batch['status'] not in TERMINAL:
        print('Batch status',batch['status'],'no result parsing or retry allowed yet')
        return
    require(batch['status']!='failed','batch validation/configuration failure: STOP, do not spend retries')
    files=[]
    for field in ('output_file_id','error_file_id'):
        if batch.get(field):
            name=field.replace('_id','.jsonl')
            data=call('GET','/files/'+batch[field]+'/content')
            write_once(state/name,data)
            files.append({'path':name,'file_id':batch[field],'sha256':sha(state/name)})
    save(state/'download_receipt.json',{'batch':batch,'files':files,
             'request_sha256':sha(path),'protocol_sha256':spec['protocol_sha256'],
             'terminal_observed_utc':now()})
    print('Downloaded terminal batch',batch['id'],'files',len(files))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('submit','download'))
    p.add_argument('--attempt',type=int,choices=(1,2,3),default=1)
    p.add_argument('--shard',type=int,required=True)
    p.add_argument('--execute-api',action='store_true')
    a=p.parse_args()
    (submit if a.action=='submit' else download)(a.attempt,a.shard,a.execute_api)
