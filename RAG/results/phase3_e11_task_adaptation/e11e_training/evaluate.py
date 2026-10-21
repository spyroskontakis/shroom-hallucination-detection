"""One fixed E11-E evaluation with the original E11-A metric function."""
import math
from collections import Counter
from e11e_common import *


def validate_stage(s,f,stage,spec):
    meta=spec['folds'][str(f)];train=spec[f'stage{stage}']
    n=meta['synthetic_rows'] if stage==1 else meta['human_train_rows']
    require(s['status']=='PASS' and s['fold_id']==f and s['stage']==stage and s['run_id']==f'e11e-fold-{f:03d}-stage-{stage}','fold/stage identity')
    require(s['protocol_sha256']==spec['protocol_sha256'] and s['trainer_sha256']==sha_file(HERE/'train_stages.py') and s['contrastive_sha256']==sha_file(HERE/'contrastive.py'),'runtime provenance')
    require(s['base_model_id']==spec['model']['id'] and s['base_revision']==spec['model']['revision'],'base model')
    require(s['training_rows_used']==n and s['class_weights']==train['class_weight_values_by_fold'][str(f)],'stage rows/weights')
    training=read_jsonl(HERE/f'private/fold_{f}'/('synthetic.jsonl' if stage==1 else 'train.jsonl'))
    require(s['fold_training_class_counts']==dict(Counter(str(r['label']) for r in training)),'training class counts')
    batches=math.ceil(n/train['train_batch_size']);epochs=train['epochs']
    require(s['optimizer_steps']==epochs*math.ceil(batches/train['gradient_accumulation_steps']) and s['backward_passes']==epochs*batches and len(s['loss_by_epoch'])==epochs,'fixed step counts')
    require(s['losses_all_finite'] and all(math.isfinite(e[k]) for e in s['loss_by_epoch'] for k in ('mean_loss','mean_classification_loss','mean_contrastive_loss')),'finite losses')
    for e in s['loss_by_epoch']:
        require(abs(e['mean_loss']-(e['mean_classification_loss']+.1*e['mean_contrastive_loss']))<1e-6,'loss formula diagnostic')
    require('A100' in s['gpu'] and s['bf16_supported'] and s['gpu_total_memory_bytes']>=79_000_000_000,'GPU precision')
    require(s['runtime']['torch']=='2.2.1+cu121' and s['runtime']['cuda']=='12.1' and s['runtime']['packages']=={'transformers':'4.38.1','tokenizers':'0.15.2','numpy':'1.26.4','safetensors':'0.4.5'},'runtime versions')
    require(s['e11e_score_produced']==(stage==2),'stage scoring rule')


def collect():
    spec=read(HERE/'E11E_TRAINING_PROTOCOL.json')
    require(digest(encoded({k:v for k,v in spec.items() if k!='protocol_sha256'}))==spec['protocol_sha256'],'protocol content hash')
    for name,sha in read(HERE/'RUNTIME_MANIFEST.json').items():require(sha_file(HERE/name)==sha,'frozen runtime')
    for f,meta in spec['folds'].items():
        for name,sha in meta['files_sha256'].items():require(sha_file(HERE/f'private/fold_{f}'/name)==sha,'prepared file drift')
    bases,human,assignments=baselines();rows=[];reports={}
    require(len(list((HERE/'private/returned').glob('fold_*.json')))==5,'exactly five fold returns')
    for f in range(1,6):
        ret=read(HERE/f'private/returned/fold_{f}.json')
        require(ret['fold_id']==f and len(ret['stages'])==2,'return identity')
        s1,s2=ret['stages']
        validate_stage(s1,f,1,spec);validate_stage(s2,f,2,spec)
        require(s1['initial_model_weights_sha256']==spec['model']['local_assets_sha256']['model.safetensors'],'Stage-1 initial weights')
        require(s2['initial_model_weights_sha256']==s1['checkpoint_sha256'],'Stage-2 must start from own Stage-1')
        require(digest(ret['predictions_jsonl'].encode())==s2['heldout_predictions_sha256'],'prediction hash')
        foldrows=[json.loads(line) for line in ret['predictions_jsonl'].splitlines()]
        validate_rows(foldrows,human,assignments,f)
        require(len(foldrows)==s2['heldout_predictions']==spec['folds'][str(f)]['heldout_rows'],'heldout row count')
        reports[str(f)]={'stages':ret['stages'],'metrics':metric(foldrows,human),
                         'probability_range':[min(r['p_H'] for r in foldrows),max(r['p_H'] for r in foldrows)],
                         'predictions_per_class':dict(Counter(str(r['predicted_class']) for r in foldrows))}
        rows.extend(foldrows)
    validate_rows(rows,human,assignments)
    ordering={sid:i for i,sid in enumerate(human)};rows.sort(key=lambda r:ordering[r['sample_id']])
    return rows,reports,bases,human


def difference(new,old):return {k:new[k]-old[k] for k in ('correct','accuracy','spearman')}


def interpretations(metrics):
    pairs=[('synthetic_human_only','E11-C','E11-A'),('contrastive_human_only','E11-D','E11-A'),('contrastive_with_synthetic','E11-E','E11-C'),('synthetic_with_contrastive','E11-E','E11-D')]
    result={}
    for name,new,old in pairs:
        d=difference(metrics[new],metrics[old])
        result[name]={'comparison':new+' minus '+old,'deltas':d,'accuracy_improved':d['accuracy']>0,'spearman_improved':d['spearman']>0}
    variants=['E11-A','E11-C','E11-D','E11-E']
    for key in ('accuracy','spearman'):
        best=max(metrics[name][key] for name in variants)
        result['best_e11_'+key]=[name for name in variants if metrics[name][key]==best]
        result['e11_exceeds_E10_'+key]=[name for name in variants if metrics[name][key]>metrics['E10'][key]]
    result['statistical_significance_tested']=False
    return result


def main():
    rows,folds,bases,human=collect()
    require(protected_files()==read(HERE/'private/PRESERVED_SHA256.json'),'prior experiment files changed')
    checkpoints=read(HERE/'CHECKPOINT_VERIFICATION.json');require(checkpoints['status']=='PASS','checkpoint verification')
    for f in range(1,6):
        for stage in (1,2):
            require(checkpoints['stages'][f'{f}:{stage}']['summary']==folds[str(f)]['stages'][stage-1],'persisted checkpoint provenance')
    tests=read(HERE/'FINAL_TESTS.json');require(tests['status']=='PASS' and tests['skipped']==0,'final tests')
    spec=read(HERE/'E11E_TRAINING_PROTOCOL.json');pre=read(HERE/'E11E_PRETRAINING_AUDIT.json')
    overall=metric(rows,human);metrics={**bases,'E11-E':overall}
    tasks={task:metric([r for r in rows if r['task']==task],human) for task in ('DM','MT','PG')}
    deltas={name:difference(overall,base) for name,base in bases.items()}
    interpretation=interpretations(metrics)
    result={'status':'PASS','experiment':'E11-E','protocol_sha256':spec['protocol_sha256'],'overall':overall,'per_task':tasks,'baselines':bases,'deltas':deltas,'interpretation':interpretation,
            'folds':folds,'oof_rows':561,'oof_unique_ids':561,'probability_range':[min(r['p_H'] for r in rows),max(r['p_H'] for r in rows)],
            'predictions_per_class':dict(Counter(str(r['predicted_class']) for r in rows)),
            'synthetic_rows_by_fold':pre['synthetic_rows_by_fold'],'validation_overlap_exclusions':pre['validation_overlap_exclusions'],
            'stage1_fits':5,'stage2_fits':5,'total_fits':10,'failed_or_restarted_folds':[],'seed':42,'statistical_significance_tested':False}
    oof=HERE/'private/E11E_OOF_PREDICTIONS.jsonl'
    write_once(oof,''.join(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n' for r in rows).encode())
    save(HERE/'E11E_RESULTS.json',result)
    stages={f'{f}:{s["stage"]}':s for f,r in folds.items() for s in r['stages']}
    timing={'stage1_seconds':sum(s['elapsed_seconds'] for s in stages.values() if s['stage']==1),
            'stage2_seconds':sum(s['elapsed_seconds'] for s in stages.values() if s['stage']==2),
            'summed_fit_seconds':sum(s['elapsed_seconds'] for s in stages.values()),
            'definition':'Per-stage time from training loop through checkpoint saving and hashing; excludes model setup and heldout inference. Concurrent sums are not wall time or billing duration.'}
    audit={'status':'PASS','stage1_fits':5,'stage2_fits':5,'total_fits':10,'failed_or_restarted_folds':[],
           'teacher_calls':0,'official_test_access':False,'hyperparameter_search':False,'prior_artifacts_unchanged':True,
           'protected_files_checked':len(read(HERE/'private/PRESERVED_SHA256.json')),'training_protocol':spec,
           'synthetic_pool_provenance':{k:pre[k] for k in ('teacher_model','synthetic_pool','synthetic_export_sha256','teacher_protocol_sha256','uncertain_excluded','Azure_rescue_excluded','duplicate_input_exclusions','duplicate_reasons','conflicting_groups','validation_overlap_exclusions','synthetic_rows_by_fold','leakage_limit')},
           'runtime_by_stage':{k:s['runtime'] for k,s in stages.items()},'gpu_by_stage':{k:s['gpu'] for k,s in stages.items()},'runtime':timing,
           'tests':tests,'all_losses_and_probabilities_finite':True,'oof_checks':'561 unique complete IDs; exact tasks, labels and folds; finite [0,1] probabilities; no fold collapsed',
           'checkpoints':checkpoints,'runtime_manifest_sha256':sha_file(HERE/'RUNTIME_MANIFEST.json'),
           'evaluator_sha256':sha_file(E11/'e11a_results/assemble_e11a_results.py')}
    save(HERE/'E11E_TRAINING_AUDIT.json',audit)
    md=['# E11-E results: PASS','','Single fixed ablation. Exact E11-C two-stage data/settings plus the unchanged E11-D contrastive objective in both stages. No tuning or additional configuration.','',
        '| Experiment | Human | Synthetic | Contrastive | Correct/561 | Accuracy | Spearman |','|---|---|---|---|---:|---:|---:|']
    for name,h,sy,co in [('E11-A','Yes','No','No'),('E11-C','Yes','Yes','No'),('E11-D','Yes','No','Yes'),('E11-E','Yes','Yes','Yes'),('E10','feature-based reference','-','-')]:
        m=metrics[name];md.append(f"| {name} | {h} | {sy} | {co} | {m['correct']}/561 | {m['accuracy']:.16f} | {m['spearman']:.16f} |")
    md+=['','| E11-E minus | Correct | Accuracy | Spearman |','|---|---:|---:|---:|']
    for name,m in deltas.items():md.append(f"| {name} | {m['correct']:+d} | {m['accuracy']:+.16f} | {m['spearman']:+.16f} |")
    md+=['','| Task | Correct/total | Accuracy | Spearman |','|---|---:|---:|---:|']
    for name,m in tasks.items():md.append(f"| {name} | {m['correct']}/{m['n']} | {m['accuracy']:.12f} | {m['spearman']:.12f} |")
    md+=['',f"Confusion matrix, gold rows/predicted columns ordered 0/1: `{overall['confusion_matrix']}`.",'',
         '| Fold | Synthetic | Human | Correct/heldout | Accuracy | Spearman | Stage 1 s | Stage 2 s |','|---|---:|---:|---:|---:|---:|---:|---:|']
    for f,r in folds.items():
        m=r['metrics'];s1,s2=r['stages'];md.append(f"| {f} | {s1['training_rows_used']} | {s2['training_rows_used']} | {m['correct']}/{m['n']} | {m['accuracy']:.12f} | {m['spearman']:.12f} | {s1['elapsed_seconds']:.3f} | {s2['elapsed_seconds']:.3f} |")
    md+=['',f"Probability range: {result['probability_range']}; predicted class counts: {result['predictions_per_class']}. 561 unique complete IDs; no NaN/Inf, missing IDs, duplicates or fold class collapse.",'','## Descriptive interpretation','']
    for key in ('synthetic_human_only','contrastive_human_only','contrastive_with_synthetic','synthetic_with_contrastive'):
        item=interpretation[key];d=item['deltas']
        accuracy_word='improved' if d['accuracy']>0 else 'decreased' if d['accuracy']<0 else 'unchanged'
        ranking_word='improved' if d['spearman']>0 else 'decreased' if d['spearman']<0 else 'unchanged'
        md.append(f"- {item['comparison']}: accuracy {accuracy_word} ({d['accuracy']:+.12f}, {d['correct']:+d} correct); Spearman {ranking_word} ({d['spearman']:+.12f}).")
    md+=['',f"Highest E11 accuracy: {', '.join(interpretation['best_e11_accuracy'])}. Highest E11 Spearman: {', '.join(interpretation['best_e11_spearman'])}.",
         f"E11 variants exceeding E10 accuracy: {interpretation['e11_exceeds_E10_accuracy']}; Spearman: {interpretation['e11_exceeds_E10_spearman']}.",
         'These are descriptive development comparisons. No statistical significance test performed.','',
         'Loss in BOTH stages: weighted CE + 0.1 × mean[(1−y)(1−cos(a,b)) + y·max(0,cos(a,b))]. y=1 denotes hallucination; margin 0, no temperature. Byte-identical E11-D implementation: final-layer mean pooling by fast-tokenizer sequence membership, special/padding tokens excluded, textual prefixes retained, cosine L2 normalization with eps=1e-8. Both representations share the original cross-encoder context. No projection head or additional forward pass.','',
         f"Exactly ten fits (five Stage 1, five Stage 2), no reruns. Seed 42. Summed recorded fit runtime {timing['summed_fit_seconds']:.3f} s; Stage 1 {timing['stage1_seconds']:.3f} s; Stage 2 {timing['stage2_seconds']:.3f} s. {timing['definition']}",
         f"GPUs: {', '.join(sorted({s['gpu'] for s in stages.values()}))}. Runtime: `{json.dumps(stages['1:1']['runtime'])}`.",'',
         f"Final tests: {tests['total_tests']} passed, zero skips. All ten persisted checkpoint hashes and five predictions independently verified. Stage-2 initial hashes match their own fold's Stage-1 checkpoints. {audit['protected_files_checked']} protected prior files unchanged.",
         'No teacher calls, official-test access, threshold/hyperparameter tuning, commit, push or E11-F.','']
    write_once(HERE/'E11E_RESULTS.md','\n'.join(md).encode())
    audit_md=['# E11-E training audit: PASS','',f"Model: {spec['model']['id']}, revision `{spec['model']['revision']}`. Pinned fast tokenizer; longest-first truncation, maximum 512 tokens. Locked fold hash `{spec['folds_sha256']}`.",'',
              'Data and stage settings are identical to E11-C. Stage 1 uses one epoch of fold-specific synthetic data; Stage 2 starts from its own Stage-1 weights, resets AdamW and scheduler, and uses five human epochs. Both use seed 42, LR 1e-5, weight decay .01, batch 8, accumulation 2, BF16, gradient clipping 1, linear warmup (.1) and decay. Class weights use only each stage/fold training labels. Final checkpoints only; threshold .5.','',
              'Exactly 11,887 definitive gpt-5.6-sol labels before identical-input and validation-overlap exclusions. All 109 uncertain outcomes and four Azure alternate-model judgments remain excluded. The original 82 duplicate/conflicting exclusions and fold-specific overlap rules were replayed without changes.','',
              f"Contrastive implementation SHA256: `{sha_file(HERE/'contrastive.py')}`. Protocol content SHA256: `{spec['protocol_sha256']}`. Original evaluator SHA256: `{audit['evaluator_sha256']}`.",'',
              'All loss components, per-stage identities/runtime, checkpoint chains, file hashes, exclusion counts and tests are recorded in the JSON audit and results. Row-level outputs remain private/gitignored.','']
    write_once(HERE/'E11E_TRAINING_AUDIT.md','\n'.join(audit_md+md[2:]).encode())
    paths=[p for p in HERE.iterdir() if p.is_file() and p.name not in ('E11E_MANIFEST.json','SHA256SUMS.txt')]
    paths+=list((HERE/'private/returned').glob('*.json'))+[oof,HERE/'private/PRESERVED_SHA256.json']
    for f in range(1,6):paths+=list((HERE/f'private/fold_{f}').glob('*.jsonl'))
    save(HERE/'E11E_MANIFEST.json',{'status':'PASS','experiment':'E11-E','protocol_sha256':spec['protocol_sha256'],
         'files_sha256':{p.relative_to(HERE).as_posix():sha_file(p) for p in sorted(paths)},
         'checkpoints':{k:s['checkpoint_sha256'] for k,s in stages.items()}})
    names=['E11E_RESULTS.json','E11E_RESULTS.md','E11E_TRAINING_AUDIT.json','E11E_TRAINING_AUDIT.md','E11E_MANIFEST.json','E11E_TRAINING_PROTOCOL.json']
    write_once(HERE/'SHA256SUMS.txt',''.join(sha_file(HERE/n)+'  '+n+'\n' for n in names).encode())
    print(json.dumps({'status':'PASS','overall':overall,'tasks':tasks,'deltas':deltas,'interpretation':interpretation,'runtime':timing},indent=2))


if __name__=='__main__':main()
