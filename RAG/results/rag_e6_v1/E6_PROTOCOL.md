# E6 v1 — locked development-only protocol

Recorded 2026-09-09 before E6 encoding, inference, training or evaluation. No E6 run existed in the inspected project artifacts.

## Population and estimator

Use the same ordered 561 canonical IDs as Module 4, and the existing five locked folds, without regeneration. Preserve all 21 E5 predictors in their existing order and values. Append, in order: `rag_definition_hyp_cosine`, `rag_definition_hyp_entailment`, `rag_definition_hyp_neutral`, `rag_definition_hyp_contradiction`. Total: 25 predictors.

RandomForestRegressor(n_estimators=500, random_state=42, n_jobs=-1), remaining parameters unchanged from the Module 4 runtime defaults; target p_hallucination; predictions clipped to [0,1]; binary decision prediction >= 0.5. No tuning, calibration, synthetic data, additional experiment, official test access, retrieval or network/API calls.

## New features

Use only rank 1 from the previously saved Module 4 retrieval ranking. Never select or rerank using hyp or labels. Use candidate_definition text without POS/context decoration for comparison. Premise = definition; hypothesis = hyp. MPNet sentence-transformers/all-mpnet-base-v2@e8c3b32edf5434bc2275fc9bab85f82640a19130, max sequence length 256, normalized embeddings, cosine dot product after the Module 4 float64 renormalization. NLI microsoft/deberta-large-mnli@7296194b9009373def4f7c5dad292651e4b5cf4e, float32 CPU, eval/inference mode, tokenizer truncation/padding, max length 512, indices contradiction=0, neutral=1, entailment=2. Seed 42; local_files_only and offline flags.

Rows without evidence receive exactly four zeros; preserve rag_evidence_available. Freeze and hash new features before joining evaluation labels. Read canonical hyp using a restricted column projection.

## Compatibility and statistics

Verify SHA-256 of canonical manifest (754b66c6c4eca2e92902d0408db4854e922d7dfb396953a0cc043c5477bd6a9b), folds (f5a5964923806a23dd34a8bcc137f3cf489437e033d645e9d0845bf40792eb5d), 14-feature matrix (3038bd8752a94064e05389e03b063484a1191f9e9a6164f06d11b40688a6828b), accepted seven features (708483b831430d876135d1484ad841bf6ba0d9c9a2d0a5f22df6280535fe3160), release artifacts and saved OOF predictions. Verify one-to-one IDs/folds and baseline counts E3=445/561, E5=446/561 before interpreting E6. Reuse valid baselines; do not retrain them unnecessarily.

Report overall, DM/MT/PG, evidence/no-evidence and fold metrics. Spearman uses p_hallucination and predictions rounded to 12 decimals, exactly as Module 4. For each baseline report corrections, introduced errors, exact two-sided McNemar binomial test (p=1 for zero discordant pairs), and paired row bootstrap accuracy difference E6 minus baseline: numpy default_rng(42), 10,000 replicates of 561 paired rows, percentile 2.5/97.5 interval. No multiplicity-adjusted significance claim. Development-only interpretation regardless of direction.

## Input issue identified before execution

The inspected Module 4 feature and overlap scripts compute rankings in memory and save only aggregate features/counts, not ordered evidence IDs. The lexical snapshot is parser order, not retrieval rank. Module 2 top-five candidates belong to a different retrieval experiment and cannot substitute for Module 4 external evidence. Execution must wait for a valid saved Module 4 ranking or explicit authorization for local reconstruction of its frozen ranking. No reconstruction is authorized by this document.

## Output layout

All new files stay under RAG/results/rag_e6_v1/: scripts/, features/, evaluation/, config/, and E6_RESULTS.md. Existing E3/E5 files remain read-only. One E6 configuration and one evaluation only; completed outputs must not be overwritten.

## Authorized addendum — 2026-09-09, before any E6 inference/evaluation

The user explicitly authorized local reconstruction from the frozen Module 4 lexical snapshot as a specific exception to the retrieval prohibition. This supersedes the historical waiting condition above. There is no historical ranking file available for direct comparison.

Call the accepted pinned Module 4 `select_top5` function unchanged: exact normalized-term candidates; query `term + "\n" + src`; candidate encoding `candidate_term + "\n" + candidate_context`; normalized MPNet embeddings, float64 renormalization and dot product; descending cosine, then source_entry_id, then evidence_id; top_k=5. Ranking inputs are projected to example_id, task, term, src, rag_applicable only. The eligibility flags/identifiers are metadata; only term and src supply query text. No tgt, hyp, labels, predictions or evaluation results enter candidate selection/ranking. Freeze and hash the ordered top-five records, scores and canonical-ID mapping before reading hyp.

Compare reconstructed evidence availability and selected sense count exactly to E5 and top-1 cosine at absolute tolerance 1e-12, rtol=0 (execution/serialization tolerance, never a ranking rule). Record actual maximum difference. Any failure blocks feature inference/evaluation for investigation. Agreement of these aggregates is a consistency check; it does not by itself prove the complete historical order. Use only the first reconstructed definition for the four new features.

Use the accepted pinned CPU float32 backends unchanged, and verify model/tokenizer files against the accepted replay provenance. Save runtime versions, resolved files and hashes. Preserve source artifacts with a before/after SHA-256 inventory. Four-feature inference occurs only after ranking freeze and consistency PASS. The first 21 E6 columns are taken from the same canonical 14-feature plus accepted seven-feature inputs used to train E5; compare them with the saved fused E5 matrix allowing only CSV floating-point serialization noise. No feature scaling or transformation is applied to them.

Before E6 fitting, recompute saved E3/E5 metrics from their existing OOF predictions and canonical labels, verify 445/561 and 446/561 and their recorded Spearman values, and verify all predictor values, IDs and fold assignments. No baseline inference or retraining is required if these checks pass. Run E6 CV once using the accepted Module 4 `run_cv` function with the 25-feature list. Save all estimator defaults and code hashes before execution; do not change them after the score is observed.

Execution commands use the existing shroom_ensemble Python environment, `-B`, local_files_only, Hugging Face offline flags and a process-local socket guard. All outputs, including temporary/checkpoint files, remain inside the E6 directory. Development-only findings will not establish generalization or replace a final configuration automatically.
