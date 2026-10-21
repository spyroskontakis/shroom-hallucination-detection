# E6-v2 — second NLI evaluator: actual results

**COMPLETED — EXPLORATORY DEVELOPMENT-ONLY on a reused development pool.** One frozen 34-feature configuration, one five-fold OOF suite, five Random Forest fits. No post-score changes or tuning. The conclusion concerns the complete nine-feature NLI block.

## Overall OOF result

| Version | Features | Correct / N | Accuracy | Spearman |
|---|---:|---:|---:|---:|
| E6-v1 | 25 | 453/561 | 0.8074866310 (80.7487%) | 0.7444205394 |
| E6-v2 | 34 | 473/561 | 0.8431372549 (84.3137%) | 0.7775058305 |

The observed accuracy improvement is +3.565062 percentage points, net +20/561 correct predictions.

## Fold, task and evidence results

| Group | N | E6-v1 correct | E6-v2 correct | E6-v1 accuracy | E6-v2 accuracy | E6-v1 Spearman | E6-v2 Spearman |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fold 1 | 113 | 93 | 98 | 0.8230088496 | 0.8672566372 | 0.7636250604 | 0.8156957930 |
| Fold 2 | 112 | 85 | 93 | 0.7589285714 | 0.8303571429 | 0.7313740768 | 0.7702660177 |
| Fold 3 | 112 | 90 | 95 | 0.8035714286 | 0.8482142857 | 0.7567080297 | 0.7646050923 |
| Fold 4 | 112 | 87 | 90 | 0.7767857143 | 0.8035714286 | 0.7254257584 | 0.7746092246 |
| Fold 5 | 112 | 98 | 97 | 0.8750000000 | 0.8660714286 | 0.7348041615 | 0.7785442987 |
| DM | 211 | 162 | 167 | 0.7677725118 | 0.7914691943 | 0.6483380720 | 0.6705929861 |
| MT | 216 | 186 | 191 | 0.8611111111 | 0.8842592593 | 0.7969005342 | 0.8289100487 |
| PG | 134 | 105 | 115 | 0.7835820896 | 0.8582089552 | 0.6950040245 | 0.7602790111 |
| With definition | 193 | 149 | 155 | 0.7720207254 | 0.8031088083 | 0.6565323714 | 0.6774871628 |
| Without definition | 368 | 304 | 318 | 0.8260869565 | 0.8641304348 | 0.7701942329 | 0.8108403495 |

## Paired E6-v2 versus E6-v1 comparison

Corrections: **42**; new errors: **22**; net **+20**. Exact two-sided McNemar p = **0.0168581900**.

Accuracy difference v2−v1: **+0.0356506239** (+3.565062 percentage points). Paired-bootstrap 95% interval: **[+0.0071301248, +0.0641711230]**, or **[+0.713012, +6.417112] percentage points**.

The fixed Module 4/E6 procedure was used: binomtest(corrected, discordant count, .5), p=1 when no discordance; 10,000 paired canonical-row bootstrap resamples of size 561, numpy.default_rng(42), percentile .025/.975. Every correction and new-error ID is in evaluation/e6_v2_metrics.json; paired_row_diagnostics.csv contains all 561 rows. Spearman compares p_hallucination against predictions rounded to 12 decimals, while accuracy uses unrounded prediction >=.5. Subgroup results are descriptive. Bootstrap conditions on saved OOF predictions, not retraining.

## Pinned second NLI and model provenance

Model and tokenizer: **MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli@b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7**. Both were loaded via AutoTokenizer / AutoModelForSequenceClassification from a local mirror downloaded exclusively from this revision, with revision specified, local_files_only=True, trust_remote_code=False. No remote inference or fine-tuning. Softmax uses three logits. Loaded configuration and model card agree on **0 entailment, 1 neutral, 2 contradiction**, distinct from the original NLI mapping.

The author declares fine-tuning on **MultiNLI, FEVER-NLI, ANLI, LingNLI and WANLI**, totaling 885,242 pairs, with SNLI excluded. The base is Microsoft DeBERTa-v3-large. These are model-card claims; this experiment does not independently audit pretraining/fine-tuning contamination. [Pinned model card](https://huggingface.co/MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli/blob/b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7/README.md).

The complete card is saved as model/README.md. All eight downloaded model/tokenizer/card files have exact source URLs, sizes and SHA-256 in provenance/acquisition.json; repository SHA is recorded in pinned_repository_metadata.json. Only safetensors weights were downloaded, not alternative PyTorch/ONNX weights. The 870,182,606-byte safetensors file SHA-256 is `c03cd208bf920b4fbbb182a0535859a566e8acc3477d2b536bf87b769978524b`.

## Feature definition and unchanged base

Exactly the original 25 E6-v1 columns were retained, in original order and with exact numeric equality after CSV round-trip. The appended columns are entailment/neutral/contradiction for each of:

| Group | Premise | Hypothesis | Feature prefix | Real pairs |
|---|---|---|---|---:|
| A | reference | hyp | nli2_ref_hyp_ | 561 |
| B | hyp | reference | nli2_hyp_ref_ | 561 |
| C | E6-v1 selected definition | hyp | nli2_definition_hyp_ | 193 |

reference=tgt for DM/MT and src for PG. Saved strings were passed as-is. A/B are always computed; missing definitions yield three exact zeros only for C, preserving rag_evidence_available in 368 rows. C reuses the exact selected[0] definition from the already saved E6-v1 ranking; no retrieval, reranking, replacement or hyp/label-based selection occurred. Direction B supplies relational information and is not treated as an independent hallucination rule. All nine scores are stored without intentional rounding.

## Runtime, technical smoke and truncation

A four-pair artificial-text smoke, with no development labels/accuracy, passed before the full protocol/configuration freeze. CPU was available, CUDA unavailable. Frozen execution: float32, batch size 2, torch threads 4/4, seed 42, eval() and inference_mode(), eager attention, no autocast. Upstream half-precision weights were explicitly loaded into float32. Fast DebertaV2Tokenizer and DebertaV2ForSequenceClassification were used with the pinned tokenizer files.

Premise and hypothesis are separate tokenizer inputs; max_length=512, truncation="longest_first", batch padding, attention_mask passed to the model. Untruncated tokenization was used only to audit removed tokens. All actual model inputs are at most 512 tokens. Original/encoded lengths, removed tokens by side, batch padding and all affected canonical IDs are recorded in features/truncation_audit.csv.

| Group | Pairs | Truncated pairs | Maximum original tokens |
|---|---:|---:|---:|
| A | 561 | 0 | 135 |
| B | 561 | 0 | 135 |
| C | 193 | 0 | 78 |

Total truncated real pairs: **0**, affecting **0** canonical rows. Bulk extraction elapsed: **1020.705 seconds** (17.012 minutes), including model loading, pair tokenization, inference, output and integrity checks; excludes initial model download and smoke. Real pairs inferred: 1315; reused cached pairs: 0.

Runtime: Python 3.11.9, torch 2.11.0, transformers 5.5.4, NumPy 2.4.4, pandas 3.0.2, SciPy 1.17.1, scikit-learn 1.8.0; full tokenizer and dependency versions in config/smoke.json and run_config.json. Model loading reports an unused deberta.embeddings.position_ids buffer; no missing model parameters were reported. Smoke/bulk inference validate finite probabilities and sums within absolute 2e-7.

## Evaluation, freeze and integrity

Same 561 canonical IDs and locked outer folds 113/112/112/112/112. RandomForestRegressor uses the full original E6-v1 parameter dictionary: 500 trees, random_state=42, min_samples_leaf=1, max_features=1.0, n_jobs=-1 and all 18 explicitly recorded parameters. No E7 router or E8 tuning settings. Target p_hallucination, clip [0,1], threshold >=.5. Exactly five outer fits; zero additional baseline fits.

Baseline verification reproduced E6-v1 453/561, accuracy 0.8074866310160428, Spearman 0.744420539373989 from saved OOF predictions. ID/fold alignment and original feature values match. Existing E7 fresh-E6 predictions also agree per ID within 1e-12 with identical binary and 12-decimal-rounded predictions (actual max difference 4.4408920985006262e-16).

Configuration/protocol/source freeze: 2026-09-10T08:53:58.169146+00:00. Bulk extraction started: 2026-09-10T08:54:31.576698+00:00. Feature matrix freeze: 2026-09-10T09:11:32.281885+00:00. Evaluation completed: 2026-09-10T12:59:19.635428+00:00.

NLI feature inputs contain no labels, target hallucination probabilities or OOF predictions. The evaluation label join followed feature freeze. The final audit reassembled the entire 34-feature matrix from saved pair scores, checked truncation, reproduced all metrics and paired statistics, and verified five RF train/validation ID partitions plus 15 input/target array hashes. **608 protected previous files remain unchanged.** Network logs after authorized model download are empty. Pre-bulk mocked contracts: 7 PASS, including syntax checks for every source file.

## Interpretation and limitations

The paired 95% interval excludes zero on these fixed development OOF predictions; this alone does not establish generalization.

**Exploratory development-only on a reused development set.** The conclusion concerns the entire added nine-feature block; there was no ablation isolating model choice, reverse direction or external-definition comparison. Existing E6-v1 reference-assisted features remain. No independent-test claim, selection-adjusted inference or multiplicity correction is made. Historical E6/Module 4 provenance limitations and the lack of a historical full ranking comparison remain. No new retrieval, remote inference/LLM API, official-test data access/evaluation, synthetic-data changes, commit/push/tag or next experiment occurred.

## Files

- E6_V2_PROTOCOL.md; config/run_config.json; config/input_manifest.json: frozen method, execution and protected input hashes.
- provenance/ and model/: exact authorized model/tokenizer/card files and provenance; no pretrained model fine-tuning.
- inputs/: label-free NLI pairs, exact definition/reference mapping, canonical metadata and locked folds.
- features/e6_v2_added_9_features.csv; features/e6_v2_34_features.csv; nli2_pair_scores.csv; truncation_audit.csv; per-batch caches.
- evaluation/e6_v2_oof_predictions.csv; e6_v2_metrics.json; paired_row_diagnostics.csv; five fit start/completion records.
- scripts/ and tests/: separate local implementation and contracts; config/final_integrity.json and completion_manifest.json: final verification.
