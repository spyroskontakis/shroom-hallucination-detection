# E6-v3 — E6-v2 plus Vectara HHEM-1.0: results

**COMPLETED. Exploratory development-only on a reused development set.** One predetermined 36-feature configuration, one five-fold OOF evaluation, exactly five RF fits and zero baseline fits. No post-score change. The conclusion concerns the entire two-feature HHEM block.

| Version | Features | Correct/N | Accuracy | Spearman |
|---|---:|---:|---:|---:|
| E6-v2 | 34 | 473/561 | 0.8431372549 | 0.7775058305 |
| E6-v3 | 36 | 474/561 | 0.8449197861 | 0.7816945786 |

Accuracy difference E6-v3 − E6-v2: **+0.178253 percentage points**, net **+1/561** correct.

## Fold, task and evidence results

| Group | N | E6-v2 correct | E6-v3 correct | E6-v2 accuracy | E6-v3 accuracy | E6-v2 Spearman | E6-v3 Spearman |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fold 1 | 113 | 98 | 100 | 0.8672566372 | 0.8849557522 | 0.8156957930 | 0.8161783605 |
| Fold 2 | 112 | 93 | 91 | 0.8303571429 | 0.8125000000 | 0.7702660177 | 0.7693547089 |
| Fold 3 | 112 | 95 | 93 | 0.8482142857 | 0.8303571429 | 0.7646050923 | 0.7703346139 |
| Fold 4 | 112 | 90 | 92 | 0.8035714286 | 0.8214285714 | 0.7746092246 | 0.7792654109 |
| Fold 5 | 112 | 97 | 98 | 0.8660714286 | 0.8750000000 | 0.7785442987 | 0.7840673179 |
| DM | 211 | 167 | 169 | 0.7914691943 | 0.8009478673 | 0.6705929861 | 0.6852178827 |
| MT | 216 | 191 | 191 | 0.8842592593 | 0.8842592593 | 0.8289100487 | 0.8327371481 |
| PG | 134 | 115 | 114 | 0.8582089552 | 0.8507462687 | 0.7602790111 | 0.7522106511 |
| With definition | 193 | 155 | 157 | 0.8031088083 | 0.8134715026 | 0.6774871628 | 0.6941425689 |
| Without definition | 368 | 318 | 317 | 0.8641304348 | 0.8614130435 | 0.8108403495 | 0.8119705384 |

## Paired comparison

**10 corrections**, **9 new errors**; both correct 464, both wrong 78. Exact two-sided McNemar **p=1.0000000000**.

Paired-bootstrap 95% accuracy-difference interval: **[-1.426025, +1.604278] percentage points** (raw difference +0.0017825312; raw interval [-0.0142602495543672, 0.016042780748663103]).

Same E6-v2/Module 4 procedure: binomtest(corrected, discordant count, .5), two-sided; p=1 if no discordance. 10,000 paired row resamples of size 561, numpy.default_rng(42), numpy.quantile at .025/.975. Spearman uses p_hallucination versus predictions rounded to 12 decimals; accuracy uses unrounded predictions >=.5. Corrected/new-error IDs are in evaluation/e6_v3_metrics.json, with all 561 row details in paired_row_diagnostics.csv. Subgroups are descriptive; bootstrap conditions on fixed OOF predictions and does not refit models.

## Pinned model and score semantics

**vectara/hallucination_evaluation_model@58383384656cbaec2949a75a41f20e891e90a73b**, historical hhem-1.0-open. Model and tokenizer were loaded from the same local revision mirror, with local_files_only=True and trust_remote_code=False. Runtime architecture DebertaV2ForSequenceClassification, one output logit. torch.sigmoid(raw logit) is applied exactly once, matching the historical Transformers example; higher means supported by the premise. No single-logit softmax, score inversion or second sigmoid.

The [pinned model card](https://huggingface.co/vectara/hallucination_evaluation_model/blob/58383384656cbaec2949a75a41f20e891e90a73b/README.md) declares MultiNLI, SNLI, FEVER, Vitamin C and PAWS training data, using microsoft/deberta-v3-base. These are author claims, not an independent contamination audit. The historical AutoModel example and downloaded card were checked directly. provenance/acquisition.json records exact revision URLs, bytes and SHA-256 for eight required files. The PyTorch weight hash also matches the Hub x-linked-etag; no alternative model revision was used.

The model stays eval(), requires_grad_(False) and inference_mode(); no fine-tuning. The four artificial-text smoke pairs and seven pre-bulk contracts passed before protocol freeze. Contracts cover exact A/C projection and label rejection, missing-definition zeros, corruption/config/text cache rejection, single-sigmoid semantics, paired tokenization/masks/truncation, folds, metrics and source syntax. No RF fits occur in tests.

## Features and extraction

All 34 saved E6-v2 columns are retained with identical values and order after round-trip CSV reading. Exactly two columns are appended:

| Feature | Premise | Hypothesis | Inferred pairs |
|---|---|---|---:|
| hhem_ref_hyp_consistency | saved A reference (tgt DM/MT, src PG) | hyp | 561 |
| hhem_definition_hyp_consistency | saved C selected definition | hyp | 193 |

All 754 pairs reuse the exact saved E6-v2 strings. No B/reverse pairs, new retrieval, reranking or definition replacement. The 368 absent-definition rows receive exact zero in the second feature, with rag_evidence_available unchanged. Inputs exclude labels, target probabilities and predictions. Label joining occurs only after the feature matrix freeze.

CPU float32, batch=2, seeds42, torch threads4/4, eager attention, no autocast. Fast tokenizer; separate premise/hypothesis, max_length512, longest_first, per-batch padding and attention_mask. Raw logits and scores have no intentional rounding. Original and encoded lengths, side-specific removed tokens, padded lengths and IDs are in features/truncation_audit.csv. The smoke warning for an untruncated long sequence came from length auditing; actual model inputs are at most512 tokens.

| Group | Pairs | Truncated | Maximum original tokens |
|---|---:|---:|---:|
| A | 561 | 0 | 135 |
| C | 193 | 0 | 78 |

Real truncated pairs: **0**, affected canonical rows **0**. Bulk extraction elapsed **248.662s** (4.144min), summed tokenization/inference batch time **226.518s**. Elapsed includes lazy model load, outputs and final integrity checks after initial verification; excludes download and smoke. This extraction invocation inferred 754 pairs and reused 0 cached pairs.

377 atomic batch caches contain configuration/text hashes, ordered pair IDs, payload hashes, raw logits, scores, truncation and durations. Every cache was revalidated and reconstructed into the final matrix without inference. Resumption verifies completed batches and computes only missing batches; session-specific logs support technical interruption.

## Fixed evaluation and integrity

Same 561 canonical IDs and locked folds. Baseline saved E6-v2 predictions and row diagnostics match per ID/fold and reproduce 473/561, accuracy 0.8431372549019608, Spearman 0.7775058304756869. No baseline retraining. RandomForestRegressor uses all18 explicitly frozen E6-v2 parameters (500 trees, seed42, min_samples_leaf1, max_features1.0); full dictionary below. Each of five fits uses only its outer training rows. Target p_hallucination, clip[0,1], threshold>=.5. No E7 router or E8 tuning.

```json
{
  "bootstrap": true,
  "ccp_alpha": 0.0,
  "criterion": "squared_error",
  "max_depth": null,
  "max_features": 1.0,
  "max_leaf_nodes": null,
  "max_samples": null,
  "min_impurity_decrease": 0.0,
  "min_samples_leaf": 1,
  "min_samples_split": 2,
  "min_weight_fraction_leaf": 0.0,
  "monotonic_cst": null,
  "n_estimators": 500,
  "n_jobs": -1,
  "oob_score": false,
  "random_state": 42,
  "verbose": 0,
  "warm_start": false
}
```

Protocol/source/config freeze: 2026-09-10T15:51:47.304960+00:00. Extraction start: 2026-09-10T15:52:15.549162+00:00. Matrix freeze: 2026-09-10T15:56:24.213552+00:00. Evaluation complete: 2026-09-10T15:56:51.690963+00:00.

Final integrity **PASS**: 1327 previous files unchanged; all36 feature columns reassembled exactly; 754 cache scores and truncation records checked; all metrics and paired statistics recomputed; five train/validation partitions and15 array hashes verified. Model, input, code and protocol hashes match. Network logs for smoke/contracts/extraction/evaluation/report are empty; only the authorized pinned download used network.

Runtime versions (same accepted E6-v2 environment):

```json
{
  "executable": "external-artifacts/local-55ad9e4e5b1b/python.exe",
  "packages": {
    "numpy": "2.4.4",
    "pandas": "3.0.2",
    "safetensors": "0.7.0",
    "scikit-learn": "1.8.0",
    "scipy": "1.17.1",
    "sentencepiece": "0.2.1",
    "tokenizers": "0.22.2",
    "torch": "2.11.0",
    "transformers": "5.5.4"
  },
  "python": "3.11.9 | packaged by Anaconda, Inc. | (main, Apr 19 2024, 16:40:41) [MSC v.1916 64 bit (AMD64)]"
}
```

## Interpretation

The paired interval includes zero; the measured accuracy difference is compatible with no difference on these fixed OOF predictions.

**Exploratory development-only on a reused development set.** The result concerns adding the entire HHEM block, without attributing effects to either individual feature. This is inspired by combining evaluators in Halu-NLP/MetaCheckGPT, not a reproduction of the full system. Existing reference-assisted features and the historical provenance limitations remain. The selected definitions descend from the frozen Module4 reconstruction; no historical full ranking file exists for direct comparison, and agreement of aggregate E5 features alone does not prove the whole historical order. There is no independent-test or selection-adjusted statistical claim. No official-test access, paid API, remote inference, synthetic-data edits, commit/push/tag or further experiment occurred.

## Artifacts

- E6_V3_PROTOCOL.md; config/run_config.json: frozen protocol, all choices and code/input manifest.
- provenance/ and model/: pinned sources, card, weights/tokenizer and hashes.
- inputs/: exact label-free pairs, definition/reference mapping and locked folds.
- features/e6_v3_added_2_features.csv; features/e6_v3_36_features.csv; hhem_pair_scores.csv; truncation_audit.csv; chunks/.
- evaluation/e6_v3_oof_predictions.csv; e6_v3_metrics.json; paired_row_diagnostics.csv; five fit start/completion records.
- scripts/; tests/; config/contracts.json; config/final_integrity.json; config/completion_manifest.json.
