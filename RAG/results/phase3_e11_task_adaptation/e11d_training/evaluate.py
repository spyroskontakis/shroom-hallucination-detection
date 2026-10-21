"""Evaluate the single E11-D return using the unchanged E11-A metric function."""
import hashlib
import json
import math
from collections import Counter
from prepare import HERE, E11, ROOT, save, sha_file, require, baselines, metric, protected_files


def validate_rows(rows, human, folds, fold_id=None):
    expected = {sid for sid in human if fold_id is None or folds[sid] == fold_id}
    ids = [r['sample_id'] for r in rows]
    require(len(ids) == len(set(ids)) == len(expected) and set(ids) == expected, 'OOF ID coverage')
    for r in rows:
        sid = r['sample_id']; p = r['p_H']
        require(r['fold_id'] == folds[sid] and r['task'] == human[sid]['task'] and r['gold_label'] == int(human[sid]['label_bin']), 'row identity')
        require(isinstance(p,(int,float)) and math.isfinite(p) and 0 <= p <= 1 and r['predicted_class'] == int(p >= .5), 'probability or class')
    for f in sorted({r['fold_id'] for r in rows}):
        require({r['predicted_class'] for r in rows if r['fold_id']==f} == {0,1}, 'fold class collapse')


def collect():
    bases, human, folds = baselines()
    protocol = json.loads((HERE/'E11D_LOSS_PROTOCOL.json').read_text())
    all_rows=[]; reports={}
    require(len(list((HERE/'private/returned').glob('fold_*.json'))) == 5, 'exactly five returns')
    for f in range(1,6):
        returned = json.loads((HERE/f'private/returned/fold_{f}.json').read_text())
        s=returned['summary']; rows=[json.loads(line) for line in returned['predictions_jsonl'].splitlines()]
        frozen=protocol['data']['folds'][f-1]
        require(returned['fold_id']==s['fold_id']==f and s['status']=='PASS' and s['mode']=='fold' and s['run_id']==f'e11d-fold-{f:03d}', 'fold result identity')
        require(s['protocol_sha256']==protocol['e11a_protocol_sha256'] and s['loss_protocol_sha256']==sha_file(HERE/'E11D_LOSS_PROTOCOL.json') and s['trainer_sha256']==sha_file(HERE/'train_fold.py') and s['contrastive_sha256']==sha_file(HERE/'contrastive.py'), 'runtime provenance')
        require(s['base_revision']==protocol['model']['revision'] and s['base_model_id']==protocol['model']['id'], 'base model')
        require('A100' in s['gpu'] and s['bf16_supported'] and s['gpu_total_memory_bytes']>=79_000_000_000, 'frozen GPU/precision')
        require(s['runtime']['torch']=='2.2.1+cu121' and s['runtime']['cuda']=='12.1' and s['runtime']['transformers']=='4.38.1' and s['runtime']['tokenizers']=='0.15.2' and s['runtime']['numpy']=='1.26.4', 'pinned runtime versions')
        require(s['training_rows_used']==frozen['train_rows'] and s['fold_training_class_counts']==frozen['train_class_counts'] and s['class_weights']==frozen['class_weights'], 'training population')
        require(s['optimizer_steps']==(140 if f==1 else 145) and s['backward_passes']==(280 if f==1 else 285) and len(s['loss_by_epoch'])==5 and s['losses_all_finite'], 'fixed steps')
        require(all(math.isfinite(e[k]) for e in s['loss_by_epoch'] for k in ('mean_loss','mean_classification_loss','mean_contrastive_loss')), 'finite loss diagnostics')
        require(hashlib.sha256(returned['predictions_jsonl'].encode()).hexdigest()==s['heldout_predictions_sha256'], 'returned predictions hash')
        validate_rows(rows,human,folds,f)
        require(s['heldout_predictions']==len(rows), 'heldout count')
        reports[str(f)]={**s,'metrics':metric(rows,human),'predictions_per_class':dict(Counter(r['predicted_class'] for r in rows))}
        all_rows.extend(rows)
    validate_rows(all_rows,human,folds)
    order={sid:i for i,sid in enumerate(human)}
    all_rows.sort(key=lambda r:order[r['sample_id']])
    return all_rows,reports,bases,human


def main():
    rows,folds,bases,human=collect()
    require(protected_files()==json.loads((HERE/'private/PRESERVED_SHA256.json').read_text()), 'prior experiment files changed')
    verification=json.loads((HERE/'CHECKPOINT_VERIFICATION.json').read_text())
    require(verification['status']=='PASS', 'saved checkpoint verification')
    for f in range(1,6):
        require(verification['folds'][str(f)]['model_sha256']==folds[str(f)]['checkpoint_sha256'], 'persisted checkpoint hash')
    tests=json.loads((HERE/'FINAL_TESTS.json').read_text()); require(tests['status']=='PASS','final tests')
    overall=metric(rows,human)
    per_task={task:metric([r for r in rows if r['task']==task],human) for task in ('DM','MT','PG')}
    deltas={name:{k:overall[k]-base[k] for k in ('correct','accuracy','spearman')} for name,base in bases.items()}
    a=deltas['E11-A']
    conclusion=f"Compared with E11-A, contrastive learning {'improves' if a['accuracy']>0 else 'reduces' if a['accuracy']<0 else 'does not change'} accuracy and {'improves' if a['spearman']>0 else 'reduces' if a['spearman']<0 else 'does not change'} Spearman. Descriptive comparison only; no significance test performed."
    result={'status':'PASS','experiment':'E11-D','overall':overall,'per_task':per_task,'baselines':bases,'deltas':deltas,'folds':folds,'fits':5,'reruns':[], 'synthetic_rows':0,'conclusion':conclusion,'statistical_significance_tested':False,
            'probability_range':[min(r['p_H'] for r in rows),max(r['p_H'] for r in rows)],'predictions_per_class':dict(Counter(r['predicted_class'] for r in rows)),'oof_unique_ids':len(rows)}
    oof=HERE/'private/E11D_OOF_PREDICTIONS.jsonl'
    data=''.join(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n' for r in rows)
    if oof.exists(): require(oof.read_text(encoding='utf-8')==data,'OOF overwrite')
    else: oof.write_text(data,encoding='utf-8',newline='\n')
    save(HERE/'E11D_RESULTS.json',result)
    audit={'status':'PASS','fits':5,'failed_or_restarted_folds':[],'seed':42,'synthetic_examples':0,'official_test_access':False,'teacher_calls':0,'hyperparameter_search':False,'prior_experiments_unchanged':True,'protected_files_checked':len(json.loads((HERE/'private/PRESERVED_SHA256.json').read_text())),
           'loss_protocol':json.loads((HERE/'E11D_LOSS_PROTOCOL.json').read_text()),'runtime_by_fold':{f:r['runtime'] for f,r in folds.items()},'gpu_by_fold':{f:r['gpu'] for f,r in folds.items()},'training_seconds_sum':sum(r['elapsed_seconds'] for r in folds.values()),'training_seconds_by_fold':{f:r['elapsed_seconds'] for f,r in folds.items()},'checkpoint_verification':verification,'tests':tests,'all_losses_and_probabilities_finite':True,'oof_checks':'561 unique, complete, correct folds and labels, [0,1] probabilities, no class collapse','runtime_manifest_sha256':sha_file(HERE/'RUNTIME_MANIFEST.json')}
    save(HERE/'E11D_TRAINING_AUDIT.json',audit)
    md=['# E11-D results: PASS','',conclusion,'','| Experiment | Human | Synthetic | Contrastive | Correct/561 | Accuracy | Spearman |','|---|---|---|---|---:|---:|---:|']
    for name,h,s,c,m in [('E11-A','Yes','No','No',bases['E11-A']),('E11-C','Yes','Yes','No',bases['E11-C']),('E11-D','Yes','No','Yes',overall),('E10','feature-based reference','-','-',bases['E10'])]:
        md.append(f"| {name} | {h} | {s} | {c} | {m['correct']}/561 | {m['accuracy']:.16f} | {m['spearman']:.16f} |")
    md+=['','| D minus | Correct | Accuracy | Spearman |','|---|---:|---:|---:|']
    for name,m in deltas.items(): md.append(f"| {name} | {m['correct']:+d} | {m['accuracy']:+.16f} | {m['spearman']:+.16f} |")
    md+=['','| Task | Correct/total | Accuracy | Spearman |','|---|---:|---:|---:|']
    for name,m in per_task.items(): md.append(f"| {name} | {m['correct']}/{m['n']} | {m['accuracy']:.12f} | {m['spearman']:.12f} |")
    md+=['',f"Confusion matrix (rows gold 0/1, columns predicted 0/1): `{overall['confusion_matrix']}`.",'','| Fold | Train rows | Correct/heldout | Accuracy | Spearman | Seconds |','|---|---:|---:|---:|---:|---:|']
    for f,r in folds.items():
        m=r['metrics'];md.append(f"| {f} | {r['training_rows_used']} | {m['correct']}/{m['n']} | {m['accuracy']:.12f} | {m['spearman']:.12f} | {r['elapsed_seconds']:.3f} |")
    md+=['',f"Five fits; no reruns; seed 42. Probability range {result['probability_range']}; predicted classes {result['predictions_per_class']}. All OOF identity/finite checks PASS.",'','Loss: fold-weighted CE + 0.1 * mean((1-y)*(1-cos(a,b)) + y*max(0,cos(a,b))). Margin 0, no temperature. Final-layer mean pooling per sequence, excluding special/padding tokens; existing textual prefixes included. Representations share the original cross-encoder context. No projection head or extra encoder pass.','',f"GPUs: {', '.join(sorted({r['gpu'] for r in folds.values()}))}; summed fit runtime {audit['training_seconds_sum']:.3f} seconds. Includes checkpoint saving/hashing; excludes model setup and heldout inference. Concurrent folds, so summed time is not wall time or a billable GPU estimate.",'',f"Runtime: `{json.dumps(folds['1']['runtime'])}`.",'','Tests and full loss/epoch diagnostics are recorded in E11D_TRAINING_AUDIT.json and E11D_RESULTS.json. Prior A, C, teacher and E10 artifacts unchanged. No teacher calls, official-test access, tuning, commit, push or E11-E.','']
    (HERE/'E11D_RESULTS.md').write_text('\n'.join(md),encoding='utf-8')
    (HERE/'E11D_TRAINING_AUDIT.md').write_text('# E11-D training audit: PASS\n\n'+ '\n\n'.join(md[2:])+'\n\nAll five persisted checkpoints independently rehashed on the Modal volume. Runtime file manifest verified before fitting. Final tests passed; see FINAL_TESTS.json.\n',encoding='utf-8')
    paths=[p for p in HERE.iterdir() if p.is_file() and p.name not in ('E11D_MANIFEST.json','SHA256SUMS.txt')]
    paths += list((HERE/'private/returned').glob('*.json'))+[oof,HERE/'private/PRESERVED_SHA256.json']
    manifest={'status':'PASS','experiment':'E11-D','files_sha256':{str(p.relative_to(HERE)).replace('\\','/'):sha_file(p) for p in sorted(paths)},'checkpoints':{f:r['checkpoint_sha256'] for f,r in folds.items()}}
    save(HERE/'E11D_MANIFEST.json',manifest)
    public=['E11D_RESULTS.json','E11D_RESULTS.md','E11D_TRAINING_AUDIT.json','E11D_TRAINING_AUDIT.md','E11D_MANIFEST.json']
    (HERE/'SHA256SUMS.txt').write_text(''.join(sha_file(HERE/name)+'  '+name+'\n' for name in public),encoding='utf-8')
    print(json.dumps({'status':'PASS','overall':overall,'per_task':per_task,'deltas':deltas,'conclusion':conclusion},indent=2))

if __name__=='__main__': main()
