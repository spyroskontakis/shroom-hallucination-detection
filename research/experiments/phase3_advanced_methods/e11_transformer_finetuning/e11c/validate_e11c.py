"""Offline end-to-end preparation validation. Network operations are never invoked."""
import ast
import sys
from collections import Counter
from e11c_common import *


def main():
    spec=load_protocol()
    master=load_master()
    candidates=load_candidates()
    require(candidates==selected(master),'candidate selection is not deterministic label-blind ranking')
    manifest=read_json(HERE/'E11C_CANDIDATE_MANIFEST.json')
    require(manifest['protocol_sha256']==spec['protocol_sha256'] and
            manifest['candidate_sha256']==sha(PRIVATE/'candidates.jsonl') and
            manifest['selected_sample_keys']==[r['sample_key'] for r in candidates] and
            manifest['selected_keys_sha256']==digest(encoded(manifest['selected_sample_keys'])),
            'candidate manifest mismatch')
    require(Counter(r['task'] for r in candidates)=={'DM':4000,'MT':4000,'PG':4000},'task quotas')
    requests=read_rows(PRIVATE/'round_1/requests.jsonl')
    require(requests==[request(row,spec) for row in candidates], 'request exact replay')
    require(len({r['custom_id'] for r in requests})==12000,'request custom IDs')
    for req,row in zip(requests,candidates):
        payload=strict_json(req['body']['input'][0]['content'])
        require(set(payload)=={'task','reference','hypothesis'} and
                payload==user_payload(row),'teacher input leakage')
        require(set(req['body'])=={'model','instructions','input','reasoning','max_output_tokens','text','store'},
                'request body allowlist')
    request_manifest=read_json(PRIVATE/'round_1/request_manifest.json')
    require(request_manifest['requests_sha256']==sha(PRIVATE/'round_1/requests.jsonl') and
            len(request_manifest['shards'])==24,'request manifest')
    shard_rows=[]
    for entry in request_manifest['shards']:
        path=PRIVATE/'round_1'/entry['path']
        require(sha(path)==entry['sha256'],'shard hash mismatch')
        group=read_rows(path)
        require(len(group)==entry['rows']==500,'shard row count')
        shard_rows.extend(group)
    require(shard_rows==requests,'shard completeness')
    from build_e11c_folds import audit_purge
    purge,_=audit_purge()
    require(purge==read_json(HERE/'E11C_TEXT_PURGE_AUDIT.json'),'text-only purge audit drift')
    # Check actual implementation literals, not words such as "official-test prohibition" in documentation.
    dangerous=[]
    for path in HERE.glob('*.py'):
        if path.name == 'validate_e11c.py' or path.name.startswith('test_'):
            continue  # Exclude the detector's own forbidden strings and negative test fixtures.
        tree=ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node,ast.Constant) and isinstance(node.value,str):
                value=node.value.lower().replace('\\','/')
                if any(x in value for x in ('test.model-agnostic','test.model-aware','/test/',
                                            'shroom_test','train.model-aware')):
                    dangerous.append(path.name)
    require(not dangerous,'forbidden input path reference')
    require(not list(PRIVATE.glob('round_*/batch_*/submission_intent.json')) and
            not list(PRIVATE.glob('round_*/ledger.jsonl')) and
            not (PRIVATE/'training_sets').exists(),'execution artifacts present during preparation')
    prior=read_json(HERE/'E11C_PRIOR_ARTIFACT_HASHES.json')
    for name,expected in prior.items():
        require(sha(HERE.parent/name)==expected,'prior E11 artifact changed: '+name)
    report={'status':'PASS','candidate_rows':12000,'unique_keys':12000,
            'task_counts':dict(Counter(r['task'] for r in candidates)),
            'master_membership':'PASS','reference_policy':'PASS',
            'teacher_payload_allowlist':'PASS','prompt_schema_model':'PASS',
            'batch_shards':24,'batch_requests':12000,
            'forbidden_dataset_path_scan':'PASS','prior_artifacts_unchanged':len(prior),
            'protocol_sha256':spec['protocol_sha256'],
            'candidate_manifest_sha256':sha(HERE/'E11C_CANDIDATE_MANIFEST.json'),
            'candidate_jsonl_sha256':sha(PRIVATE/'candidates.jsonl'),
            'batch_jsonl_sha256':sha(PRIVATE/'round_1/requests.jsonl'),
            'live_api_model_metadata':'NOT_QUERIED_PER_NO_API_INSTRUCTION',
            'no_label_generation':True,'no_student_training':True,'python':sys.version.split()[0]}
    save(HERE/'E11C_LOCAL_VALIDATION.json',report)
    print(json.dumps(report,indent=2))
    return report


if __name__=='__main__':
    main()
