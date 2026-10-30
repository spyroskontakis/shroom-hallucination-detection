"""Authorized production complement; frozen helpers and artifacts remain untouched."""
import argparse
from collections import Counter
from contextlib import contextmanager
import subprocess
import sys
import e11c_common as c
import e11c_pilot as pilot

PRIVATE = c.PRIVATE / 'production_11700'
BASELINE = c.HERE / 'E11C_PRODUCTION_PRESERVATION_BASELINE.json'


def check_hashes(base, hashes):
    for name, expected in hashes.items():
        actual = c.sha(base / name)
        c.require(actual == expected,
                  f'integrity failure: {name}: expected {expected}, actual {actual}')


def preservation():
    pilot.protocol()
    check_hashes(c.HERE, c.read_json(c.HERE/'E11C_PREPARATION_MANIFEST.json')['files_sha256'])
    check_hashes(c.HERE.parent, c.read_json(c.HERE/'E11C_PRIOR_ARTIFACT_HASHES.json'))
    m = c.read_json(c.HERE/'E11C_PILOT_MANIFEST.json')
    check_hashes(c.HERE, {
        'E11C_PILOT_MANIFEST.json': (c.HERE/'E11C_PILOT_MANIFEST.sha256').read_text().strip(),
        'E11C_PILOT_SELECTION_MANIFEST.json': m['selection_manifest_sha256'],
        'private/pilot_300/candidates.jsonl': m['candidate_list_sha256'],
        'private/pilot_300/parsed_labels.jsonl': m['parsed_labels_sha256'],
        'E11C_PILOT_AUDIT.json': m['audit_sha256'],
        **m['request_files'], **m['raw_response_files']})
    if BASELINE.exists():
        check_hashes(c.HERE, c.read_json(BASELINE)['files_sha256'])


def snapshot():
    preservation()
    paths = [p for p in c.HERE.rglob('*') if p.is_file()
             and '__pycache__' not in p.parts
             and (p.is_relative_to(pilot.PILOT) or
                  (p.parent == c.HERE and 'PRODUCTION' not in p.name
                   and 'production' not in p.name))]
    c.save(BASELINE, {'files_sha256': {str(p.relative_to(c.HERE)): c.sha(p)
                                     for p in sorted(paths)}})


def partition():
    spec = pilot.protocol()
    pool = c.load_candidates()
    used = pilot.candidates()
    ids = {r['sample_key'] for r in used}
    remaining = [r for r in pool if r['sample_key'] not in ids]
    for rows, n in ((pool, 4000), (used, 100), (remaining, 3900)):
        c.require(len(rows) == len({r['sample_key'] for r in rows}) == n*3, 'unique population')
        c.require(Counter(r['task'] for r in rows) == {t:n for t in c.POLICY}, 'task quotas')
    rem = {r['sample_key'] for r in remaining}
    c.require(not ids & rem and ids | rem == {r['sample_key'] for r in pool}, 'partition coverage')
    with pilot.scope():
        report, ledger = pilot.results.parse_round(1, write=False)
    c.require(report['rows'] == 300 and report['retryable'] == 0
              and report['accepted'] == 298
              and report['outcomes'] == dict(zip(c.LABELS, (123,175,2))), 'pilot outcomes')
    c.require(all(len(r['history']) == 1 for r in ledger), 'pilot attempt count')
    return pool, remaining, ledger


def candidates():
    _, rows, _ = partition()
    c.require(c.read_rows(PRIVATE/'candidates.jsonl') == rows, 'production complement drift')
    return rows


@contextmanager
def scope():
    saved = []
    try:
        for module in (pilot.batch, pilot.requests, pilot.results):
            for name, value in [('PRIVATE', PRIVATE), ('load_candidates', candidates),
                                ('load_protocol', pilot.protocol)]:
                saved.append((module,name,getattr(module,name)))
                setattr(module,name,value)
        yield
    finally:
        for module,name,value in reversed(saved):
            setattr(module,name,value)


def ignored():
    paths = [str(p) for p in c.PRIVATE.rglob('*') if p.is_file()]
    paths.append(str(PRIVATE/'future_binary_supervision.jsonl'))
    result = subprocess.run(['git','check-ignore','--stdin'], input='\n'.join(paths)+'\n',
                            text=True,capture_output=True,cwd=c.root(),check=False)
    c.require(result.returncode == 0 and len(result.stdout.splitlines()) == len(paths),
              'private artifacts not all git ignored')


def prepare():
    snapshot()
    _, rows, _ = partition()
    c.write_once(PRIVATE/'candidates.jsonl',c.rows_bytes(rows))
    with scope():
        manifest = pilot.requests.build(1)
    # Compare every request to historical preparation, and pilot requests too.
    full = {r['custom_id']:r for r in c.read_rows(c.PRIVATE/'round_1/requests.jsonl')}
    generated = c.read_rows(PRIVATE/'round_1/requests.jsonl')
    old = c.read_rows(pilot.PILOT/'round_1/requests.jsonl')
    c.require(len(full) == 12000 and len(generated) == 11700, 'request count')
    c.require(generated == [full[r['custom_id']] for r in generated], 'production request replay')
    c.require(old == [full[r['custom_id']] for r in old], 'pilot request replay')
    c.require(not {r['custom_id'] for r in old} & {r['custom_id'] for r in generated},
              'pilot resubmission')
    ignored(); preservation()
    print('Production preparation PASS: 11700 requests, 3900/task, 24 shards; no API calls')


def tests(stage):
    commands = [
        [sys.executable,'-m','unittest','discover','-s',str(c.HERE),'-p','test_e11c*.py','-v'],
        [sys.executable,'-m','unittest','discover','-s',str(c.HERE.parent),'-p','test_*.py','-v']]
    reports=[]
    for i, command in enumerate(commands):
        result=subprocess.run(command,cwd=c.root(),text=True,capture_output=True)
        log=c.HERE/f'E11C_PRODUCTION_{stage}_TEST_{i+1}.txt'
        c.write_once(log,(result.stdout+result.stderr).encode())
        reports.append({'command':command,'exit_code':result.returncode,'log':log.name,'sha256':c.sha(log)})
        c.require(result.returncode==0, f'test suite failed: {log}')
    c.save(c.HERE/f'E11C_PRODUCTION_{stage}_TEST_REPORT.json',{'status':'PASS','suites':reports})
    return reports


def preflight():
    prepare()
    reports=tests('PREFLIGHT')
    preservation(); ignored()
    audit=c.read_json(c.HERE/'E11C_PILOT_AUDIT.json')
    cost=audit['pilot_batch_cost_estimate_usd']
    c.save(c.HERE/'E11C_PRODUCTION_PREFLIGHT.json',{
        'status':'PASS','protocol_sha256':pilot.EXPECTED,
        'pilot_count':300,'production_count':11700,'total_count':12000,
        'per_task':{'pilot':100,'production':3900,'total':4000},
        'duplicates':0,'missing':0,'intersection':0,'outside_pool':0,
        'requests_sha256':c.sha(PRIVATE/'round_1/requests.jsonl'),
        'request_manifest_sha256':c.sha(PRIVATE/'round_1/request_manifest.json'),
        'preservation_baseline_sha256':c.sha(BASELINE),
        'frozen_request_replay':'PASS','frozen_and_pilot_preservation':'PASS',
        'private_files_git_ignored':True,'test_suites':reports,
        'production_cost_estimate_usd':cost*39,'combined_cost_estimate_usd':cost*40})
    print('Full preflight PASS')


def action(name, attempt, execute):
    gate=c.read_json(c.HERE/'E11C_PRODUCTION_PREFLIGHT.json')
    c.require(gate['status']=='PASS' and gate['protocol_sha256']==pilot.EXPECTED,'preflight gate')
    preservation(); ignored()
    c.require(c.sha(PRIVATE/'round_1/requests.jsonl')==gate['requests_sha256'], 'preflight requests drift')
    with scope():
        if name=='prepare-retry':
            c.require(attempt in (2,3),'retry attempt')
            report,_=pilot.results.parse_round(attempt-1,write=False)
            c.require(report['retryable']>0,'no retryable failures')
            pilot.requests.build(attempt)
        elif name=='parse':
            print(c.json.dumps(pilot.results.parse_round(attempt)[0],indent=2))
        else:
            manifest=c.read_json(PRIVATE/f'round_{attempt}/request_manifest.json')
            for i in range(1,len(manifest['shards'])+1):
                state=PRIVATE/f'round_{attempt}/batch_{i:03d}'
                if name=='submit':
                    if (state/'submission.json').exists():
                        receipt=c.read_json(state/'submission.json')
                        _,path=pilot.batch.checked_shard(attempt,i)
                        c.require(receipt['request_sha256']==c.sha(path),'existing submission drift')
                        print('Already submitted',receipt['batch_id']); continue
                    pilot.batch.submit(attempt,i,execute)
                elif name=='download' and not (state/'download_receipt.json').exists():
                    pilot.batch.download(attempt,i,execute)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','preflight','submit','download','parse','prepare-retry'])
    parser.add_argument('--attempt',type=int,choices=(1,2,3),default=1)
    parser.add_argument('--execute-api',action='store_true')
    args=parser.parse_args()
    if args.action=='prepare': prepare()
    elif args.action=='preflight': preflight()
    else: action(args.action,args.attempt,args.execute_api)
