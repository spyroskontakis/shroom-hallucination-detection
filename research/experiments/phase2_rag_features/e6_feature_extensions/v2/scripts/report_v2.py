"""Verify saved E6-v2 artifacts and report; no model loading or training."""
if "_H2_CTX" not in globals():
    raise RuntimeError("Historical source: use the pinned cross-experiment context; direct execution/import is disabled")
import json
import numpy as np
import pandas as pd
import v2_common as c
from evaluate_v2 import load_evaluation,metric,paired
from extract_features import assemble


def main():
    log=c.offline('report')
    f,lock,baseline=load_evaluation()
    result=c.read_json(c.OUT/'evaluation/e6_v2_metrics.json')
    assert result['status']=='COMPLETED'
    pred=pd.read_csv(c.OUT/'evaluation/e6_v2_oof_predictions.csv',float_precision='round_trip')
    assert c.sha(c.OUT/'evaluation/e6_v2_oof_predictions.csv')==result['oof_sha256']
    assert pred.canonical_id.tolist()==f.canonical_id.tolist() and np.array_equal(pred.fold_id,f.fold_id)
    f['E6-v2']=pred.prediction.to_numpy()
    saved=pd.read_csv(c.OUT/'evaluation/paired_row_diagnostics.csv',float_precision='round_trip')
    for key in ['canonical_id','fold_id','task','label_bin','p_hallucination','rag_evidence_available','E6-v1','E6-v2']:
        assert np.array_equal(saved[key],f[key]),key
    d=result['diagnostics']
    for groups,stored in [([('all',f)],{'all':d['all_rows']}),(f.groupby('fold_id'),d['per_fold']),
                          (f.groupby('task'),d['per_task']),(f.groupby('rag_evidence_available'),d['by_evidence'])]:
        for key,g in groups:
            for name in ['E6-v1','E6-v2']:assert metric(g,name)==stored[str(key)][name]
    assert paired(f)==result['paired_vs_e6_v1']
    pairs=c.read_json(c.OUT/'inputs/nli_pairs_label_free.json')
    scores=pd.read_csv(c.OUT/'features/nli2_pair_scores.csv',float_precision='round_trip')
    base=pd.read_csv(c.V1/'features/e6_25_features.csv',float_precision='round_trip')
    extra,full=assemble(base,pairs,scores.to_dict('records'))
    loaded=pd.read_csv(c.OUT/'features/e6_v2_34_features.csv',float_precision='round_trip')
    np.testing.assert_array_equal(full.to_numpy(),loaded.to_numpy())
    trunc=pd.read_csv(c.OUT/'features/truncation_audit.csv')
    assert trunc.pair_id.tolist()==scores.pair_id.tolist()==[p['pair_id'] for p in pairs]
    assert (trunc.original_tokens-trunc.encoded_tokens==trunc.premise_tokens_removed+trunc.hypothesis_tokens_removed).all()
    assert np.array_equal(trunc.truncated.to_numpy(),(trunc.original_tokens>512).to_numpy())
    assert np.array_equal(trunc.encoded_tokens.to_numpy(),np.minimum(trunc.original_tokens,512).to_numpy())
    indexed=f.set_index('canonical_id');starts=[];ends=[]
    for fold in range(1,6):
        start=c.read_json(c.OUT/f'evaluation/fit_{fold}_started.json')
        end=c.read_json(c.OUT/f'evaluation/fit_{fold}_completed.json')
        assert start=={k:v for k,v in end.items() if k!='completed_utc'}
        assert end['parameters']==lock['random_forest']
        assert end['train_ids']==f.loc[f.fold_id!=fold,'canonical_id'].tolist()
        assert end['validation_ids']==f.loc[f.fold_id==fold,'canonical_id'].tolist()
        for key,array in [('train_x_sha256',indexed.loc[end['train_ids'],lock['features']].to_numpy(float)),
                          ('train_y_sha256',indexed.loc[end['train_ids'],'p_hallucination'].to_numpy(float)),
                          ('validation_x_sha256',indexed.loc[end['validation_ids'],lock['features']].to_numpy(float))]:
            assert c.hashlib.sha256(array.tobytes()).hexdigest()==end[key]
        starts.append(start);ends.append(end)
    freeze=c.read_json(c.OUT/'config/feature_freeze.json')
    assert freeze['completed_utc']<c.read_json(c.OUT/'evaluation/evaluation_started.json')['started_utc']
    assert lock['frozen_utc']<freeze['started_utc']
    protected=c.verify_inputs();c.verify_models();c.verify_freeze()
    network_logs=list((c.OUT/'config').glob('network_attempts_*.jsonl'))
    assert len(network_logs)==4 and all(p.stat().st_size==0 for p in network_logs)
    audit={'status':'PASS','verified_utc':c.now(),'protected_unchanged':len(protected['protected_sha256']),
           'rf_fits':len(ends),'additional_baseline_fits':0,'prediction_rows':561,'old_features_unchanged':25,
           'new_features':9,'nli_pairs':1315,'truncation_audit_pairs':1315,'pair_scores_reassembled':True,
           'paired_statistics_recomputed':True,'train_target_validation_array_hashes_verified':15,
           'inference_evaluation_network_attempts':0,'authorized_model_download':True,
           'no_router_or_rf_tuning':True}
    c.write_json(c.OUT/'config/final_integrity.json',audit)
    with (c.OUT/'E6_V2_RESULTS.md').open('x',encoding='utf-8',newline='\n') as out:
        out.write(render(result,freeze,lock,audit,baseline))
    c.write_json(c.OUT/'config/completion_manifest.json',{'status':'COMPLETED','completed_utc':c.now(),
                 'evaluations':1,'rf_fits':5,'files':{p.relative_to(c.OUT).as_posix():c.sha(p)
                    for p in sorted(c.OUT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}})
    print({'report':'E6_V2_RESULTS.md','final_integrity':audit},flush=True)


def render(result,freeze,lock,audit,baseline):
    d=result['diagnostics'];paired_result=result['paired_vs_e6_v1'];boot=paired_result['bootstrap']
    def rho(m):return 'undefined' if m['spearman'] is None else f"{m['spearman']:.10f}"
    lines=['# E6-v2 — second NLI evaluator: actual results','',
           '**COMPLETED — EXPLORATORY DEVELOPMENT-ONLY on a reused development pool.** '
           'One frozen 34-feature configuration, one five-fold OOF suite, five Random Forest fits. '
           'No post-score changes or tuning. The conclusion concerns the complete nine-feature NLI block.','',
           '## Overall OOF result','',
           '| Version | Features | Correct / N | Accuracy | Spearman |','|---|---:|---:|---:|---:|']
    for name,count in [('E6-v1',25),('E6-v2',34)]:
        m=d['all_rows'][name]
        lines.append(f"| {name} | {count} | {m['correct']}/{m['n']} | {m['accuracy']:.10f} ({m['accuracy']*100:.4f}%) | {rho(m)} |")
    net=paired_result['net_correct']
    direction='improvement' if net>0 else ('decrease' if net<0 else 'no change')
    lines+=['',f"The observed accuracy {direction} is {boot['accuracy_difference_pp']:+.6f} percentage points, net {net:+d}/561 correct predictions.",
            '', '## Fold, task and evidence results','',
            '| Group | N | E6-v1 correct | E6-v2 correct | E6-v1 accuracy | E6-v2 accuracy | E6-v1 Spearman | E6-v2 Spearman |',
            '|---|---:|---:|---:|---:|---:|---:|---:|']
    groups=[(f'Fold {k}',g) for k,g in d['per_fold'].items()]+list(d['per_task'].items())
    groups+=[('With definition',d['by_evidence']['1']),('Without definition',d['by_evidence']['0'])]
    for label,g in groups:
        a,b=g['E6-v1'],g['E6-v2']
        lines.append(f"| {label} | {b['n']} | {a['correct']} | {b['correct']} | {a['accuracy']:.10f} | {b['accuracy']:.10f} | {rho(a)} | {rho(b)} |")
    low,high=boot['percentile_95_ci'];lop,hip=boot['percentile_95_ci_pp']
    lines+=['','## Paired E6-v2 versus E6-v1 comparison','',
            f"Corrections: **{paired_result['corrected']}**; new errors: **{paired_result['introduced_errors']}**; net **{net:+d}**. "
            f"Exact two-sided McNemar p = **{paired_result['mcnemar_exact_two_sided_p']:.10f}**.",'',
            f"Accuracy difference v2−v1: **{boot['accuracy_difference']:+.10f}** ({boot['accuracy_difference_pp']:+.6f} percentage points). "
            f"Paired-bootstrap 95% interval: **[{low:+.10f}, {high:+.10f}]**, or **[{lop:+.6f}, {hip:+.6f}] percentage points**.",'',
            'The fixed Module 4/E6 procedure was used: binomtest(corrected, discordant count, .5), p=1 when no discordance; '
            '10,000 paired canonical-row bootstrap resamples of size 561, numpy.default_rng(42), percentile .025/.975. '
            'Every correction and new-error ID is in evaluation/e6_v2_metrics.json; paired_row_diagnostics.csv contains all 561 rows. '
            'Spearman compares p_hallucination against predictions rounded to 12 decimals, while accuracy uses unrounded prediction >=.5. '
            'Subgroup results are descriptive. Bootstrap conditions on saved OOF predictions, not retraining.', '',
            '## Pinned second NLI and model provenance','',
            f"Model and tokenizer: **{c.MODEL_ID}@{c.REVISION}**. Both were loaded via AutoTokenizer / AutoModelForSequenceClassification "
            'from a local mirror downloaded exclusively from this revision, with revision specified, local_files_only=True, trust_remote_code=False. '
            'No remote inference or fine-tuning. Softmax uses three logits. Loaded configuration and model card agree on '
            '**0 entailment, 1 neutral, 2 contradiction**, distinct from the original NLI mapping.', '',
            'The author declares fine-tuning on **MultiNLI, FEVER-NLI, ANLI, LingNLI and WANLI**, totaling 885,242 pairs, with SNLI excluded. '
            'The base is Microsoft DeBERTa-v3-large. These are model-card claims; this experiment does not independently audit pretraining/fine-tuning contamination. '
            f'[Pinned model card](https://huggingface.co/{c.MODEL_ID}/blob/{c.REVISION}/README.md).', '',
            'The complete card is saved as model/README.md. All eight downloaded model/tokenizer/card files have exact source URLs, sizes and SHA-256 '
            'in provenance/acquisition.json; repository SHA is recorded in pinned_repository_metadata.json. Only safetensors weights were downloaded, '
            'not alternative PyTorch/ONNX weights. The 870,182,606-byte safetensors file SHA-256 is '
            '`c03cd208bf920b4fbbb182a0535859a566e8acc3477d2b536bf87b769978524b`.', '',
            '## Feature definition and unchanged base','',
            'Exactly the original 25 E6-v1 columns were retained, in original order and with exact numeric equality after CSV round-trip. '
            'The appended columns are entailment/neutral/contradiction for each of:', '',
            '| Group | Premise | Hypothesis | Feature prefix | Real pairs |',
            '|---|---|---|---|---:|',
            '| A | reference | hyp | nli2_ref_hyp_ | 561 |',
            '| B | hyp | reference | nli2_hyp_ref_ | 561 |',
            '| C | E6-v1 selected definition | hyp | nli2_definition_hyp_ | 193 |', '',
            'reference=tgt for DM/MT and src for PG. Saved strings were passed as-is. A/B are always computed; missing definitions yield '
            'three exact zeros only for C, preserving rag_evidence_available in 368 rows. C reuses the exact selected[0] definition '
            'from the already saved E6-v1 ranking; no retrieval, reranking, replacement or hyp/label-based selection occurred. '
            'Direction B supplies relational information and is not treated as an independent hallucination rule. '
            'All nine scores are stored without intentional rounding.', '',
            '## Runtime, technical smoke and truncation','',
            'A four-pair artificial-text smoke, with no development labels/accuracy, passed before the full protocol/configuration freeze. '
            'CPU was available, CUDA unavailable. Frozen execution: float32, batch size 2, torch threads 4/4, seed 42, eval() and inference_mode(), '
            'eager attention, no autocast. Upstream half-precision weights were explicitly loaded into float32. '
            'Fast DebertaV2Tokenizer and DebertaV2ForSequenceClassification were used with the pinned tokenizer files.', '',
            'Premise and hypothesis are separate tokenizer inputs; max_length=512, truncation="longest_first", batch padding, '
            'attention_mask passed to the model. Untruncated tokenization was used only to audit removed tokens. '
            'All actual model inputs are at most 512 tokens. Original/encoded lengths, removed tokens by side, batch padding and '
            'all affected canonical IDs are recorded in features/truncation_audit.csv.', '',
            '| Group | Pairs | Truncated pairs | Maximum original tokens |','|---|---:|---:|---:|']
    for group,values in freeze['truncation']['by_group'].items():
        lines.append(f"| {group} | {values['pairs']} | {values['truncated']} | {values['max_original_tokens']} |")
    lines+=['',f"Total truncated real pairs: **{freeze['truncation']['truncated_pairs']}**, affecting "
            f"**{freeze['truncation']['truncated_canonical_rows']}** canonical rows. Bulk extraction elapsed: "
            f"**{freeze['duration_seconds']:.3f} seconds** ({freeze['duration_seconds']/60:.3f} minutes), including model loading, "
            'pair tokenization, inference, output and integrity checks; excludes initial model download and smoke. '
            f"Real pairs inferred: {freeze['pairs_inferred_this_execution']}; reused cached pairs: {freeze['pairs_reused_from_cache']}.", '',
            'Runtime: Python 3.11.9, torch 2.11.0, transformers 5.5.4, NumPy 2.4.4, pandas 3.0.2, SciPy 1.17.1, '
            'scikit-learn 1.8.0; full tokenizer and dependency versions in config/smoke.json and run_config.json. '
            'Model loading reports an unused deberta.embeddings.position_ids buffer; no missing model parameters were reported. '
            'Smoke/bulk inference validate finite probabilities and sums within absolute 2e-7.', '',
            '## Evaluation, freeze and integrity','',
            'Same 561 canonical IDs and locked outer folds 113/112/112/112/112. RandomForestRegressor uses the full original E6-v1 parameter '
            'dictionary: 500 trees, random_state=42, min_samples_leaf=1, max_features=1.0, n_jobs=-1 and all 18 explicitly recorded parameters. '
            'No E7 router or E8 tuning settings. Target p_hallucination, clip [0,1], threshold >=.5. Exactly five outer fits; zero additional baseline fits.', '',
            'Baseline verification reproduced E6-v1 453/561, accuracy 0.8074866310160428, Spearman 0.744420539373989 from saved OOF predictions. '
            'ID/fold alignment and original feature values match. Existing E7 fresh-E6 predictions also agree per ID within 1e-12 with identical binary '
            f"and 12-decimal-rounded predictions (actual max difference {baseline['e7_existing_fresh_prediction_max_difference']:.17g}).", '',
            f"Configuration/protocol/source freeze: {lock['frozen_utc']}. Bulk extraction started: {freeze['started_utc']}. "
            f"Feature matrix freeze: {freeze['completed_utc']}. Evaluation completed: {result['completed_utc']}.", '',
            'NLI feature inputs contain no labels, target hallucination probabilities or OOF predictions. The evaluation label join followed feature freeze. '
            'The final audit reassembled the entire 34-feature matrix from saved pair scores, checked truncation, reproduced all metrics and paired statistics, '
            'and verified five RF train/validation ID partitions plus 15 input/target array hashes. '
            f"**{audit['protected_unchanged']} protected previous files remain unchanged.** Network logs after authorized model download are empty. "
            f"Pre-bulk mocked contracts: {lock['contracts_passed']} PASS, including syntax checks for every source file.", '',
            '## Interpretation and limitations','',
            ('The paired 95% interval includes zero; the measured accuracy difference is compatible with no difference on these fixed OOF predictions.'
             if low<=0<=high else 'The paired 95% interval excludes zero on these fixed development OOF predictions; this alone does not establish generalization.'), '',
            '**Exploratory development-only on a reused development set.** The conclusion concerns the entire added nine-feature block; '
            'there was no ablation isolating model choice, reverse direction or external-definition comparison. Existing E6-v1 reference-assisted features remain. '
            'No independent-test claim, selection-adjusted inference or multiplicity correction is made. '
            'Historical E6/Module 4 provenance limitations and the lack of a historical full ranking comparison remain. '
            'No new retrieval, remote inference/LLM API, official-test data access/evaluation, synthetic-data changes, commit/push/tag or next experiment occurred.', '',
            '## Files','',
            '- E6_V2_PROTOCOL.md; config/run_config.json; config/input_manifest.json: frozen method, execution and protected input hashes.',
            '- provenance/ and model/: exact authorized model/tokenizer/card files and provenance; no pretrained model fine-tuning.',
            '- inputs/: label-free NLI pairs, exact definition/reference mapping, canonical metadata and locked folds.',
            '- features/e6_v2_added_9_features.csv; features/e6_v2_34_features.csv; nli2_pair_scores.csv; truncation_audit.csv; per-batch caches.',
            '- evaluation/e6_v2_oof_predictions.csv; e6_v2_metrics.json; paired_row_diagnostics.csv; five fit start/completion records.',
            '- scripts/ and tests/: separate local implementation and contracts; config/final_integrity.json and completion_manifest.json: final verification.','']
    return '\n'.join(lines)


if __name__=='__main__':main()
