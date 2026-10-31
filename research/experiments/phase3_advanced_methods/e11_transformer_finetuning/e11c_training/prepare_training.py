"""Offline E11-C training audit and fixed two-stage preparation. No model fits."""
import csv
import sys
from collections import Counter,defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
E11=HERE.parent
sys.path[:0]=[str(E11/'e11c'),str(E11),str(E11/'e11a_results')]
import e11c_common as c
import e11c_production as production
import e11a_prepare_data as a
import validate_e11a_protocol as av
import assemble_e11a_results as ev

PRIVATE=HERE/'private'


def text_keys(row):
    # Only text/task, never labels or ratings. Case-fold adds conservative overlap protection.
    norm=lambda s:c.normalize(s).casefold()
    task=row['task']; src,tgt,hyp=[norm(row[k]) for k in ('src','tgt','hyp')]
    result={'full':c.parts(task,src,tgt,hyp),'source_pair':c.parts(task,src,tgt),
            'hyp':c.parts(hyp),'reference':c.parts(task,norm(row[c.POLICY[task]]))}
    for field,text in [('src',src),('tgt',tgt)]:
        if text:result[field]=c.parts(task,text)
    return result


def purge(rows,heldout):
    blocked=defaultdict(set)
    for human in heldout:
        for name,value in text_keys(human).items():blocked[name].add(value)
    kept=[];removed=[]
    for row in rows:
        reasons=[name for name,value in text_keys(row).items() if value in blocked[name]]
        if reasons:removed.append({'sample_key':row['sample_key'],'reasons':reasons})
        else:kept.append(row)
    return kept,removed


def preserve():
    for name,digest in c.read_json(HERE/'PRESERVATION_BASELINE.json').items():
        c.require(c.sha(E11/name)==digest,'prior artifact changed: '+name)


def prepare():
    production.preservation()
    production.ignored()
    # Validate pinned E11-A model/tokenizer/prepared human splits without running preparation.
    av.validate_local()
    aspec=a.load_protocol()
    t=production.pilot.protocol()
    paths=[p for p in E11.rglob('*') if p.is_file() and '__pycache__' not in p.parts
           and not p.is_relative_to(HERE)]
    c.save(HERE/'PRESERVATION_BASELINE.json',{str(p.relative_to(E11)):c.sha(p) for p in paths})
    for name in ('E11C_PRODUCTION_MANIFEST.json','E11C_ALTERNATE_MODEL_RESCUE_MANIFEST.json'):
        production.check_hashes(c.HERE,c.read_json(c.HERE/name)['files_sha256'])
    pool=c.load_candidates(); bykey={r['sample_key']:r for r in pool}
    _,_,pilot=production.partition()
    with production.scope():_,ledger=production.pilot.results.parse_round(1,write=False)
    all_rows=pilot+ledger
    synthetic=[r['synthetic'] for r in all_rows if r['accepted']]
    c.require(len(synthetic)==len({r['sample_key'] for r in synthetic})==11887,'definitive population')
    c.require(Counter(r['llm_label'] for r in synthetic)=={'hallucination':5111,'not_hallucination':6776},'labels')
    c.require(all(r['teacher_model_id']=='gpt-5.6-sol' for r in synthetic),'teacher homogeneity')
    c.require(sum(r['outcome']=='uncertain' for r in all_rows)==109 and sum(r['retryable'] for r in all_rows)==4,'exclusions')
    c.require(c.read_rows(production.PRIVATE/'future_binary_supervision.jsonl')==
              [r['synthetic'] for row in pool for r in all_rows if r['sample_key']==row['sample_key'] and r['accepted']],
              'authoritative export replay')
    rescue=c.read_rows(c.PRIVATE/'azure_alternate_rescue/rescue_judgments.jsonl')
    c.require(not {r['sample_key'] for r in synthetic}&{r['sample_key'] for r in rescue},'Azure exclusion')
    humans=a.csv_rows(c.root()/aspec['data']['canonical_path'])
    assignments=a.csv_rows(c.root()/aspec['data']['folds_path'])
    fold_of={r['canonical_id']:int(r['fold_id']) for r in assignments}
    # The canonical ID and row index are split-scoped; compare content, not unrelated indices.
    c.require(len(humans)==len(fold_of)==561,'human identity coverage')
    labeled={r['sample_key']:r for r in synthetic}
    rows=[r for r in pool if r['sample_key'] in labeled]
    # Remove exact duplicated model inputs globally, deterministically; conflicting labels remove all.
    groups=defaultdict(list)
    for row in rows:groups[c.parts(row['task'],row['reference_text'],row['hyp'])].append(row)
    duplicate_removed=[];dedup=[]
    for group in groups.values():
        conflict=len({labeled[r['sample_key']]['label'] for r in group})>1
        dedup.extend([] if conflict else group[:1])
        duplicate_removed.extend({'sample_key':r['sample_key'],'reason':'conflicting_identical_input' if conflict else 'duplicate_input'}
                                 for r in (group if conflict else group[1:]))
    selected_keys={r['sample_key'] for r in dedup};rows=[r for r in rows if r['sample_key'] in selected_keys]
    c.write_once(PRIVATE/'duplicate_exclusions.jsonl',c.rows_bytes(duplicate_removed))
    folds={}
    for f in range(1,6):
        kept,removed=purge(rows,[r for r in humans if fold_of[r['canonical_id']]==f])
        stage1=[]
        for row in kept:
            stage1.append({'sample_id':row['sample_key'],'fold_id':0,'task':row['task'],
                'reference_field':c.POLICY[row['task']],
                'text':aspec['input']['sequence_a_template'].format(task=row['task'],reference=row['reference_text']),
                'text_pair':aspec['input']['sequence_b_template'].format(hyp=row['hyp']),
                'label':labeled[row['sample_key']]['label']})
        folder=PRIVATE/f'fold_{f}'
        c.write_once(folder/'synthetic.jsonl',c.rows_bytes(stage1))
        c.write_once(folder/'leakage_exclusions.jsonl',c.rows_bytes(removed))
        for split in ('train','heldout'):
            c.write_once(folder/f'{split}.jsonl',(E11/f'e11a_prepared/fold_{f}/{split}.jsonl').read_bytes())
        folds[str(f)]={'synthetic_rows':len(stage1),'leakage_exclusions':len(removed),
            'reasons':dict(Counter(reason for r in removed for reason in r['reasons'])),
            'class_counts':dict(Counter(str(r['label']) for r in stage1)),
            'per_task':{task:dict(Counter(str(r['label']) for r in stage1 if r['task']==task)) for task in c.POLICY},
            'human_train_rows':448 if f==1 else 449,'heldout_rows':113 if f==1 else 112,
            'files_sha256':{name:c.sha(folder/name) for name in ('synthetic.jsonl','leakage_exclusions.jsonl','train.jsonl','heldout.jsonl')}}
    # Exact baseline metrics from existing predictions, using the original evaluator only.
    human={r['canonical_id']:r for r in humans}
    aresult=c.read_json(E11/'e11a_results/E11A_RESULTS.json')
    aman=c.read_json(E11/'e11a_results/E11A_RESULTS_MANIFEST.json')
    apath=E11/'e11a_results/E11A_OOF_PREDICTIONS.jsonl'
    c.require(c.sha(apath)==aman['files_sha256']['oof_predictions'],'E11A OOF anchor')
    ametrics=ev.metric(c.read_rows(apath),human)
    c.require(ametrics==aresult['overall'],'E11A exact metric replay')
    e10dir=E11.parent/'phase3_e9_claim_verification/evaluation/E10'
    e10=c.read_json(e10dir/'E10_metrics.json')['metrics']['overall']
    ev.baseline('E10',e10dir/'E10_oof.csv',e10dir/'E10_metrics.json',e10,human,fold_of)
    stage1={**aspec['training'],'epochs':1,'checkpoint_selection':'final model after exactly one synthetic epoch',
            'class_weight_values_by_fold':{f:{k:folds[f]['synthetic_rows']/(2*v) for k,v in folds[f]['class_counts'].items()} for f in folds}}
    protocol={'experiment':'E11-C','status':'FROZEN_BEFORE_TRAINING','teacher_protocol_sha256':t['protocol_sha256'],
        'e11a_protocol_sha256':aspec['protocol_sha256'],'model':aspec['model'],'input':aspec['input'],
        'stage1':stage1,'stage2':aspec['training'],'output':aspec['output'],'folds_sha256':aspec['data']['folds_sha256'],
        'architecture':'five fold-specific synthetic Stage-1 checkpoints followed by five human Stage-2 fits',
        'fits':10,'seed':42,'stage1_choice':'One fixed conservative epoch; all other optimizer/input settings inherited from E11-A. No search.',
        'selection_override':'Current user instruction uses the full definitive pool after leakage/duplicate exclusions; supersedes earlier teacher-preparation balanced/capped selection. Teacher artifacts unchanged.',
        'leakage_policy':'NFC whitespace-normalized casefold full/task-source/task-target/task-reference/source-pair and global hypothesis matches to outer validation; no validation labels used.',
        'folds':folds,'requirements_sha256':c.sha(E11/'E11A_REQUIREMENTS.lock.txt')}
    protocol['protocol_sha256']=c.digest(c.encoded(protocol))
    c.save(HERE/'E11C_TRAINING_PROTOCOL.json',protocol)
    audit={'status':'PENDING_TESTS','model_fits':0,'teacher_pool':11887,'hallucination':5111,'not_hallucination':6776,
        'uncertain_excluded':109,'technical_failures_excluded':4,'Azure_rescue_excluded':4,
        'duplicate_candidate_ids':0,'duplicate_input_exclusions':len(duplicate_removed),'folds':folds,
        'E11A':ametrics,'E10':e10,'protocol_sha256':protocol['protocol_sha256'],
        'provenance':'Synthetic sample_key and source_row_index validated against hash-anchored unlabeled master and raw-source digest; human canonical IDs, source_split/row index and text are from hash-anchored canonical manifest. Split-scoped row indices are not cross-split identifiers.',
        'leakage_limit':'Conservative exact normalized content/source matching; undocumented upstream semantic derivations cannot be proven absent. No cross-split upstream source IDs are supplied.',
        'E11A_control':{'protocol':str(a.PROTOCOL),'training_code':str(E11/'e11a_train_fold.py'),
            'evaluation_code':str(E11/'e11a_results/assemble_e11a_results.py')},
        'folds_identical_to_E11A':True,'teacher_artifacts_unchanged':True,'official_test_access':False}
    c.save(HERE/'PRETRAINING_AUDIT_INITIAL.json',audit)
    preserve()
    print(c.json.dumps(audit,indent=2))


if __name__=='__main__':prepare()
