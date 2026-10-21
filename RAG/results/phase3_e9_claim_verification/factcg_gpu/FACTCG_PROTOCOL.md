# Frozen E10: FactCG

Prepared before any E10 score or performance observation. No tuning or E10-v2.

## Population and model input

Exactly 561 canonical human development/trial rows: 493 development_model_agnostic
and 68 trial, in the frozen E6-v3 order. The whole original hypothesis is the claim.
DM and MT use tgt; PG uses src. Export only canonical_id, task, whole_hypothesis,
reference_text. The model sees only reference and hypothesis in the official template.
IDs and tasks are transport/provenance fields, not added to the model prompt.
No labels, target probabilities, predictions, definitions, retrieval or official test data.
No decomposition and no use of E9 claims as E10 claims.

## Released inference semantics

Paper: [FactCG: Enhancing Fact Checkers with Graph-Based Multi-Hop Data, NAACL 2025](https://arxiv.org/abs/2501.17144).
Checkpoint: [yaxili96/FactCG-DeBERTa-v3-Large](https://huggingface.co/yaxili96/FactCG-DeBERTa-v3-Large/tree/0430e3509dbd28d2dff7a117c0eae25359ff3e80),
revision `0430e3509dbd28d2dff7a117c0eae25359ff3e80`.
Official source: [derenlei/FactCG](https://github.com/derenlei/FactCG/tree/41f185413312ed9b3904ec03963fe899693498e0),
commit `41f185413312ed9b3904ec03963fe899693498e0`.

Use the HF safetensors classifier, num_labels=2, single_label_classification,
ignore_mismatched_sizes=False, eval mode, float32, CUDA, no autocast or quantization.
Torch 2.2.1 is the release's recommended version; Transformers 4.38.1 matches the
checkpoint configuration. Use a separate environment from MiniCheck's Torch 2.4.0.

The lightweight adapter mirrors the official HF branch without importing Lightning
or any training code. Reference sentences are grouped using NLTK word counts up to
550 per chunk, preserving upstream newline joining and oversized-sentence behavior.
Each reference chunk is combined with the complete hypothesis using the exact
INSTRUCTION_TEMPLATE from upstream/utils.py. No hypothesis splitting occurs.
The fast tokenizer uses pad_token=eos_token, max_length=2048, truncation=only_first,
padding=longest. This is one formatted string, not a generic NLI text-pair shortcut.
Tokenization errors block/fail rather than switching to the upstream exception
fallback. Truncation counts are recorded, not used to select a different configuration.

Support = softmax(logits)[1], with no temperature scaling, then max across reference
chunks. Batch size is frozen at 1 for inference; it is not optimized after results.
Class index 1 is established by the official HF inference branch, not guessed from
generic LABEL_0/LABEL_1 names. No FactCG classification threshold is used.
TF32 matmul is disabled. Seed 42 is fixed. CUDA unavailability blocks; no CPU fallback.
Bundled English NLTK tables and reference source files are hashed in the manifest.

## Feature import

Exactly one added column: factcg_support_probability. No thresholded labels or other
derived features. E10 has exactly 37 features: the unchanged 36 E6-v3 features plus
the raw FactCG support probability. The importer checks all 561 IDs exactly once,
finite scores in [0,1], exact model/revision/settings, input-row hashes, output hash,
successful GPU report, local canonical source hash and baseline hash. It preserves
every baseline CSV cell and row order. Missing/duplicate/unknown rows are rejected.

## One future evaluation

Preparation runs zero Random Forest fits. After verified GPU scores are returned,
evaluate_e10.py --run-rf executes exactly five RandomForestRegressor fits using the
unchanged five locked folds and all E6-v3 hyperparameters from the frozen manifest.
The target remains p_hallucination. Only the training fold target is passed to fit.
No preprocessing, folds, thresholds or RF hyperparameters are tuned.
OOF predictions are clipped to [0,1]; binary predictions use >=0.5. Spearman uses
probabilities rounded to 12 decimal places, matching E6-v3. All 561 rows get one OOF prediction.

Report overall correct/561, accuracy, Spearman, DM/MT/PG, each fold, corrections,
regressions and net correct versus saved E6-v3 OOF predictions. Reuse the exact paired
McNemar binomial test and paired bootstrap accuracy-difference CI: 10,000 draws,
default_rng(42), 2.5/97.5 percentiles. No baseline refit.
Selection follows the project's frozen priority: accuracy first, then Spearman for
an exact accuracy tie; exact tie or worse retains E6-v3 (474/561,
accuracy 0.8449197860962567, Spearman 0.7816945786401444).
An exclusive evaluation directory and fit markers prohibit reruns, including after
partial failure; do not delete them to rerun or create E10-v2 after seeing results.

## Limits

Local source/tokenization/contract checks do not certify actual Linux CUDA execution.
Numerical bit equality across GPU architectures is not guaranteed. The remote run
must pass preflight, load the exact model and complete validation. No official
1,500-row test access, commit or push is authorized by this preparation.
