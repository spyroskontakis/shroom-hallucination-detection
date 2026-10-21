"""Independent saved-artifact verification and final report; no inference or RF fits."""
import json
import numpy as np
import pandas as pd
import v3_common as c
from evaluate_v3 import load_evaluation,metric,paired
from extract_features import assemble,validate_cache

def main():
    log=c.offline('report');c.versions()
    f,lock,baseline=load_evaluation();result=c.read_json(c.OUT/'evaluation/e6_v3_metrics.json')
    assert result['status']=='COMPLETED' and result['rf_fits']==5 and result['additional_baseline_fits']==0
    pred=pd.read_csv(c.OUT/'evaluation/e6_v3_oof_predictions.csv',float_precision='round_trip')
    assert c.sha(c.OUT/'evaluation/e6_v3_oof_predictions.csv')==result['oof_sha256']
    assert pred.canonical_id.tolist()==f.canonical_id.tolist() and np.array_equal(pred.fold_id,f.fold_id)
    f['E6-v3']=pred.prediction.to_numpy()
    rows=pd.read_csv(c.OUT/'evaluation/paired_row_diagnostics.csv',float_precision='round_trip')
    for key in ['canonical_id','fold_id','task','label_bin','p_hallucination','rag_evidence_available','E6-v2','E6-v3']:
        np.testing.assert_array_equal(rows[key],f[key])
    for name in ['E6-v2','E6-v3']:
        np.testing.assert_array_equal(rows[name+'_binary'],(f[name]>=.5).astype(int))
        np.testing.assert_array_equal(rows[name+'_correct'],(f[name]>=.5).astype(int)==f.label_bin)
    changes=np.select([~rows['E6-v2_correct']&rows['E6-v3_correct'],rows['E6-v2_correct']&~rows['E6-v3_correct']],
                      ['corrected','introduced_error'],default='unchanged_correctness')
    np.testing.assert_array_equal(rows.change,changes)
    d=result['diagnostics']
    for groups,stored in [([('all',f)],{'all':d['all_rows']}),(f.groupby('fold_id'),d['per_fold']),
                          (f.groupby('task'),d['per_task']),(f.groupby('rag_evidence_available'),d['by_evidence'])]:
        for key,g in groups:
            for name in ['E6-v2','E6-v3']:assert metric(g,name)==stored[str(key)][name]
    assert paired(f)==result['paired_vs_e6_v2']
    pairs=c.read_json(c.OUT/'inputs/hhem_pairs_label_free.json')
    assert pairs==[p for p in c.read_json(c.V2/'inputs/nli_pairs_label_free.json') if p['group'] in ['A','C']]
    all_scores=[];all_audits=[]
    config_sha=c.sha(c.OUT/'config/run_config.json')
    for begin in range(0,754,2):
        scores,audits=validate_cache(c.read_json(c.OUT/f'features/chunks/batch_{begin//2:04d}.json'),pairs[begin:begin+2],config_sha)
        all_scores+=scores;all_audits+=audits
    scores=pd.read_csv(c.OUT/'features/hhem_pair_scores.csv',float_precision='round_trip')
    audits=pd.read_csv(c.OUT/'features/truncation_audit.csv')
    np.testing.assert_array_equal(pd.DataFrame(all_scores)[scores.columns].to_numpy(),scores.to_numpy())
    # JSON uses sorted object keys; CSV column names select the canonical comparison order.
    np.testing.assert_array_equal(pd.DataFrame(all_audits)[audits.columns].to_numpy(),audits.to_numpy())
    base=pd.read_csv(c.V2/'features/e6_v2_34_features.csv',float_precision='round_trip')
    extra,full=assemble(base,pairs,all_scores)
    for name,df in [('e6_v3_added_2_features',extra),('e6_v3_36_features',full)]:
        saved=pd.read_csv(c.OUT/f'features/{name}.csv',float_precision='round_trip')
        np.testing.assert_array_equal(df.to_numpy(),saved.to_numpy())
    assert (full.loc[full.rag_evidence_available==0,c.NEW[1]]==0).sum()==368
    indexed=f.set_index('canonical_id')
    assert len(list((c.OUT/'evaluation').glob('fit_*_started.json')))==5
    assert len(list((c.OUT/'evaluation').glob('fit_*_completed.json')))==5
    for fold in range(1,6):
        start=c.read_json(c.OUT/f'evaluation/fit_{fold}_started.json');end=c.read_json(c.OUT/f'evaluation/fit_{fold}_completed.json')
        assert start=={k:v for k,v in end.items() if k!='completed_utc'}
        assert end['parameters']==lock['random_forest']
        assert end['train_ids']==f.loc[f.fold_id!=fold,'canonical_id'].tolist()
        assert end['validation_ids']==f.loc[f.fold_id==fold,'canonical_id'].tolist()
        assert set(end['train_ids']).isdisjoint(end['validation_ids'])
        for key,array in [('train_x_sha256',indexed.loc[end['train_ids'],lock['features']].to_numpy(float)),
                          ('train_y_sha256',indexed.loc[end['train_ids'],'p_hallucination'].to_numpy(float)),
                          ('validation_x_sha256',indexed.loc[end['validation_ids'],lock['features']].to_numpy(float))]:
            assert c.hashlib.sha256(array.tobytes()).hexdigest()==end[key]
    freeze=c.read_json(c.OUT/'config/feature_freeze.json')
    assert lock['frozen_utc']<freeze['started_utc']<freeze['completed_utc']
    assert freeze['completed_utc']<c.read_json(c.OUT/'evaluation/evaluation_started.json')['started_utc']
    assert freeze['truncation']['pairs']==754 and freeze['truncation']['truncated_pairs']==int(audits.truncated.sum())
    for group,g in audits.groupby('group'):
        assert freeze['truncation']['by_group'][group]=={'pairs':len(g),'truncated':int(g.truncated.sum()),'max_original_tokens':int(g.original_tokens.max())}
    protected=c.verify_inputs();c.verify_models();c.verify_freeze()
    network_logs=list((c.OUT/'config').glob('network_attempts_*.jsonl'))
    assert len(network_logs)>=5 and all(p.stat().st_size==0 for p in network_logs)
    audit={'status':'PASS','verified_utc':c.now(),'protected_unchanged':len(protected['protected_sha256']),
           'rf_fits':5,'additional_baseline_fits':0,'prediction_rows':561,'old_features_unchanged':34,'new_features':2,
           'hhem_pairs':754,'verified_batches':377,'cache_reassembly_exact':True,'pair_text_reuse_exact':True,
           'paired_statistics_recomputed':True,'all_subgroup_metrics_recomputed':True,
           'train_target_validation_array_hashes_verified':15,'inference_evaluation_network_attempts':0,
           'authorized_model_download':True,'no_router_or_rf_tuning':True}
    c.write_json(c.OUT/'config/final_integrity.json',audit)
    with (c.OUT/'E6_V3_RESULTS.md').open('x',encoding='utf-8',newline='\n') as out:out.write(render(result,freeze,lock,audit))
    c.write_json(c.OUT/'config/completion_manifest.json',{'status':'COMPLETED','completed_utc':c.now(),'evaluations':1,'rf_fits':5,
                 'files':{p.relative_to(c.OUT).as_posix():c.sha(p) for p in sorted(c.OUT.rglob('*')) if p.is_file()}})
    print({'report':'E6_V3_RESULTS.md','integrity':audit},flush=True)

def render(result,freeze,lock,audit):
    d=result['diagnostics'];p=result['paired_vs_e6_v2'];b=p['bootstrap'];lo,hi=b['percentile_95_ci_pp']
    def rho(m):return 'undefined' if m['spearman'] is None else f"{m['spearman']:.10f}"
    lines=['# E6-v3 — E6-v2 plus Vectara HHEM-1.0: results','',
           '**COMPLETED. Exploratory development-only on a reused development set.** One predetermined 36-feature configuration, '
           'one five-fold OOF evaluation, exactly five RF fits and zero baseline fits. No post-score change. '
           'The conclusion concerns the entire two-feature HHEM block.','',
           '| Version | Features | Correct/N | Accuracy | Spearman |','|---|---:|---:|---:|---:|']
    for name,count in [('E6-v2',34),('E6-v3',36)]:
        m=d['all_rows'][name];lines.append(f"| {name} | {count} | {m['correct']}/{m['n']} | {m['accuracy']:.10f} | {rho(m)} |")
    lines+=['',f"Accuracy difference E6-v3 − E6-v2: **{b['accuracy_difference_pp']:+.6f} percentage points**, net **{p['net_correct']:+d}/561** correct.",
            '', '## Fold, task and evidence results','',
            '| Group | N | E6-v2 correct | E6-v3 correct | E6-v2 accuracy | E6-v3 accuracy | E6-v2 Spearman | E6-v3 Spearman |',
            '|---|---:|---:|---:|---:|---:|---:|---:|']
    groups=[(f'Fold {k}',g) for k,g in d['per_fold'].items()]+list(d['per_task'].items())
    groups += [('With definition',d['by_evidence']['1']),('Without definition',d['by_evidence']['0'])]
    for name,g in groups:
        a,z=g['E6-v2'],g['E6-v3']
        lines.append(f"| {name} | {z['n']} | {a['correct']} | {z['correct']} | {a['accuracy']:.10f} | {z['accuracy']:.10f} | {rho(a)} | {rho(z)} |")
    lines+=['','## Paired comparison','',
            f"**{p['corrected']} corrections**, **{p['introduced_errors']} new errors**; both correct {p['both_correct']}, both wrong {p['both_wrong']}. "
            f"Exact two-sided McNemar **p={p['mcnemar_exact_two_sided_p']:.10f}**.",'',
            f"Paired-bootstrap 95% accuracy-difference interval: **[{lo:+.6f}, {hi:+.6f}] percentage points** "
            f"(raw difference {b['accuracy_difference']:+.10f}; raw interval {b['percentile_95_ci']}).",'',
            'Same E6-v2/Module 4 procedure: binomtest(corrected, discordant count, .5), two-sided; p=1 if no discordance. '
            '10,000 paired row resamples of size 561, numpy.default_rng(42), numpy.quantile at .025/.975. '
            'Spearman uses p_hallucination versus predictions rounded to 12 decimals; accuracy uses unrounded predictions >=.5. '
            'Corrected/new-error IDs are in evaluation/e6_v3_metrics.json, with all 561 row details in paired_row_diagnostics.csv. '
            'Subgroups are descriptive; bootstrap conditions on fixed OOF predictions and does not refit models.','',
            '## Pinned model and score semantics','',
            f'**{c.MODEL_ID}@{c.REVISION}**, historical hhem-1.0-open. Model and tokenizer were loaded from the same local revision mirror, '
            'with local_files_only=True and trust_remote_code=False. Runtime architecture DebertaV2ForSequenceClassification, '
            'one output logit. torch.sigmoid(raw logit) is applied exactly once, matching the historical Transformers example; '
            'higher means supported by the premise. No single-logit softmax, score inversion or second sigmoid.', '',
            f'The [pinned model card](https://huggingface.co/{c.MODEL_ID}/blob/{c.REVISION}/README.md) declares '
            'MultiNLI, SNLI, FEVER, Vitamin C and PAWS training data, using microsoft/deberta-v3-base. '
            'These are author claims, not an independent contamination audit. The historical AutoModel example and downloaded '
            'card were checked directly. provenance/acquisition.json records exact revision URLs, bytes and SHA-256 for eight '
            'required files. The PyTorch weight hash also matches the Hub x-linked-etag; no alternative model revision was used.', '',
            'The model stays eval(), requires_grad_(False) and inference_mode(); no fine-tuning. '
            'The four artificial-text smoke pairs and seven pre-bulk contracts passed before protocol freeze. '
            'Contracts cover exact A/C projection and label rejection, missing-definition zeros, corruption/config/text cache rejection, '
            'single-sigmoid semantics, paired tokenization/masks/truncation, folds, metrics and source syntax. No RF fits occur in tests.', '',
            '## Features and extraction','',
            'All 34 saved E6-v2 columns are retained with identical values and order after round-trip CSV reading. '
            'Exactly two columns are appended:', '',
            '| Feature | Premise | Hypothesis | Inferred pairs |','|---|---|---|---:|',
            '| hhem_ref_hyp_consistency | saved A reference (tgt DM/MT, src PG) | hyp | 561 |',
            '| hhem_definition_hyp_consistency | saved C selected definition | hyp | 193 |','',
            'All 754 pairs reuse the exact saved E6-v2 strings. No B/reverse pairs, new retrieval, reranking or definition replacement. '
            'The 368 absent-definition rows receive exact zero in the second feature, with rag_evidence_available unchanged. '
            'Inputs exclude labels, target probabilities and predictions. Label joining occurs only after the feature matrix freeze.', '',
            'CPU float32, batch=2, seeds42, torch threads4/4, eager attention, no autocast. Fast tokenizer; separate premise/hypothesis, '
            'max_length512, longest_first, per-batch padding and attention_mask. Raw logits and scores have no intentional rounding. '
            'Original and encoded lengths, side-specific removed tokens, padded lengths and IDs are in features/truncation_audit.csv. '
            'The smoke warning for an untruncated long sequence came from length auditing; actual model inputs are at most512 tokens.', '',
            '| Group | Pairs | Truncated | Maximum original tokens |','|---|---:|---:|---:|']
    for g,a in freeze['truncation']['by_group'].items():lines.append(f"| {g} | {a['pairs']} | {a['truncated']} | {a['max_original_tokens']} |")
    lines += ['',f"Real truncated pairs: **{freeze['truncation']['truncated_pairs']}**, affected canonical rows **{freeze['truncation']['truncated_canonical_rows']}**. "
              f"Bulk extraction elapsed **{freeze['duration_seconds']:.3f}s** ({freeze['duration_seconds']/60:.3f}min), "
              f"summed tokenization/inference batch time **{freeze['summed_batch_inference_seconds']:.3f}s**. "
              'Elapsed includes lazy model load, outputs and final integrity checks after initial verification; excludes download and smoke. '
              f"This extraction invocation inferred {freeze['pairs_inferred_this_execution']} pairs and reused {freeze['pairs_reused_from_cache']} cached pairs.", '',
              '377 atomic batch caches contain configuration/text hashes, ordered pair IDs, payload hashes, raw logits, scores, '
              'truncation and durations. Every cache was revalidated and reconstructed into the final matrix without inference. '
              'Resumption verifies completed batches and computes only missing batches; session-specific logs support technical interruption.', '',
              '## Fixed evaluation and integrity','',
              'Same 561 canonical IDs and locked folds. Baseline saved E6-v2 predictions and row diagnostics match per ID/fold '
              'and reproduce 473/561, accuracy 0.8431372549019608, Spearman 0.7775058304756869. No baseline retraining. '
              'RandomForestRegressor uses all18 explicitly frozen E6-v2 parameters (500 trees, seed42, min_samples_leaf1, '
              'max_features1.0); full dictionary below. Each of five fits uses only its outer training rows. '
              'Target p_hallucination, clip[0,1], threshold>=.5. No E7 router or E8 tuning.', '',
              '```json',json.dumps(lock['random_forest'],indent=2,sort_keys=True),'```','',
              f"Protocol/source/config freeze: {lock['frozen_utc']}. Extraction start: {freeze['started_utc']}. "
              f"Matrix freeze: {freeze['completed_utc']}. Evaluation complete: {result['completed_utc']}.", '',
              f"Final integrity **PASS**: {audit['protected_unchanged']} previous files unchanged; all36 feature columns reassembled exactly; "
              '754 cache scores and truncation records checked; all metrics and paired statistics recomputed; five train/validation '
              'partitions and15 array hashes verified. Model, input, code and protocol hashes match. Network logs for '
              'smoke/contracts/extraction/evaluation/report are empty; only the authorized pinned download used network.', '',
              'Runtime versions (same accepted E6-v2 environment):','',
              '```json',json.dumps(lock['runtime'],indent=2,sort_keys=True),'```','',
              '## Interpretation','',
              ('The paired interval includes zero; the measured accuracy difference is compatible with no difference on these fixed OOF predictions.'
               if lo<=0<=hi else 'The paired interval excludes zero on these fixed development OOF predictions; this does not establish independent-test generalization.'),'',
              '**Exploratory development-only on a reused development set.** The result concerns adding the entire HHEM block, '
              'without attributing effects to either individual feature. This is inspired by combining evaluators in Halu-NLP/MetaCheckGPT, '
              'not a reproduction of the full system. Existing reference-assisted features and the historical provenance limitations remain. '
              'The selected definitions descend from the frozen Module4 reconstruction; no historical full ranking file exists for direct '
              'comparison, and agreement of aggregate E5 features alone does not prove the whole historical order. '
              'There is no independent-test or selection-adjusted statistical claim. No official-test access, paid API, remote inference, '
              'synthetic-data edits, commit/push/tag or further experiment occurred.', '',
              '## Artifacts','',
              '- E6_V3_PROTOCOL.md; config/run_config.json: frozen protocol, all choices and code/input manifest.',
              '- provenance/ and model/: pinned sources, card, weights/tokenizer and hashes.',
              '- inputs/: exact label-free pairs, definition/reference mapping and locked folds.',
              '- features/e6_v3_added_2_features.csv; features/e6_v3_36_features.csv; hhem_pair_scores.csv; truncation_audit.csv; chunks/.',
              '- evaluation/e6_v3_oof_predictions.csv; e6_v3_metrics.json; paired_row_diagnostics.csv; five fit start/completion records.',
              '- scripts/; tests/; config/contracts.json; config/final_integrity.json; config/completion_manifest.json.','']
    return '\n'.join(lines)

if __name__=='__main__':main()
