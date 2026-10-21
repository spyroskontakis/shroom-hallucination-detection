"""Consolidate validated pilot and production ledgers without fold selection."""
import argparse
import statistics
from collections import Counter
import e11c_common as c
import e11c_production as p


def audit(attempt, blocked=False):
    p.preservation()
    pool,_,pilot_ledger=p.partition()
    with p.scope():
        report,production=p.pilot.results.parse_round(attempt,write=False)
    c.require(blocked or report['retryable']==0,'operational retries pending')
    if blocked:
        error=c.read_json(p.PRIVATE/'round_2/batch_001/reconciled_creation_error.json')
        c.require(error['error']['code']=='billing_hard_limit_reached','unverified billing block')
    combined=pilot_ledger+production
    by_key={r['sample_key']:r for r in combined}
    c.require(len(combined)==len(by_key)==12000 and set(by_key)=={r['sample_key'] for r in pool},
              'consolidated coverage')
    ledger=[by_key[r['sample_key']] for r in pool]
    binary=[r['synthetic'] for r in ledger if r['accepted']]
    c.require(all(r['llm_label'] in c.LABELS[:2] for r in binary),'binary uncertain exclusion')
    # Full ledger retains uncertain provenance; parsed labels retain its exact answer.
    parsed=[]
    raw_lines={}
    teacher=p.pilot.protocol()['teacher']['model']
    for row in ledger:
        if row['outcome'] not in c.LABELS: continue
        h=row['history'][-1]
        path=h['raw_response_path']
        if path not in raw_lines:
            raw_lines[path]=(c.HERE/path).read_bytes().splitlines()
        raw=c.strict_json(raw_lines[path][h['raw_response_line']-1])
        outcome,retry,answer=p.pilot.results.classify(raw,teacher)
        c.require(outcome==row['outcome'] and not retry,'semantic replay')
        parsed.append({'sample_key':row['sample_key'],'task':row['task'],
                       'label':answer['label'],'reason':answer['reason'],
                       'accepted':row['accepted'],'protocol_sha256':p.pilot.EXPECTED,**h})
    c.write_once(p.PRIVATE/'full_audit_ledger.jsonl',c.rows_bytes(ledger))
    c.write_once(p.PRIVATE/'parsed_labels.jsonl',c.rows_bytes(parsed))
    c.write_once(p.PRIVATE/'future_binary_supervision.jsonl',c.rows_bytes(binary))
    usages={'pilot':[],'production':[]}; batches=[]; hashes={}; models=set()
    for label,base,rounds in [('pilot',p.pilot.PILOT,1),('production',p.PRIVATE,attempt)]:
        for n in range(1,rounds+1):
            folder=base/f'round_{n}'
            manifest=c.read_json(folder/'request_manifest.json')
            for i in range(1,len(manifest['shards'])+1):
                state=folder/f'batch_{i:03d}'
                receipt=c.read_json(state/'download_receipt.json')
                b=receipt['batch']
                batches.append({'stage':label,'round':n,**{k:b.get(k) for k in
                    ('id','status','request_counts','created_at','completed_at','expired_at','cancelled_at')}})
                for f in receipt['files']:
                    path=state/f['path']; hashes[str(path.relative_to(c.HERE))]=c.sha(path)
                    for raw in c.read_rows(path):
                        body=(raw.get('response') or {}).get('body') or {}
                        if body.get('model'): models.add(body['model'])
                        u=body.get('usage')
                        if u:
                            usages[label].append({
                                'input':u['input_tokens'],'output':u['output_tokens'],
                                'reasoning':u.get('output_tokens_details',{}).get('reasoning_tokens',0),
                                'cached':u.get('input_tokens_details',{}).get('cached_tokens',0)})
    spec=p.pilot.protocol(); price=spec['pricing']
    def metrics(records):
        totals={k:sum(r[k] for r in records) for k in ('input','output','reasoning','cached')}
        tokens=[r['input']+r['output'] for r in records]
        return {**totals,'usage_records':len(records),
                'mean_tokens_per_request':statistics.mean(tokens) if tokens else None,
                'median_tokens_per_request':statistics.median(tokens) if tokens else None,
                'max_output_tokens_per_request':max((r['output'] for r in records),default=0),
                'estimated_cost_usd':(totals['input']*price['standard_input_per_million']+
                                      totals['output']*price['standard_output_per_million'])/1e6*price['batch_discount']}
    stats={stage:metrics(rows) for stage,rows in usages.items()}
    stats['combined']=metrics(usages['pilot']+usages['production'])
    histories=[h for r in ledger for h in r['history']]
    counts=Counter(r['outcome'] for r in ledger)
    failures=sum(r['outcome'] not in c.LABELS for r in ledger)
    c.require(stats['combined']['usage_records'] >= sum(counts[label] for label in c.LABELS),
              'missing usage for successful structured responses')
    tests=p.tests('FINAL')
    p.preservation();p.ignored()
    for path in [c.HERE/'e11c_production.py',c.HERE/'audit_e11c_production.py',
                 c.HERE/'test_e11c_production.py',c.HERE/'README_E11C_PRODUCTION.md',
                 p.PRIVATE/'full_audit_ledger.jsonl',p.PRIVATE/'parsed_labels.jsonl',
                 p.PRIVATE/'future_binary_supervision.jsonl',p.PRIVATE/'candidates.jsonl',
                 c.HERE/'E11C_PRODUCTION_PREFLIGHT.json',p.BASELINE]:
        hashes[str(path.relative_to(c.HERE))]=c.sha(path)
    for n in range(1,attempt+1):
        for name in ('requests.jsonl','request_manifest.json','ledger.jsonl','parse_report.json'):
            path=p.PRIVATE/f'round_{n}'/name
            hashes[str(path.relative_to(c.HERE))]=c.sha(path)
    audit={'status':'FAIL_BLOCKED_BILLING' if blocked else ('PASS' if not failures else 'FAIL'),'protocol_sha256':p.pilot.EXPECTED,
        'requested_teacher_model':spec['teacher']['model'],'returned_model_ids':sorted(models),
        'reasoning_effort':spec['teacher']['reasoning_effort'],'batches':batches,
        'production_rounds':attempt,'pilot_rounds':1,'pilot_count':300,'production_count':11700,
        'total_coverage':12000,'per_task_counts':dict(Counter(r['task'] for r in ledger)),
        'duplicate_count':0,'missing_count':0,
        'by_task':{task:{label:sum(r['task']==task and r['outcome']==label for r in ledger)
                         for label in c.LABELS} for task in c.POLICY},
        'labels':{label:counts[label] for label in c.LABELS},
        'uncertain_percent':100*counts['uncertain']/12000,
        'successful_structured_responses':sum(counts[label] for label in c.LABELS),
        'request_failures':sum(h['outcome'] not in c.LABELS for h in histories),
        'retry_count':len(histories)-12000,
        'schema_failures':sum(h['outcome']=='invalid_schema' for h in histories),
        'terminal_failures':sum(r['outcome'] not in c.LABELS and not r['retryable'] for r in ledger),
        'pending_technical_failures':sum(r['retryable'] for r in ledger),
        'definitive_labels':len(binary),'usage':stats,
        'operational_block':{'code':'billing_hard_limit_reached','prepared_retry_requests':4,
            'retry_batch_submitted':False,'batch_creation_http_400_failures':2,
            'reconciliation':'Exhaustive Batch listing found no Batch for the processed retry input file.',
            'resume':'Restore billing capacity; reconcile round_2 submission intents before creating a Batch using the existing uploaded file. Do not rerun round 1.'} if blocked else None,
        'cost_basis':'Actual returned usage; frozen pricing; reasoning included in output; no cache discount; estimates, not invoices.',
        'preservation':{'frozen_protocol_unchanged':True,'pilot_artifacts_unchanged':True,
                        'frozen_preparation_unchanged':True,'prior_E11_unchanged':True,
                        'row_level_files_git_ignored':True},
        'actions':{name:False for name in ('prompt_tuning','manual_label_correction','student_training',
            'development_evaluation','official_test_access','gpu_modal_run','commit','push',
            'fold_selection','leakage_purge','label_balancing')},
        'test_suites':tests,'artifact_sha256':hashes}
    c.save(c.HERE/'E11C_PRODUCTION_AUDIT.json',audit)
    lines=['# E11-C full production audit','',f"Status: {audit['status']}",
        f"Protocol SHA256: `{p.pilot.EXPECTED}`",'','300 pilot + 11,700 production = 12,000 unique candidates.',
        '', '| Task | hallucination | not_hallucination | uncertain |','|---|---:|---:|---:|']
    for task,values in audit['by_task'].items(): lines.append('| '+task+' | '+' | '.join(str(values[l]) for l in c.LABELS)+' |')
    lines.extend(['','```json',c.json.dumps(audit,indent=2),'```',''])
    c.write_once(c.HERE/'E11C_PRODUCTION_AUDIT.md','\n'.join(lines).encode())
    c.save(c.HERE/'E11C_PRODUCTION_MANIFEST.json',{'protocol_sha256':p.pilot.EXPECTED,
        'files_sha256':{**hashes,**{name:c.sha(c.HERE/name) for name in
          ('E11C_PRODUCTION_AUDIT.json','E11C_PRODUCTION_AUDIT.md')}}})
    print(c.json.dumps({k:v for k,v in audit.items() if k not in ('artifact_sha256','test_suites','batches')},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,choices=(1,2,3),required=True)
    parser.add_argument('--blocked-billing',action='store_true')
    args=parser.parse_args()
    audit(args.attempt,args.blocked_billing)
