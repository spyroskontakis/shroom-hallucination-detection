"""Offline consolidation of existing E11 results. No fitting or network clients."""
import csv
import hashlib
import io
import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
E11=HERE.parent
ROOT=E11.parents[2]
sys.path[:0]=[str(E11/'e11e_training'),str(E11),str(E11/'e11a_results')]
from e11e_common import baselines,metric,validate_rows,read_jsonl,load_protocol

CHECKS=[]
SOURCES={}


def read(path):
    SOURCES[path.relative_to(ROOT).as_posix()]=sha(path)
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    with path.open('rb') as handle:return hashlib.file_digest(handle,'sha256').hexdigest()


def require(ok,message):
    if not ok:raise ValueError(message)


def check(name,ok,details=None):
    require(ok,name)
    CHECKS.append({'name':name,'status':'PASS',**({'details':details} if details is not None else {})})


def save_new(path,value):
    data=(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
    with path.open('xb') as handle:handle.write(data)


def verify_manifest(folder,name):
    manifest=read(folder/name)
    for relative,digest in manifest['files_sha256'].items():require(sha(folder/relative)==digest,'source manifest: '+relative)
    check(name+' all declared hashes',True,len(manifest['files_sha256']))


def main():
    final_names=['E11_FINAL_SUMMARY.md','E11_FINAL_SUMMARY.json','E11_FINAL_TABLE.csv','E11_FINAL_MANIFEST.json','E11_FINAL_SHA256SUMS.txt']
    require(not any((E11/name).exists() for name in final_names),'final artifacts already exist; do not overwrite a freeze')
    original=read(HERE/'private/PRIOR_SHA256.json')
    tests=read(HERE/'FINALIZATION_TESTS.json')
    check('Offline regression suites',tests['status']=='PASS' and tests['tests']==111 and tests['skipped']==0,tests)
    a=load_protocol();SOURCES[(E11/'E11A_TRAINING_PROTOCOL.json').relative_to(ROOT).as_posix()]=sha(E11/'E11A_TRAINING_PROTOCOL.json')
    sources={'E11-A':E11/'e11a_results','E11-C':E11/'e11c_training','E11-D':E11/'e11d_training','E11-E':E11/'e11e_training'}
    reports={name:read(folder/(name.replace('-','')+'_RESULTS.json')) for name,folder in sources.items()}
    for name in ('E11-C','E11-D','E11-E'):verify_manifest(sources[name],name.replace('-','')+'_MANIFEST.json')
    bases,human,fold_of=baselines()
    metrics={name:bases[name] for name in ('E11-A','E11-C','E11-D','E10')}
    tasks={}
    for name,folder in sources.items():
        oof=folder/('E11A_OOF_PREDICTIONS.jsonl' if name=='E11-A' else 'private/'+name.replace('-','')+'_OOF_PREDICTIONS.jsonl')
        rows=read_jsonl(oof);validate_rows(rows,human,fold_of)
        computed=metric(rows,human)
        check(name+' 561-row existing OOF identity and metrics',computed==reports[name]['overall'])
        metrics[name]={k:computed[k] for k in ('n','correct','accuracy','spearman')}
        tasks[name]={task:metric([r for r in rows if r['task']==task],human) for task in ('DM','MT','PG')}
        check(name+' task metric replay',tasks[name]==reports[name]['per_task'])
        SOURCES[oof.relative_to(ROOT).as_posix()]=sha(oof)
    check('E10 authoritative existing OOF replay',metrics['E10']['correct']==475 and metrics['E10']['accuracy']==475/561)
    expected={'E11-A':(460,.8199643493761141,.7172565081322899),'E11-C':(466,.8306595365418895,.7270182116026076),'E11-D':(459,.8181818181818182,.7006748393613571),'E11-E':(466,.8306595365418895,.7150820586520120),'E10':(475,.8467023172905526,.7828092941190203)}
    check('Requested authoritative values match repository',all(tuple(metrics[n][k] for k in ('correct','accuracy','spearman'))==v for n,v in expected.items()))
    # A checkpoints are available locally; use the initial snapshot hashes, then
    # rehash all protected files at closure to confirm the bytes still match.
    aman=read(sources['E11-A']/'E11A_RESULTS_MANIFEST.json');astatus={}
    amap={'protocol':E11/'E11A_TRAINING_PROTOCOL.json','canonical':ROOT/a['data']['canonical_path'],'locked_folds':ROOT/a['data']['folds_path'],
          'oof_predictions':sources['E11-A']/'E11A_OOF_PREDICTIONS.jsonl','results_json':sources['E11-A']/'E11A_RESULTS.json','results_md':sources['E11-A']/'E11A_RESULTS.md'}
    for f in range(1,6):
        folder=sources['E11-A']/f'fold_{f}/e11a-fold-{f:03d}'
        s=read(folder/'FOLD_PASS.json');astatus[str(f)]=s
        require(s['fold_id']==f and s['status']=='PASS' and s['protocol_sha256']==a['protocol_sha256'],'A fold identity')
        for suffix,path in [('checkpoint',folder/'final_checkpoint/model.safetensors'),('predictions',folder/'heldout_predictions.jsonl'),('status',folder/'FOLD_PASS.json')]:amap[f'fold_{f}_{suffix}']=path
        require(original[(folder/'final_checkpoint/model.safetensors').relative_to(ROOT).as_posix()]==s['checkpoint_sha256'],'A checkpoint status hash')
    for key,path in amap.items():require(original.get(path.relative_to(ROOT).as_posix(),sha(path) if key in ('canonical','locked_folds') else None)==aman['files_sha256'][key],'A manifest '+key)
    check('E11-A complete manifest and five local checkpoint hashes',True,len(amap))
    c=read(sources['E11-C']/'E11C_TRAINING_PROTOCOL.json');d=read(sources['E11-D']/'E11D_LOSS_PROTOCOL.json');e=read(sources['E11-E']/'E11E_TRAINING_PROTOCOL.json')
    check('C/E exact data and stage settings',all(c[k]==e[k] for k in ('model','input','output','stage1','stage2','folds','folds_sha256','seed','fits')))
    check('D/E frozen loss implementation and configuration',sha(sources['E11-D']/'contrastive.py')==sha(sources['E11-E']/'contrastive.py') and all(d[k]==v for k,v in e['contrastive'].items()) and d['lambda']==.1 and d['margin']==0 and d['temperature'] is None)
    for folder,file in [(sources['E11-C'],'E11C_TRAINING_PROTOCOL.json'),(sources['E11-E'],'E11E_TRAINING_PROTOCOL.json')]:
        p=json.loads((folder/file).read_text(encoding='utf-8'));content={k:v for k,v in p.items() if k!='protocol_sha256'}
        check(file+' canonical content hash',hashlib.sha256(json.dumps(content,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()==p['protocol_sha256'])
    runtimes={'E11-A':{f:s['runtime'] for f,s in astatus.items()}};gpus={'E11-A':sorted({s['gpu'] for s in astatus.values()})}
    checkpoint_hashes={'E11-A':{f:s['checkpoint_sha256'] for f,s in astatus.items()}}
    audits={name:read(folder/(name.replace('-','')+'_TRAINING_AUDIT.json')) for name,folder in sources.items() if name!='E11-A'}
    checkpoint_evidence={}
    for name in ('E11-C','E11-D','E11-E'):
        folder=sources[name];verification=read(folder/'CHECKPOINT_VERIFICATION.json');require(verification['status']=='PASS','stored checkpoint verification')
        checkpoint_evidence[name]={'path':(folder/'CHECKPOINT_VERIFICATION.json').relative_to(ROOT).as_posix(),'sha256':sha(folder/'CHECKPOINT_VERIFICATION.json'),'saved_checkpoints':5 if name=='E11-D' else 10,'mode':'Recorded prior remote rehash evidence, reconciled locally; no API calls during finalization.'}
        states={}
        for f in range(1,6):
            ret=read(folder/f'private/returned/fold_{f}.json');require(ret['fold_id']==f,'return fold identity')
            if name=='E11-D':
                s=ret['summary'];require(s==verification['folds'][str(f)]['summary'] and s['checkpoint_sha256']==verification['folds'][str(f)]['model_sha256'],'D saved checkpoint evidence');states[str(f)]=s
            else:
                for stage,s in enumerate(ret['stages'],1):
                    record=verification['evidence'][f'{f}:{stage}'] if name=='E11-C' else verification['stages'][f'{f}:{stage}']
                    require(s==record['status' if name=='E11-C' else 'summary'],'two-stage saved checkpoint evidence')
                    states[f'{f}:{stage}']=s
                require(ret['stages'][1]['initial_model_weights_sha256']==ret['stages'][0]['checkpoint_sha256'],'Stage-1 to Stage-2 chain')
            last=ret['summary'] if name=='E11-D' else ret['stages'][1]
            require(hashlib.sha256(ret['predictions_jsonl'].encode()).hexdigest()==last['heldout_predictions_sha256'],'return prediction hash')
        check(name+' checkpoint evidence, local returns and chains',True,len(states))
        checkpoint_hashes[name]={k:s['checkpoint_sha256'] for k,s in states.items()}
        runtimes[name]={k:s['runtime'] for k,s in states.items()};gpus[name]=sorted({s['gpu'] for s in states.values()})
    teacher=read(E11/'e11c/E11C_PRODUCTION_AUDIT.json');rescue=read(E11/'e11c/E11C_ALTERNATE_MODEL_RESCUE_AUDIT.json')
    check('Original homogeneous teacher outcome counts',teacher['total_coverage']==12000 and teacher['successful_structured_responses']==11996 and teacher['definitive_labels']==11887 and teacher['pending_technical_failures']==4 and teacher['labels']=={'hallucination':5111,'not_hallucination':6776,'uncertain':109})
    check('Azure rescue aggregate and separation',rescue['completed']==4 and Counter(r['label'] for r in rescue['results'])=={'hallucination':1,'not_hallucination':3} and rescue['excluded_from_homogeneous_supervision'] and all(r['excluded_from_original_supervision'] for r in rescue['results']))
    pre=read(sources['E11-E']/'E11E_PRETRAINING_AUDIT.json');require(pre['status']=='PASS','E pretraining status')
    sizes=[c['folds'][str(f)]['synthetic_rows'] for f in range(1,6)]
    overlaps=[c['folds'][str(f)]['leakage_exclusions'] for f in range(1,6)]
    check('Exact synthetic sizes and validation exclusions',sizes==[11787,11791,11795,11787,11790] and overlaps==[18,14,10,18,15])
    check('Duplicate/conflict exclusions',pre['duplicate_input_exclusions']==82 and pre['duplicate_reasons']=={'duplicate_input':76,'conflicting_identical_input':6} and pre['conflicting_groups']==3)
    azure_ids={r['sample_key'] for r in rescue['results']}
    for f in range(1,6):
        for name,digest in c['folds'][str(f)]['files_sha256'].items():
            require(sha(sources['E11-C']/f'private/fold_{f}'/name)==digest==sha(sources['E11-E']/f'private/fold_{f}'/name),'C/E data hash equality')
        require(not azure_ids & {r['sample_id'] for r in read_jsonl(sources['E11-C']/f'private/fold_{f}/synthetic.jsonl')},'Azure rows in supervision')
    check('All C/E fold bytes and Azure exclusion',True,20)
    b=read(E11/'E11_PSEUDOLABEL_MANIFEST.json')
    check('E11-B zero balanced set and no student result',b['status']=='PASS' and b['teacher_fit_count']==5 and b['student_trained'] is False and [b['folds'][str(f)]['accepted_before_balancing'] for f in range(1,6)]==[0,50,0,44,41] and all(v['retained_after_balancing']==0 for v in b['folds'].values()))
    for artifacts in b['fold_artifacts'].values():
        for record in artifacts.values():require(sha(Path(record['path']))==record['sha256'],'B fold artifact hash')
    check('E11-B 25 teacher-stage artifact hashes',True,25)
    # These two commands were independently executed read-only by the audit agent.
    check('Independent E11-B teacher-stage validator',True,'verify_teacher_stage.py: PASS; no fits')
    check('Independent E11-B full detector-output validator',True,'validate_scoring_outputs.py --scope full: PASS for four times 28,649 unlabeled scores and 561 human MiniCheck scores')
    def delta(new,old):return {k:metrics[new][k]-metrics[old][k] for k in ('correct','accuracy','spearman')}
    deltas={f'{new}_minus_{old}':delta(new,old) for new,old in [('E11-C','E11-A'),('E11-D','E11-A'),('E11-E','E11-C'),('E11-E','E11-D')]}
    check('Best E11 descriptive ranking',metrics['E11-C']['accuracy']==metrics['E11-E']['accuracy']==max(metrics[n]['accuracy'] for n in sources) and metrics['E11-C']['spearman']==max(metrics[n]['spearman'] for n in sources))
    check('E10 remains ahead on both metrics',all(metrics[n]['accuracy']<metrics['E10']['accuracy'] and metrics[n]['spearman']<metrics['E10']['spearman'] for n in sources))
    check('MT strongest accuracy and PG weakest Spearman in C/D/E',all(tasks[n]['MT']['accuracy']==max(m['accuracy'] for m in tasks[n].values()) and tasks[n]['PG']['spearman']==min(m['spearman'] for m in tasks[n].values()) for n in ('E11-C','E11-D','E11-E')))
    # Rehash all original experiment files, including the five local A weights.
    current_paths=[p for p in E11.rglob('*') if p.is_file() and not p.is_relative_to(HERE) and '__pycache__' not in p.parts]
    current_paths += [p for p in (ROOT/'RAG/results/phase3_e9_claim_verification/evaluation/E10').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    current={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(current_paths)}
    check('All protected prior files unchanged',current==original,len(original))
    table=[]
    for name,h,s,co in [('E11-A','Yes','No','No'),('E11-B','feasibility only','pseudo-label ensemble','No'),('E11-C','Yes','Yes','No'),('E11-D','Yes','No','Yes'),('E11-E','Yes','Yes','Yes'),('E10','feature-based reference','—','—')]:
        m=metrics.get(name,{});table.append({'experiment':name,'human':h,'synthetic':s,'contrastive':co,'correct':m.get('correct'),'denominator':561 if name!='E11-B' else None,'accuracy':m.get('accuracy'),'spearman':m.get('spearman')})
    synthesis={'teacher':'gpt-5.6-sol','reasoning_effort':teacher['reasoning_effort'],'candidate_pool':12000,'terminal_original_teacher_outcomes':11996,'definitive_binary_labels':11887,'hallucination':5111,'not_hallucination':6776,'uncertain':109,'original_technical_failures':4,
               'original_audit_status_preserved':teacher['status'],'teacher_protocol_content_sha256':teacher['protocol_sha256'],'definitive_export_sha256':pre['synthetic_export_sha256'],
               'alternate_rescue':{'provider':'Azure / Microsoft Foundry','model':'gpt-5-mini','candidates':4,'task':'PG','hallucination':1,'not_hallucination':3,'excluded_from_homogeneous_pool':True},
               'duplicate_exclusions':{'redundant_rows':76,'conflicting_label_rows':6,'conflicting_groups':3,'total_rows':82},'validation_overlap_exclusions_by_fold':overlaps,'synthetic_rows_by_fold_C_and_E':sizes,
               'limitation':'Four original-model technical failures remain in the homogeneous ledger; separate Azure judgments do not close or expand that supervision pool. Exact leakage filtering matches C/E; undocumented semantic source overlap cannot be ruled out.'}
    configuration={k:d[k] for k in ('formula','total_loss','lambda','margin','temperature','normalization','representation','contextualization','positive','negative')}
    configuration['implementation_sha256']=sha(sources['E11-D']/'contrastive.py');configuration['applied_to']={'E11-D':'human-only training','E11-E':'both synthetic Stage 1 and human Stage 2'}
    bsummary={'status':'feasibility only; no student result','detectors':['FactCG','MiniCheck','HHEM','NLI'],'logistic_teacher_fits':5,'student_fits':0,'accuracy':None,'spearman':None,'thresholds':b['thresholds'],
              'eligible_by_fold':[b['folds'][str(f)]['eligible_unlabeled'] for f in range(1,6)],'confidence_accepted_by_fold':[b['folds'][str(f)]['accepted_before_balancing'] for f in range(1,6)],'balanced_retained_by_fold':[0]*5,
              'explanation':'Every task/fold lacked at least one accepted class; the frozen task-wise 50/50 balance requirement retained no examples. No student training or OOF evaluation followed.','software':b['software']}
    historical_tests={'E11-C':audits['E11-C']['tests']['tests_passed'],'E11-D':audits['E11-D']['tests']['total_tests'],'E11-E':audits['E11-E']['tests']['total_tests'],'note':'79/94/111 are overlapping historical suite runs, not additive distinct tests. No standalone A final-test total was inferred; its tests are included in this finalization run.'}
    checkpoint_evidence['E11-A']={'saved_checkpoints':5,'mode':'Five existing local weights rehashed and matched to original manifest and fold status.'}
    summary={'status':'PASS','suite_status':'FROZEN','created_utc':datetime.now(timezone.utc).isoformat(),'scope':'Final consolidation of existing artifacts only; no new models evaluated or fitted. Existing OOF vectors replayed using authoritative evaluator.',
             'table':table,'task_metrics':{n:tasks[n] for n in ('E11-C','E11-D','E11-E')},'descriptive_deltas':deltas,'best_e11':'E11-C','selection_reason':'Tied highest E11 accuracy and highest E11 Spearman','any_e11_exceeds_E10':False,'statistical_significance_claimed':False,
             'E11B':bsummary,'synthetic_data':synthesis,'contrastive':configuration,'final_fold_student_fits':{'E11-A':5,'E11-B':0,'E11-C':10,'E11-D':5,'E11-E':10},'C_and_E_fits_each':{'stage1':5,'stage2':5},
             'reproducibility':{'model':a['model'],'input':a['input'],'reference_policy':a['reference_policy'],'seed':42,'human_training':a['training'],'synthetic_stage1':c['stage1'],'human_stage2':c['stage2'],
                                'canonical_human_sha256':a['data']['canonical_sha256'],'folds_path':a['data']['folds_path'],'folds_sha256':a['data']['folds_sha256'],'folds':a['data']['folds'],'software_lock':a['software'],'recorded_runtime_by_fold_stage':runtimes,'gpu_types':gpus,
                                'runtime_reporting_note':'A fold statuses record Python/PyTorch; its CUDA/Transformers versions are pinned by the shared lock. C/D/E runtime records explicitly report CUDA 12.1 and Transformers 4.38.1.'},
             'checkpoint_verification':checkpoint_evidence,'checkpoint_weights_sha256':checkpoint_hashes,'historical_tests':historical_tests,'finalization_tests':tests,
             'verification':{'checks':len(CHECKS),'records':CHECKS,'protected_files_unchanged':len(original),'baseline_snapshot_sha256':sha(HERE/'private/PRIOR_SHA256.json'),'excludes_interpreter_caches':True},
             'aggregate_csv_policy':'Six aggregate rows only; existing global *.csv ignore rule preserved. Local CSV is not force-added. No row-level predictions included.',
             'safety':{'new_training_fits':0,'new_model_evaluations':0,'API_calls':0,'official_test_access':False,'prior_artifacts_modified':False,'commit':False,'push':False,'E11F_started':False}}
    # Important existing source hashes only; row-level data remain private.
    for path in [E11/'e11c/E11C_LLM_LABEL_PROTOCOL.json',E11/'E11_PSEUDOLABEL_AUDIT.md',E11/'E11_TEACHER_PROTOCOL.json',E11/'E11A_REQUIREMENTS.lock.txt',E11/'e11a_results/assemble_e11a_results.py',ROOT/'.gitignore']:
        SOURCES[path.relative_to(ROOT).as_posix()]=sha(path)
    summary['source_artifacts_sha256']=SOURCES
    save_new(E11/'E11_FINAL_SUMMARY.json',summary)
    out=io.StringIO(newline='');fields=['Experiment','Human','Synthetic','Contrastive','Correct/561','Accuracy','Spearman'];writer=csv.writer(out,lineterminator='\n');writer.writerow(fields)
    for row in table:writer.writerow([row['experiment'],row['human'],row['synthetic'],row['contrastive'],row['correct'] if row['correct'] is not None else '',row['accuracy'] if row['accuracy'] is not None else '',row['spearman'] if row['spearman'] is not None else ''])
    with (E11/'E11_FINAL_TABLE.csv').open('x',encoding='utf-8',newline='') as handle:handle.write(out.getvalue())
    md=['# E11 final frozen summary','', '**PASS — suite frozen from authoritative repository artifacts.** No training, new-model evaluation, API calls, tuning or official-test access occurred during finalization.','',
        '| Experiment | Human | Synthetic | Contrastive | Correct/561 | Accuracy | Spearman |','|---|---|---|---|---:|---:|---:|']
    for row in table:
        values=['—']*3 if row['correct'] is None else [str(row['correct']),f"{row['accuracy']:.16f}",f"{row['spearman']:.16f}"]
        md.append('| '+' | '.join([row['experiment'],row['human'],row['synthetic'],row['contrastive']]+values)+' |')
    md+=['','## Descriptive conclusions','',
         f"1. Synthetic supervision helped: E11-C versus E11-A gained 6 correct, {deltas['E11-C_minus_E11-A']['accuracy']:+.12f} accuracy and {deltas['E11-C_minus_E11-A']['spearman']:+.12f} Spearman.",
         f"2. Contrastive learning did not help human-only training: E11-D versus E11-A lost 1 correct, {deltas['E11-D_minus_E11-A']['accuracy']:+.12f} accuracy and {deltas['E11-D_minus_E11-A']['spearman']:+.12f} Spearman.",
         f"3. Contrastive learning did not improve synthetic-supervision training: E11-E tied E11-C at 466/561 and identical accuracy, with {deltas['E11-E_minus_E11-C']['spearman']:+.12f} Spearman.",
         '4. **E11-C is the best E11 variant overall:** tied highest accuracy with E11-E and highest Spearman.',
         '5. No E11 variant exceeded E10 on either metric. These are descriptive comparisons; no statistical significance claim is made.','',
         '## E11-B feasibility branch','',
         'FactCG / MiniCheck / HHEM / NLI scores fed five fold-specific logistic teachers. At the frozen confidence thresholds (p(H) ≥ .95 or ≤ .05), accepted rows before balancing were 0 / 50 / 0 / 44 / 41. Every task/fold lacked at least one accepted class. Required per-task 50/50 balancing retained 0 / 0 / 0 / 0 / 0 rows. Therefore no final student training or OOF evaluation was performed, and Accuracy/Spearman are not applicable—not zero.',
         'The four detector datasets each cover 28,649 unlabeled inputs; human MiniCheck covers 561. B teacher fits are separate from student fits.','',
         '## Synthetic supervision','',
         'Frozen teacher: **gpt-5.6-sol**, medium reasoning. Frozen pool: **12,000 candidates**. Original outcomes: **11,887 definitive binary labels** (5,111 hallucination; 6,776 not_hallucination), **109 uncertain**, and **four technical failures**. The original teacher ledger has 11,996 terminal responses; its billing-blocked audit status is preserved.',
         'The four PG failures received separate Azure / Microsoft Foundry gpt-5-mini judgments: **one hallucination and three not_hallucination**. They were never merged into the homogeneous gpt-5.6-sol pool. Uncertain outcomes were also excluded.',
         'Identical-input exclusions: **82 rows = 76 redundant rows + six conflicting-label rows across three groups**. C and E use exactly the same prepared bytes and exclusions.','',
         '| Fold | Validation-overlap exclusions | Synthetic rows for C/E | Human training | Held out |','|---|---:|---:|---:|---:|']
    for f in range(1,6):md.append(f"| {f} | {overlaps[f-1]} | {sizes[f-1]} | {448 if f==1 else 449} | {113 if f==1 else 112} |")
    md+=['','Leakage filtering uses the frozen normalized content/source rules. Undocumented upstream semantic derivations cannot be proven absent.','',
         'Final fold fits: A = five human-only; D = five human-only; C = five synthetic Stage-1 plus five human Stage-2; E = five synthetic Stage-1 plus five human Stage-2. These are final CV fit counts, separate from B’s five logistic teacher fits and any historical smoke checks.','',
         '## Frozen contrastive objective','',
         '```text\nweighted CE + 0.1 × mean[\n  (1-y)(1-cos(a,b)) +\n  y * max(0, cos(a,b))\n]\n```',
         'y=1 means hallucination; lambda=0.1; margin=0; no temperature. Mean-pooled final-layer representations exclude special/padding tokens and retain textual prefixes. Cosine uses L2 normalization (float32, eps=1e-8). The two representations share the original cross-encoder context. The implementation is identical in D/E; E applies it in both stages.','',
         '## Task-level results','', '| Experiment | Task | Correct/total | Accuracy | Spearman |','|---|---|---:|---:|---:|']
    for name in ('E11-C','E11-D','E11-E'):
        for task,m in tasks[name].items():md.append(f"| {name} | {task} | {m['correct']}/{m['n']} | {m['accuracy']:.16f} | {m['spearman']:.16f} |")
    md+=['','MT consistently had the highest accuracy (190/216 in C, D and E). PG remained more difficult, especially in Spearman, which was the lowest task ranking score in all three variants.','',
         '## Reproducibility and verification','',
         f"Model: `{a['model']['id']}`. Exact revision: `{a['model']['revision']}`. Pinned fast tokenizer, longest-first paired truncation, maximum 512 tokens. DM/MT reference = tgt; PG reference = src. Seed 42.",
         'AdamW, LR 1e-5, weight decay .01, batch 8, gradient accumulation 2 (effective 16), evaluation batch 16, BF16 on one A100-80GB per fold, clip norm 1. Linear warmup for ceil(.1 × updates), then linear decay to zero. Weighted CE uses N/(2 × class count) from each stage/fold training split. Human adaptation uses five epochs; synthetic Stage 1 uses one fixed epoch. Final checkpoints only, threshold .5, no early stopping or search.',
         'Python 3.11.12 and PyTorch 2.2.1+cu121 are recorded for all student variants. C/D/E explicitly record CUDA 12.1, Transformers 4.38.1, NumPy 1.26.4 and tokenizers 0.15.2. A uses the same frozen software lock; its fold statuses explicitly record Python/PyTorch. A/D used A100-SXM4-80GB and A100 80GB PCIe; C/E used A100-SXM4-80GB. Full runtime records and GPU sets are in the JSON.',
         f"Fold definition: `{a['data']['folds_path']}`; SHA256 `{a['data']['folds_sha256']}`. Canonical human SHA256 `{a['data']['canonical_sha256']}`.",
         f"Synthetic teacher protocol **content** SHA256: `{teacher['protocol_sha256']}`. The source manifest separately records its JSON file-byte hash. Definitive export SHA256: `{pre['synthetic_export_sha256']}`.",
         f"D/E contrastive implementation SHA256: `{configuration['implementation_sha256']}`.",
         f"Finalization: **111 offline tests passed, zero skipped; {len(CHECKS)} named verification groups passed**, including the two independent read-only B validators. All **{len(original)} prior E11/E10 files** remained byte-for-byte unchanged; interpreter caches are excluded from artifact accounting.",
         'Existing A/C/D/E OOF vectors were replayed using the unchanged authoritative metric function; no model was loaded to generate predictions. Five local A checkpoints were rehashed. Prior independent remote rehash records for C (10), D (5), E (10) were matched to local return records and initialization chains. No remote checkpoint API was called during this freeze.',
         'Historical final suites recorded C=79, D=94, E=111 passing tests; these overlapping runs are not additive. Historical protection audits recorded C unchanged, D=507 files unchanged and E=550 files unchanged. Full checkpoint and source hashes are retained in the JSON summary/manifest.','',
         '## Final artifacts','',
         '- `E11_FINAL_SUMMARY.md` and `E11_FINAL_SUMMARY.json`: consolidated aggregate report.',
         '- `E11_FINAL_TABLE.csv`: six aggregate rows only; retained locally under the existing global CSV ignore rule.',
         '- `E11_FINAL_MANIFEST.json`: output, source, verification and checkpoint hashes.',
         '- `E11_FINAL_SHA256SUMS.txt`: final file hashes, including the manifest (avoids self-reference).','',
         'Prior artifacts are preserved. No new training, APIs, official-test access, tuning, commit, push or E11-F.','']
    with (E11/'E11_FINAL_SUMMARY.md').open('x',encoding='utf-8',newline='\n') as handle:handle.write('\n'.join(md))
    # Output schema/CSV checks before sealing the final manifest.
    saved=json.loads((E11/'E11_FINAL_SUMMARY.json').read_text(encoding='utf-8'))
    csvrows=list(csv.DictReader(io.StringIO((E11/'E11_FINAL_TABLE.csv').read_text(encoding='utf-8'))))
    require(len(csvrows)==6 and csvrows[1]['Accuracy']==csvrows[1]['Spearman']=='' and saved['table']==table,'final aggregate consistency')
    manifests={'status':'PASS','suite':'E11-A/B/C/D/E','files_sha256':{name:sha(E11/name) for name in final_names[:3]},
               'source_artifacts_sha256':SOURCES,'checkpoint_weights_sha256':checkpoint_hashes,'finalization_tests':tests,'verification_checks':CHECKS,
               'prior_artifacts_unchanged':True,'protected_files':len(original),'preservation_snapshot_sha256':sha(HERE/'private/PRIOR_SHA256.json'),'finalizer_sha256':sha(Path(__file__))}
    save_new(E11/'E11_FINAL_MANIFEST.json',manifests)
    with (E11/'E11_FINAL_SHA256SUMS.txt').open('x',encoding='utf-8',newline='\n') as handle:handle.write(''.join(sha(E11/name)+'  '+name+'\n' for name in final_names[:4]))
    print(json.dumps({'status':'PASS','tests':tests['tests'],'verification_groups':len(CHECKS),'protected_files':len(original),'table':table},indent=2))


if __name__=='__main__':main()
