# E6-v2 — επέκταση του E6 με δεύτερο NLI αξιολογητή

**Κατάσταση: πλήρες πρωτόκολλο, οριστικοποιημένο μετά το τεχνικό smoke και πριν από bulk inference/αξιολόγηση. Το SHA-256 παγώνει στο config/run_config.json.**

Καταγράφηκε στις 2026-09-10. Η νέα επέκταση ονομάζεται **E6-v2**, αντί της προτεινόμενης ονομασίας E9. Δεν βρέθηκε προϋπάρχουσα υλοποίηση E9 ή E6-v2 στο project κατά την αρχική αναζήτηση.

## Επιβεβαιωμένες οδηγίες

- Φάκελος νέων αποτελεσμάτων: `RAG/results/rag_e6_v2/`.
- Πρωτόκολλο: `E6_V2_PROTOCOL.md`.
- Τελική αναφορά μετά την πραγματική αξιολόγηση: `E6_V2_RESULTS.md`.
- Είσοδος: τα 25 παγωμένα χαρακτηριστικά του **E6-v1**, συν 9 νέα χαρακτηριστικά από δεύτερο NLI αξιολογητή· συνολικά 34.
- Πηγή αρχικών χαρακτηριστικών, ορισμών και baseline: αποκλειστικά `RAG/results/rag_e6_v1/`.
- Baseline **E6-v1**: 453/561, accuracy 0.8074866310160428, Spearman 0.744420539373989.
- Οι συγκριτικοί πίνακες θα διακρίνουν ρητά **E6-v1** και **E6-v2**.
- Το E6-v1 και όλα τα προηγούμενα αποτελέσματα παραμένουν ανέπαφα.
- Το πραγματικό αποτέλεσμα της v2 θα αναφερθεί είτε βελτιώνει είτε όχι την επίδοση.

## Πλήρεις τεχνικές οδηγίες και ιστορικό

Οι πλήρεις οδηγίες παραλήφθηκαν και διατηρούνται στο provenance/user_request.txt. Το αρχικό προσχέδιο διατηρείται στο history/INITIAL_NAMING_DRAFT.md. Καμία προηγούμενη E6-v2 εκτέλεση δεν υπήρχε. Τα E7/E8 πρωτόκολλα και αποτελέσματα διαβάστηκαν· δεν μεταφέρεται router ή tuning. Οι επόμενες ενότητες αποτελούν το μοναδικό πρωτόκολλο εκτέλεσης.

## Fixed population, baseline and RF

Use exactly 561 canonical IDs in E6-v1 feature order, and the five locked outer folds (113/112/112/112/112). Load the 25 original columns with pandas float_precision='round_trip'; retain numeric equality and order, without scaling, imputation or selection. Append the nine columns below. Frozen E6-v1 OOF predictions are the baseline; verify their hashes and ID/fold alignment, then recompute baseline metrics after feature freeze. The existing E7 fresh-E6 predictions provide an additional per-ID check at atol=1e-12, rtol=0 with exact binary and 12-decimal-rounded equality; no new baseline fits.

Exactly one five-fold RF suite: training rows exclude the corresponding outer-validation fold. Target p_hallucination; clip predictions [0,1]; binary threshold >=0.5. Five RF fits, no search or final all-data model. Explicit full parameters, identical to E6-v1:

```json
{"n_estimators":500,"criterion":"squared_error","max_depth":null,"min_samples_split":2,"min_samples_leaf":1,"min_weight_fraction_leaf":0.0,"max_features":1.0,"max_leaf_nodes":null,"min_impurity_decrease":0.0,"bootstrap":true,"oob_score":false,"n_jobs":-1,"random_state":42,"verbose":0,"warm_start":false,"ccp_alpha":0.0,"max_samples":null,"monotonic_cst":null}
```

## Pinned second NLI and source documentation

Model/tokenizer ID: MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli. Immutable revision for both: b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7. Only this revision's authorized files/documentation were downloaded. URLs, repository SHA, sizes and SHA-256 appear in provenance/acquisition.json and pinned_repository_metadata.json. Load the local immutable mirror through AutoTokenizer and AutoModelForSequenceClassification, with revision specified, local_files_only=True, trust_remote_code=False, use_fast=True for tokenizer, use_safetensors=True for model.

Both loaded config and model card specify 0 entailment, 1 neutral, 2 contradiction. Assert id2label, label2id and num_labels=3. Model card declares MultiNLI, FEVER-NLI, ANLI, LingNLI, WANLI (885,242 fine-tuning pairs), with SNLI excluded; these are author claims, not a new contamination audit. Base encoder: DeBERTa-v3-large. Card saved at model/README.md. Source: https://huggingface.co/MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli/blob/b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7/README.md

## Exact text pairs and feature order

reference=tgt for DM/MT, reference=src for PG. Use stored text as-is, with no prompts, normalization, stripping or field substitution; nonempty checks do not alter strings.

| Group | Premise | Hypothesis | Prefix |
|---|---|---|---|
| A | reference | hyp | nli2_ref_hyp_ |
| B | hyp | reference | nli2_hyp_ref_ |
| C | E6-v1 selected rank-1 candidate_definition | hyp | nli2_definition_hyp_ |

Append entailment, neutral, contradiction in that order to each prefix, A then B then C: nine columns, 34 total. B is additional relational information, not an independent hallucination rule. Apply softmax to all three logits and save float32-derived scores without intentional rounding.

C reads only selected[0].candidate_definition from E6-v1/ranking/reconstructed_top5.jsonl. Verify rank=1, evidence ID, count, availability and top-1 score consistency with E6-v1. Never retrieve, rerank or replace evidence. There are 193 real C pairs; 368 missing-definition rows get exactly three C zeros and retain original rag_evidence_available. A/B remain normal inference for every row. Process 1,315 pairs: 561 A + 561 B + 193 C, canonical row order with A/B/C within row.

## Smoke-tested execution and truncation

Four artificial text pairs, including long and differently sized inputs, passed a label-free technical smoke; no accuracy was computed. CUDA is unavailable. Freeze CPU, float32, batch size 2, seed 42, model.eval(), torch.inference_mode(), no fine-tuning/autocast. Upstream weights/config specify float16; explicitly load and execute in tested float32. Loaded tokenizer: fast DebertaV2Tokenizer; model: DebertaV2ForSequenceClassification; attention implementation eager; torch intra/inter-op threads 4/4. Reuse these settings unchanged.

Pass premise and hypothesis as two distinct tokenizer arguments: max_length=512, truncation='longest_first', padding=True per batch, return_attention_mask=True, return_tensors='pt'. Pass all returned model inputs, including attention_mask. Separately tokenize the same pairs without truncation solely to record original lengths and sequence membership. Record original/used tokens, premise/hypothesis removed tokens, padded length, truncation flag, canonical ID/group. Only truncated inputs enter the model. Audit-tokenization long-input warnings do not imply untruncated inference.

Preserve accepted runtime: Python 3.11.9, torch 2.11.0, transformers 5.5.4, NumPy 2.4.4, pandas 3.0.2, SciPy 1.17.1, scikit-learn 1.8.0; save tokenizer/sentencepiece/safetensors versions. After authorized download, HF offline flags and process-local network blockers apply to smoke, extraction and evaluation. All new model/cache/experiment files stay under E6-v2.

## Integrity gates and artifact freeze

Verify the 608 protected existing files against config/input_manifest.json, including original E6-v1 and completed E7/E8 manifests. Validate unique/aligned IDs, folds, all required text fields, model output order, finite probabilities, probability sums within absolute 2e-7 and exact C-zero fallback. Labels, p_hallucination and baseline predictions are excluded from saved NLI inputs and model calls. Only explicit canonical text projections are used. No labels in smoke or feature extraction; evaluation label join follows feature freeze.

Before bulk inference, run mocked contracts for A/B direction, task reference, first stored definition, forbidden label fields, fallback, schema/feature order, probability validity, metric conventions and compilation of every source file. Freeze this protocol, configuration, smoke, code/tests and label-free inputs with SHA-256 and timestamps. Batch scores are cached using immutable pair/config identity; validated successful batches can be reused after a documented technical interruption, never changed due to results. Completed matrices and evaluation outputs are not overwritten. An exclusive evaluation-start marker prevents a second RF suite.

Freeze nine-feature and 34-feature CSVs and pair/truncation audits before evaluation. Recheck exact numeric preservation of original 25 features after CSV round-trip. Record train/validation IDs and array hashes for all five RF fits; verify original artifacts again after execution.

## Metrics and interpretation

Report correct/N, accuracy and Spearman overall, each fold, DM/MT/PG, with/without definition. Spearman uses unrounded p_hallucination and predictions rounded to 12 decimals, exactly as E6-v1. Undefined small/constant correlations are null. Classification and NLI features are not rounded.

Paired E6-v2 minus E6-v1: corrections, new errors and IDs; exact two-sided McNemar binomtest(corrected, corrected+new_errors, .5), p=1 for no discordance; 10,000 paired resamples of 561 correctness differences in canonical order using numpy.default_rng(42), percentile .025/.975. Report raw and percentage-point differences/CI. No tuning, multiplicity/adaptive-research correction or repeat fitting. Bootstrap conditions on fixed OOF predictions and omits retraining uncertainty.

E6_V2_RESULTS.md reports actual results regardless of direction, extraction time, truncations, five RF fits, zero extra baseline fits, configuration/provenance and final integrity. Comparative labels: E6-v1/E6-v2. Conclusions concern the entire new NLI feature block. This is exploratory development-only on a reused dataset, not an independent test. Inherited reference-assisted features and prior provenance limitations remain.

No new retrieval, remote inference/LLM API, official-test data access/evaluation, synthetic-data edits, commit/push/tag or other experiment. Preserve all previous results and untracked changes.
