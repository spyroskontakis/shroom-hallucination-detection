# E9 predeclared development protocol

Current decomposition clarification: [Amendment 01](E9_PROTOCOL_AMENDMENT_01.md)
supersedes the original world-verifiability filter, single-claim rewriting,
prompt version and smoke size below. The original text remains as protocol history.
Only the amended nine-sample smoke has been authorized; no full run is authorized.

Status: local preparation complete; execution blocked before decomposition.
No official SHROOM test file may be accessed, even for an overlap check.
The existing canonical development manifest is the sole population authority.

## Frozen experiment

561 canonical rows: 493 development_model_agnostic and 68 trial. Reuse locked
folds 1–5 with sizes 113/112/112/112/112. The 36 E6-v3 columns retain their
order and exact floating-point values. Baseline verification uses saved OOF
predictions, never a refit. Configurations and input hashes are recorded locally.

RandomForestRegressor uses every parameter from E6-v3: 500 trees,
random_state=42, max_features=1.0, min_samples_leaf=1, n_jobs=-1, and the
remaining explicit defaults in config/run_config.json. Target is p_hallucination.
Each completed variant gets exactly five fits. Predictions are clipped to [0,1];
binary classification uses >=0.5. Spearman uses predictions rounded to 12 decimals.
No learned preprocessing, threshold selection, tuning, fold generation or E9-C.

## Claim extraction

This is a Claimify-style adaptation, not a replication of the paper's full
multi-completion implementation. It combines selection, hypothesis-internal
disambiguation and atomic decomposition in one structured response. It follows
the paper's emphasis on faithful claims and unresolved ambiguity, with the
user-required original-hypothesis fallback replacing sample exclusion.
Reference: Metropolitansky & Larson, [ACL 2025](https://aclanthology.org/2025.acl-long.348/).

Pinned model: gpt-4o-2024-08-06; temperature=0; prompt e9-hyp-only-v1.
The API payload accepts exactly hyp and task. Canonical IDs are attached only
locally. Labels, probabilities, reference text, definitions, folds and saved
predictions never enter the payload. Quoted hypothesis content is treated as data.
The model must preserve negation, uncertainty, attribution and quantities.
No external context or factual correction is permitted.

Strict JSON schema plus local validation checks claim structure, exact support
quotes, and model-declared entailment/atomicity/self-containment. These checks do
not mathematically establish semantic entailment. A label-blind review of the
three-row smoke output is required before the full run. The subset is the first
canonical-ID-sorted example of each task; its selection does not use labels.
The review must compare claims to hyp alone, including ambiguity and qualifiers.
No smoke output exists yet; semantic quality has not been verified.

At most three attempts for invalid row outputs; empty valid responses immediately
fall back to the complete hypothesis. Authentication, model identity, service and
transport failures stop with BLOCKED_DECOMPOSER_API; they do not generate bulk
fallbacks. Persistent cache identity includes the model, prompt, schema, version,
task and hypothesis. Successful outputs and row fallbacks are cached immediately.
Temperature zero does not guarantee bit-identical provider outputs; the cache
preserves exact returned outputs for reuse.

The structured response format follows [official OpenAI documentation](https://developers.openai.com/api/docs/guides/structured-outputs).

## Fixed features

E9-A appends exactly these eight columns after the baseline: claim_count,
claim_entailment_mean, claim_entailment_min, claim_contradiction_mean,
claim_contradiction_max, claim_neutral_mean, claim_unsupported_ratio,
claim_min_entailment_contradiction_margin. Total: 44.

Use the existing E6-v2 backend for
MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli at revision
b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7, local CPU float32, batch size two,
longest-first truncation at 512 tokens, with truncation audits retained locally.
Premise: tgt for DM/MT, src for PG. Hypothesis: individual claim.
Unsupported means argmax(entailment, neutral, contradiction) is not entailment;
ties follow that fixed order. Margin is min(entailment - contradiction).

E9-B starts only after E9-A completes. Before loading
bespokelabs/Bespoke-MiniCheck-7B, verify dependencies, available hardware and VRAM,
the exact checkpoint and official inference interface. If unsafe, stop E9-B with
BLOCKED_MINICHECK. Do not substitute, quantize or redesign to accommodate OOM.
This preflight and model-specific adapter are deferred, not claimed complete.

E9-B appends minicheck_support_mean, minicheck_support_min,
minicheck_support_max, minicheck_support_std (population std, ddof=0), and
minicheck_unsupported_ratio (support probability strictly below 0.5). Total: 49.
The document uses the same task-specific reference as E9-A. Retain raw claim
support probabilities locally. Reuse all 44 E9-A values exactly.

## Evaluation and selection

Report overall, per-task and per-fold correct counts, accuracy and Spearman.
Paired comparisons use corrections, regressions, net change, exact two-sided
McNemar (binomial) test and 10,000 paired bootstrap resamples with default_rng(42).
The 95% percentile interval measures the difference in accuracy, not separate
unpaired intervals. Statistics do not guide tuning.

Select by OOF accuracy, then Spearman. No numerical definition of 'meaningful'
secondary advantage was supplied; retain raw secondary scores for review rather
than invent a post-result threshold. Exact ties prefer E9-A. No winner is selected
while variants are incomplete. Stop after development reporting; no official test.

## Execution and publication

Use the frozen shroom_ensemble Python 3.11.9 environment recorded in the config.
Run scripts with -B to avoid writing bytecode into historical directories.

1. scripts/prepare.py verifies and creates immutable preparation artifacts (already run).
2. tests/test_e9.py runs synthetic offline tests.
3. After credentials are available, scripts/claim_runner.py --run-api-calls --mode smoke.
4. Review hypothesis/claims only; save local claims/smoke_review.json with status PASS
   and a cache_hashes mapping from the three canonical IDs to reviewed cache hashes.
5. scripts/claim_runner.py --run-api-calls --mode full, then scripts/nli_features.py.
6. scripts/evaluate.py --variant E9-A. E9-B integration/preflight follows only then.

Scripts never accept arbitrary dataset paths. Protected CSV/JSONL data and all
claims/features are ignored. Publishable preparation is limited to scripts, tests,
configuration, hashes, aggregate metrics and reports, subject to user review.
Nothing is staged, committed or pushed by these scripts.
