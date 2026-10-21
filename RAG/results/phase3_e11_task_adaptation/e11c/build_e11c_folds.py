"""Offline text-only purge audit or future balanced training-data construction.

No student fitting; constructing labeled datasets requires an explicit flag and
a complete, nonretryable result ledger replayed from archived raw API responses.
"""
import argparse
from collections import Counter
from e11c_common import *


def audit_purge():
    candidates=load_candidates()
    humans,folds=human_text()
    maps={f:purge_candidates(candidates,humans,folds,f) for f in range(1,6)}
    report={}
    for fold,mapping in maps.items():
        tasks={}
        for task in POLICY:
            group=[r for r in mapping if r['task']==task]
            tasks[task]={'candidates':len(group),'purged':sum(bool(r['matches']) for r in group),
                         'eligible':sum(not r['matches'] for r in group),
                         'matching_rules_nonexclusive':dict(Counter(k for r in group for k in r['matches']))}
        report[str(fold)]={'heldout_human':sum(v==fold for v in folds.values()),'tasks':tasks,
                          'purged_total':sum(bool(r['matches']) for r in mapping)}
    return report,maps


def build(attempt,allow=False):
    require(allow,'labeled dataset construction disabled; use --build-after-labeling only later')
    from parse_e11c_results import parse_round
    spec=load_protocol()
    parsed,ledger=parse_round(attempt,write=False)
    require(parsed['retryable']==0,'pending operational retries; labels not final')
    purge_report,maps=audit_purge()
    accepted=[r['synthetic'] for r in ledger if r['accepted']]
    prepared=read_json(HERE.parent/'E11A_PREPARATION_MANIFEST.json')
    report={'protocol_sha256':spec['protocol_sha256'],'attempt':attempt,'folds':{},
            'training_started':False,'human_synthetic_weighting':'NOT_FROZEN'}
    for fold,mapping in maps.items():
        eligible={r['sample_key'] for r in mapping if not r['matches']}
        survivors=[r for r in accepted if r['sample_key'] in eligible]
        selected_rows=[]
        counts={}
        for task in POLICY:
            chosen=balanced(survivors,fold,task)
            counts[task]={'accepted_after_purge':dict(Counter(r['llm_label'] for r in survivors if r['task']==task)),
                          'kept':len(chosen),'per_class':len(chosen)//2}
            selected_rows.extend(chosen)
        require(len(selected_rows)<=9000 and len({r['sample_key'] for r in selected_rows})==len(selected_rows),
                'synthetic population')
        hspec=prepared['folds'][str(fold)]
        human_path=HERE.parent/hspec['train_path']
        require(sha(human_path)==hspec['train_sha256'],'frozen human training file changed')
        human_rows=read_rows(human_path)
        require(len(human_rows)==(448 if fold==1 else 449) and
                all(r['fold_id']!=fold for r in human_rows),'human training fold isolation')
        human_rows=[{**r,'source':'human'} for r in human_rows]
        destination=PRIVATE/'training_sets'/f'fold_{fold}'
        write_once(destination/'human.jsonl',rows_bytes(human_rows))
        write_once(destination/'llm_synthetic.jsonl',rows_bytes(selected_rows))
        write_once(destination/'purge_map.jsonl',rows_bytes(mapping))
        report['folds'][str(fold)]={'human_rows':len(human_rows),'synthetic_rows':len(selected_rows),
                'per_task':counts,'text_purge':purge_report[str(fold)],
                'human_sha256':sha(destination/'human.jsonl'),
                'synthetic_sha256':sha(destination/'llm_synthetic.jsonl')}
    save(PRIVATE/'training_sets/manifest.json',report)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--audit-text-only',action='store_true')
    p.add_argument('--build-after-labeling',action='store_true')
    p.add_argument('--attempt',type=int,choices=(1,2,3),default=1)
    a=p.parse_args()
    require(a.audit_text_only != a.build_after_labeling,'choose exactly one mode')
    if a.audit_text_only:
        report,_=audit_purge()
        save(HERE/'E11C_TEXT_PURGE_AUDIT.json',report)
    else:
        report=build(a.attempt,a.build_after_labeling)
    print(json.dumps(report,indent=2))
