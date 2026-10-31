"""Local-only Azure alternate annotations. Never updates the original teacher pool.

Use --dry-run to validate without importing/constructing an API client.
Use --execute-api explicitly for the four synchronous requests. Requires openai.
"""
import argparse
import copy
import os
import re
import subprocess
import time
from pathlib import Path
import e11c_common as c
import close_e11c_retry as closure
import parse_e11c_results as parser

BASE_URL=__import__('os').environ['AZURE_OPENAI_BASE_URL']
MODEL='gpt-5-mini'
IDS=(
 '1f2a34940a94ab535d5fba86b8e0eee6b4426a1e81f33455ed3e38b338b74adc',
 'f4fdbac32e85fe991167d007dee366f195f1ecab7808e9ebe3ac4eb7b3416e39',
 '24d9c782312eaaa9fca602f5688d43605af8470a8b6c83da8e81dd4c003f2382',
 'baa5feb7b943ad163b7d3ad434ef3aaf27505092f4cc772fda2f59c956fdb833')
OUT=c.PRIVATE/'azure_alternate_rescue'
PREFIX='E11C_ALTERNATE_MODEL_RESCUE'


def environment():
    for name in ('AZURE_OPENAI_API_KEY','AZURE_OPENAI_BASE_URL','AZURE_OPENAI_DEPLOYMENT'):
        c.require(bool(os.environ.get(name)),name+' must exist in the local PowerShell process')
    c.require(os.environ['AZURE_OPENAI_BASE_URL']==BASE_URL,'Azure base URL mismatch')
    c.require(os.environ['AZURE_OPENAI_DEPLOYMENT']==MODEL,'Azure deployment mismatch')


def rescue_body(original):
    body=copy.deepcopy(original['body'])
    body['model']=MODEL
    return body


def protected_files():
    return {str(p.relative_to(c.HERE)):c.sha(p) for p in c.HERE.rglob('*')
            if p.is_file() and '__pycache__' not in p.parts and not p.is_relative_to(OUT)
            and not p.name.startswith(PREFIX)}


def verify_preservation(baseline):
    for name,digest in baseline.items():
        c.require(c.sha(c.HERE/name)==digest,'protected artifact changed: '+name)


def preflight():
    environment()
    closure.preserve()
    pending,requests=closure.reconcile_local()
    c.require(len(pending)==4 and {r['sample_key'] for r in pending}==set(IDS),'exact pending IDs')
    candidates={r['sample_key']:r for r in c.load_candidates() if r['sample_key'] in IDS}
    c.require(len(candidates)==4 and all(r['task']=='PG' for r in candidates.values()),'four PG rows')
    spec=closure.p.pilot.protocol()
    expected=[c.request(candidates[key],spec,2) for key in IDS]
    c.require(requests==expected,'frozen request bytes/order replay')
    # Also verify the historical combined ledger and authoritative binary pool.
    ledger=c.read_rows(closure.p.PRIVATE/'full_audit_ledger.jsonl')
    c.require(sum(r['accepted'] for r in ledger)==11887 and
              sum(r['outcome']=='uncertain' for r in ledger)==109,'original label counts')
    c.require(c.read_rows(closure.p.PRIVATE/'future_binary_supervision.jsonl')==
              [r['synthetic'] for r in ledger if r['accepted']],'original supervision pool')
    check=subprocess.run(['git','check-ignore','--stdin'],input=str(OUT/'responses.jsonl')+'\n',
                         capture_output=True,text=True,cwd=c.root())
    c.require(check.returncode==0,'private rescue output must be git ignored')
    baseline=protected_files()
    if (OUT/'preservation_baseline.json').exists():
        verify_preservation(c.read_json(OUT/'preservation_baseline.json'))
    return requests,baseline


def classify(body):
    model=body.get('model','')
    c.require(bool(re.fullmatch(r'gpt-5-mini(?:-\d{4}-\d{2}-\d{2})?',model)),
              'unexpected Azure returned model; stop without substitution')
    return parser.classify({'response':{'status_code':200,'body':body}},model)


def run_candidate(client,key,original,spec):
    c.require(key in IDS,'candidate outside rescue allowlist')
    folder=OUT/key
    body=rescue_body(original)
    c.require(original['custom_id']==c.request(
        next(r for r in c.load_candidates() if r['sample_key']==key),spec,2)['custom_id'],
        'candidate request mapping')
    c.save(folder/'request.json',body)
    maximum=spec['retry']['maximum_attempts_per_sample']
    for attempt in range(1,maximum+1):
        path=folder/f'attempt_{attempt}.json'
        intent=folder/f'intent_{attempt}.json'
        if not path.exists():
            c.require(not intent.exists(),'unresolved request intent; reconcile manually before resuming')
            if attempt>1:
                prior=c.read_json(folder/f'attempt_{attempt-1}.json')
                delay=spec['retry']['minimum_round_delays_seconds'][str(attempt)]
                time.sleep(max(0,prior['recorded_at']+delay-time.time()))
            identity=f'e11c-azure-alternate-{key}-a{attempt}'
            c.save(intent,{'identity':identity,'sample_key':key,'attempt':attempt,
                           'request_sha256':c.digest(c.encoded(body))})
            # Automatic SDK retries are disabled. Only classified failures below retry.
            import openai
            try:
                response=client.responses.create(**body)
                result={'body':response.model_dump(mode='json')}
            except openai.APIStatusError as exc:
                status=exc.status_code
                result={'outcome':'http_'+str(status),
                        'retryable':status in (408,429) or 500<=status<600}
            except openai.APIConnectionError:
                result={'outcome':'transport','retryable':True}
            result.update(recorded_at=time.time(),identity=identity,attempt=attempt)
            c.save(path,result)  # Persist before parsing; no exception/header/key logs.
        result=c.read_json(path)
        if 'body' in result:
            outcome,retry,answer=classify(result['body'])
        else:
            outcome,retry,answer=result['outcome'],result['retryable'],None
        if answer:
            return {'sample_key':key,'task':'PG','label':answer['label'],'reason':answer['reason'],
                    'attempt':attempt,'returned_model':result['body']['model'],
                    'response_id':result['body']['id'],'raw_response_path':str(path.relative_to(c.HERE)),
                    'raw_response_sha256':c.sha(path),'excluded_from_original_supervision':True}
        if not retry or attempt==maximum:
            return {'sample_key':key,'task':'PG','label':None,'outcome':outcome,'attempt':attempt,
                    'excluded_from_original_supervision':True}
    raise AssertionError('unreachable')


def audit(results,baseline):
    verify_preservation(baseline)
    records=[c.read_json(p) for p in OUT.glob('*/attempt_*.json')]
    usage=[r['body']['usage'] for r in records if r.get('body',{}).get('usage')]
    outcomes=[]
    for r in records:
        outcomes.append(classify(r['body'])[0] if 'body' in r else r['outcome'])
    tokens={'input_tokens':sum(u['input_tokens'] for u in usage),
            'output_tokens':sum(u['output_tokens'] for u in usage),
            'reasoning_tokens':sum((u.get('output_tokens_details') or {}).get('reasoning_tokens',0) for u in usage),
            'cached_input_tokens':sum((u.get('input_tokens_details') or {}).get('cached_tokens',0) for u in usage),
            'usage_records':len(usage)}
    complete=sum(r['label'] in c.LABELS for r in results)
    report={'status':'PASS' if complete==4 else 'FAIL','provider':'Azure / Microsoft Foundry',
        'deployment':MODEL,'rescue_teacher':MODEL,'original_teacher':'gpt-5.6-sol',
        'deployment_type':'not exposed by Responses API','protocol_sha256':closure.p.pilot.EXPECTED,
        'requested_candidates':4,'task':'PG','completed':complete,'results':results,
        'returned_models':sorted({r['returned_model'] for r in results if r.get('returned_model')}),
        'configuration_differences':['Azure provider and gpt-5-mini model instead of gpt-5.6-sol',
            'Synchronous Responses API instead of Batch; no Batch pricing assumption',
            'Separate rescue attempt budget of at most three calls per candidate; SDK retries disabled'],
        'unchanged_request_settings':['prompt','input and PG source reference','schema','label vocabulary',
            'medium reasoning','2048 output token limit','store=false','omitted sampling parameters'],
        'excluded_from_homogeneous_supervision':True,'original_definitive_labels':11887,
        'original_uncertain_labels':109,'original_terminal_outcomes':11996,'original_pending':4,
        'original_artifacts_unchanged':True,'previous_successful_outcomes_overwritten':False,
        'api_failures':sum(x.startswith('http_') or x=='transport' for x in outcomes),
        'schema_failures':outcomes.count('invalid_schema'),'retries':len(records)-len(results),
        'usage':tokens,'azure_cost':None,'cost_note':'Responses does not expose billed cost; Azure deployment rate not assumed.',
        'student_training':False,'fold_construction':False,'dev_evaluation':False,'official_test_access':False,
        'prompt_tuning':False,'manual_correction':False,'commit':False,'push':False}
    c.write_once(OUT/'rescue_judgments.jsonl',c.rows_bytes(results))
    c.save(c.HERE/f'{PREFIX}_AUDIT.json',report)
    c.write_once(c.HERE/f'{PREFIX}_AUDIT.md',('# E11-C alternate-model rescue\n\n'
        'These Azure gpt-5-mini judgments are excluded from the homogeneous gpt-5.6-sol pool.\n\n'
        '```json\n'+c.json.dumps(report,indent=2)+'\n```\n').encode())
    paths=[p for p in OUT.rglob('*') if p.is_file()]+[
        c.HERE/f'{PREFIX}_AUDIT.json',c.HERE/f'{PREFIX}_AUDIT.md',Path(__file__).resolve(),
        c.HERE/'test_e11c_azure_alternate.py']
    c.save(c.HERE/f'{PREFIX}_MANIFEST.json',{'files_sha256':{
        str(p.relative_to(c.HERE)):c.sha(p) for p in paths},'excluded_from_homogeneous_supervision':True})
    print(f"{report['status']}: {complete}/4 alternate judgments; original supervision pool unchanged.")


def main(argv=None):
    args=argparse.ArgumentParser(description=__doc__)
    mode=args.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run',action='store_true')
    mode.add_argument('--execute-api',action='store_true')
    options=args.parse_args(argv)
    requests,baseline=preflight()
    if options.dry_run:
        verify_preservation(baseline)
        print('DRY RUN PASS: four PG requests reconciled; no client created, no API calls, no output files written.')
        return
    from openai import OpenAI
    c.save(OUT/'preservation_baseline.json',baseline)
    spec=closure.p.pilot.protocol()
    with OpenAI(api_key=os.environ['AZURE_OPENAI_API_KEY'],base_url=os.environ['AZURE_OPENAI_BASE_URL'],
                max_retries=0,timeout=120) as client:
        results=[run_candidate(client,key,request,spec) for key,request in zip(IDS,requests)]
    audit(results,baseline)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        # Never expose SDK exception text, request headers, credentials or payloads.
        print('STOP: local precheck or execution failed ('+type(exc).__name__+
              '). No automatic restart. Check environment configuration and saved private attempt state.')
        raise SystemExit(1) from None
