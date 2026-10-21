# E6-v4 — Formal protocol amendment 01: pinned BERTScore environment

**Protocol amendment performed before any real-sample E6-v4 feature extraction, model fitting, or evaluation.**

The user authorized this amendment and one fixed E6-v4 execution in the request archived at `execution/user_request.txt`. At amendment time real E6-v4 feature extraction=0, RF fits=0, evaluations=0; no E6-v4 performance score has been observed. The original `E6_V4_PROTOCOL.md` and `config/run_config.json` remain unchanged. This separate amendment supersedes their compatibility stop only after the final synthetic gate passes; it does not change the research design.

## Phase 1 and phase 2: reason and evidence

The original official bert-score 0.3.13 attempt failed before real extraction/evaluation with `builtins.OverflowError: int too big to convert`. The minimal reproducer is `sent_encode(get_tokenizer('microsoft/deberta-large-mnli', use_fast=False), 'a')`, using the unmodified official BERTScore utilities and locally cached pinned checkpoint. In transformers 5.5.4/tokenizers 0.22.2, the undefined tokenizer maximum-length sentinel `1000000000000000019884624838656` was passed into the truncation backend. Padding=False still failed; disabling truncation only as a diagnostic control succeeded. This was a runtime/package compatibility failure, not a methodological result.

The full evidence and official sources are preserved in `compatibility_analysis/E6_V4_COMPATIBILITY_ANALYSIS.md`. An isolated environment with the pins below completed official BERTScore scoring on synthetic pairs and automatically resolved the historical model-ID maximum length to 512. No tokenizer mutation or custom metric was used.

## Phase 3: exact permitted environment change

Encoding interpreter: the existing isolated venv at `compatibility_analysis/env/Scripts/python.exe`, Python **3.11.9**. It uses separately installed **transformers==4.30.2**, **tokenizers==0.13.3**, **huggingface-hub==0.25.2**, the unchanged official **bert-score==0.3.13** wheel in `packages/`, and shared **torch==2.11.0**. The wheel's internal `__version__` is 0.3.12; both values are recorded. Installed package/wheel hashes are preserved by the diagnosis manifest; active dependencies and environment variables are frozen in `execution/run_config.json`.

The venv uses system-site-packages for unchanged shared dependencies; it is an isolated interpreter with three local dependency pins, not a standalone hermetic installation. It is not staged or committed. No new dependencies or model downloads are needed for execution. Temporary writes are confined to `execution/tmp/`. The RF evaluation uses the original `shroom_ensemble` interpreter and unchanged E6-v3 numerical/sklearn dependencies; no baseline or original feature extraction is rerun.

Official API: `bert_score.BERTScorer(model_type='microsoft/deberta-large-mnli', num_layers=None, batch_size=2, nthreads=4, all_layers=False, idf=False, idf_sents=None, device='cpu', lang=None, rescale_with_baseline=False, use_fast_tokenizer=False).score(cands=hyp, refs=reference, batch_size=2)`.

Model and tokenizer revision: **7296194b9009373def4f7c5dad292651e4b5cf4e**, exactly the original E3 checkpoint. Official model2layers selects **18**, with no SHROOM tuning. CPU float32, four intra/inter-op threads, seed 42, no GPU, autocast or training. Official hash string: `microsoft/deberta-large-mnli_L18_no-idf_version=0.3.12(hug_trans=4.30.2)`.

**No manual tokenizer.model_max_length override.** The official transformers 4.30.2 pretrained model-ID mapping supplies 512 including special tokens. The BERTScore package is unmodified, applies its normal internal strip and tokenization, and receives exact saved strings. The official P/R/F1 definition, layer, IDF/rescale and candidate/reference direction do not change. Runtime numerical equivalence with the failed 5.5.4 path is not claimed; the pinned runtime and restored official tokenization behavior are explicitly recorded for reproducibility.

## Unchanged research design and stage gates

- Exactly the frozen 561 canonical IDs and five locked folds, including the established development/trial canonical pool. Reference=tgt for DM/MT, src for PG; candidate=hyp. No definitions enter the seven new features.
- Exact 36 E6-v3 columns in original order and values, plus the same three BERTScore and four structural columns. All structural normalization, regex and negation lexicon remain exactly those in the original `scripts/structure.py` and `config/structure_spec.json`. Total 43; no feature selection.
- Exactly the full frozen E6-v3 RandomForestRegressor configuration; target p_hallucination, clip [0,1], threshold prediction>=0.5, one five-fold OOF evaluation with five RF fits, zero baseline fits. No hyperparameter tuning, router, task-specific model, variant or post-score change.
- A fresh synthetic official BERTScore test in the final pinned environment must pass finite P/R/F1, identity/omission/addition direction checks, number/negation examples, no override and zero network attempts before real extraction.
- Before real extraction, freeze this amendment, the original protocol, compatibility report, package/model provenance, code including evaluator/reporter, input hashes, exact ID list, locked folds, feature schema and RF parameters in a new execution manifest. Retain original configuration files.
- Encoding reads only the frozen label-free A pairs and the 36-column feature matrix. External definitions, labels and OOF predictions are not inputs to the seven-feature extraction. Human targets are joined only for RF/evaluation after feature freeze. Read-only baseline verification remains allowed.
- Run official BERTScore in batches of 2, saved in fixed 16-row chunks solely for progress/cache durability. Audit original and used token lengths separately for reference/hyp. Expected truncation is the official 512-token cap; require used length=min(original length,512) and log all truncated IDs. Any exception, nonfinite value or mismatch stops before RF evaluation. Missing/invalid values are not imputed.
- Freeze the final feature matrix only after all IDs, folds, 36-column numerical equality, seven finite new values and ordered 43-column schema pass. Confirm all protected files unchanged and network logs empty before RF fits.

## Offline execution and reporting

HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1, HF_DATASETS_OFFLINE=1, HF_HUB_DISABLE_TELEMETRY=1, socket network guard with attempt logs. Verify cached model/tokenizer file hashes and local refs/main equals the pinned revision before loading; verify the loaded model commit. A missing asset or any network attempt is a stop condition. No model download is authorized.

Use the original E6-v3 baseline 474/561, accuracy 0.8449197861, Spearman 0.7816945786, validated from saved OOF predictions by ID/fold without fits. Report overall, fold, DM/MT/PG, evidence and DM-only evidence subgroups, corrections/regressions, net accuracy change, exact two-sided McNemar and 10,000 paired row bootstrap resamples using default_rng(42), percentile 2.5/97.5. Spearman follows the original 12-decimal prediction rounding; accuracy uses unrounded scores.

The intervention was selected after error analysis, so all performance findings are **adaptive exploratory development-only** and McNemar/bootstrap are **descriptive exploratory statistics**, not confirmatory evidence. A negative or negligible result ends the experiment without redesign.

The original blocker report is archived byte-for-byte at `execution/E6_V4_RESULTS_PHASE1_ARCHIVE.md` before the authorized update to `E6_V4_RESULTS.md`. The final report distinguishes initial failure, diagnosis, this amendment and actual execution. All prior experimental artifacts and diagnosis remain immutable. No official-test access, synthetic-data edits, retrieval, API/LLM calls, git add/commit/push/tag or other experiment.
