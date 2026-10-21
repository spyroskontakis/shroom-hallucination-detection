# E11-B frozen pseudo-label teacher protocol

**Status:** frozen before any pseudo-label generation, 2026-09-28. This is a static design and validation artifact. No detector inference, logistic-regression fit, DeBERTa training, new-model evaluation, API call, or Modal run was performed here. The official 1,500-example test content was not accessed.

The machine-readable authority is [`E11_TEACHER_PROTOCOL.json`](E11_TEACHER_PROTOCOL.json). Its protocol content SHA256 is `c0645ef01f885ef22b7abaf5634f8a62d66a3e7174cb0d07aa2a47fba425a5ac`. This is SHA256 of UTF-8 canonical JSON **excluding** the self-referential `protocol_sha256` field, using sorted keys, compact separators, Unicode text, and no nonfinite numbers. The companion read-only validator recomputes it.

## Inputs and score meanings

The labeled human pool is `codex/canonical_human_development_manifest.csv`, 561 unique IDs, SHA256 `754b66c6c4eca2e92902d0408db4854e922d7dfb396953a0cc043c5477bd6a9b`. Its `label_bin=1` means hallucination. The exact five locked folds are `codex/canonical_fold_assignments.csv`, SHA256 `f5a5964923806a23dd34a8bcc137f3cf489437e033d645e9d0845bf40792eb5d` (held-out sizes 113, 112, 112, 112, 112). The only pseudo-label candidate source is `Unlabeled train/SHROOM_unlabeled-training-data-v2/train.model-agnostic.json`, SHA256 `dead22eb9b11bbd5bf8e895d01e11ab517a7a7dcebe82f82c6349a3f235d86a3`, 30,000 unlabeled rows and 28,649 unique normalized full samples before fold purge. No model-aware split, augmentation, prior prediction, or official test row is admitted.

The task reference is **DM → `tgt`, MT → `tgt`, PG → `src`**. Every detector sees the complete original `hyp` as a single claim. It receives only sample key, task, chosen reference, and whole hypothesis. The raw source fields are used locally to derive the reference and duplicate keys, not passed as extra detector evidence. No claim decomposition, external definitions, RF predictions, labels, BERTScore, or MPNet enter the teacher.

| Frozen signal | Exact model / revision | Stored meaning and direction |
| --- | --- | --- |
| FactCG | `yaxili96/FactCG-DeBERTa-v3-Large@0430e3509dbd28d2dff7a117c0eae25359ff3e80` | Support probability: class-1 **Yes** softmax for reference → whole hypothesis, maximum across reference chunks. Higher = more support. |
| MiniCheck | `bespokelabs/Bespoke-MiniCheck-7B@1ed7786bcda3fa1dc35f7c4ed9e3f36b785d33b8`; official code commit `00a1ed40715ba11b9718ef251a3b0c493992944e` | Official whole-claim support score: sum of the returned top-5 `yes` token probabilities, maximum over document chunks; **not** renormalized yes/no posterior. Higher = more support. |
| HHEM | `vectara/hallucination_evaluation_model@58383384656cbaec2949a75a41f20e891e90a73b` | Existing `hhem_ref_hyp_consistency`: `sigmoid(single logit)` for reference → whole hypothesis. Higher = more **consistent/supported** by premise; it is not a hallucination probability, and no calibration is claimed. |
| NLI | `MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli@b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7` | Reference premise → whole-hypothesis hypothesis **only**. Softmax class order is entailment, neutral, contradiction. Entailment is support-oriented, contradiction is contradiction-oriented, neutral is neither. Never use hypothesis → reference or definition pairs. |

These orientations are established by the existing frozen implementations: `factcg_backend.py` uses the fixed Yes/No instruction and `softmax(logits)[0,1]`; MiniCheck's pinned runner and official scoring description use yes-token mass; `hhem_backend.py` uses `sigmoid(logits[:,0])` and the E6-v3 results document explains its supported-by-premise direction; `nli_backend.py` asserts the exact ordered `id2label`/`label2id` maps before softmax. The four raw detector numbers are not manually inverted. The logistic regression learns `p(H)` from the human labels.

The existing E10 FactCG score, E6-v3 HHEM `hhem_ref_hyp_consistency`, and E6-v2 NLI `nli2_ref_hyp_{entailment,neutral,contradiction}` can supply the 561 **human** rows if their IDs, input text, model/revision metadata, and frozen hashes are verified at execution time. The NLI names map directly to the teacher's `nli_ref_hyp_*` names; no other NLI feature is used. **E9-B MiniCheck cannot supply the human score:** its 575 scores represent frozen claim units, whereas E11-B requires one whole-hypothesis score per each of the 561 human samples. A future label-blind whole-hypothesis MiniCheck pass is therefore required before fitting any teacher. Do not substitute MiniCheck aggregates or split claims.

## Five teachers and fold isolation

For each locked outer fold, fit **one** `sklearn.linear_model.LogisticRegression(penalty='l2', C=1.0, solver='lbfgs', class_weight='balanced', max_iter=2000, random_state=42)` with the default intercept enabled. Fit on that fold's human-labeled training partition only, after the text-only human training purge described below. The class-1 `predict_proba` output is `p(Hallucination)`. No hyperparameter tuning, feature scaling, score inversion, calibration, or RF stage is allowed.

The input columns, in exact order, are:

1. `factcg_support_probability`
2. `minicheck_support_probability`
3. `hhem_ref_hyp_consistency`
4. `nli_ref_hyp_entailment`
5. `nli_ref_hyp_neutral`
6. `nli_ref_hyp_contradiction`
7. `task_DM`
8. `task_MT`
9. `task_PG`

The task columns are exact 0/1 one-hot indicators. All raw scores must be finite and in `[0,1]`; NLI's three probabilities must sum to 1 within ordinary float tolerance. Reject missing or duplicate IDs. For each unlabeled input, compute the **four frozen detector outputs once**, on the deduplicated pool, and reuse those immutable rows for all five teachers. The pretrained detectors never receive SHROOM labels. This reuse is fold-safe because the later fold-specific teacher fit and pseudo-label assignment are separate from detector inference; no held-out label enters either. Labels of held-out humans must never enter a fold's teacher fit or student training.

## Normalization, purge, acceptance, and balance

Reuse the rule in `codex/canonical_evaluation_data_prep.py::normalize_value/hash_parts` (source SHA256 `d98717c7b56c5f3298b8b99c89eac2687e70e83459f42100a017bacc56d5e8d5`): `None` → empty string; list/dict → JSON with `ensure_ascii=False` and sorted keys; otherwise `str(value)`; Unicode NFC; strip leading/trailing whitespace; collapse every whitespace run to one ASCII space. Preserve case and punctuation. A key is SHA256 of UTF-8 normalized components joined by U+241F. The full sample key uses `(task, src, tgt, hyp)`; hypothesis key uses `(hyp)`; task-reference key uses `(task, reference)`; source-target pair key uses `(task, src, tgt)`.

Deduplicate unlabeled rows on the full sample key and keep the lowest original row index. For a given fold, compare candidates to **held-out human text only** and purge any match on full sample, hypothesis, task-reference, or task+source+target pair. This adds source-target pair protection beyond the required three comparisons. Also remove a human training row if its hypothesis or task-reference matches a held-out human row; preserve held-out rows unchanged. Neither purge uses held-out labels. The static validator finds 28,649 deduplicated candidates, then fold-specific candidate counts **28,575 / 28,623 / 28,627 / 28,611 / 28,615**, and human training counts **445 / 448 / 449 / 448 / 445** after text purge. These are eligibility counts, **not** pseudo-label yields.

On remaining unlabeled candidates, accept `label=1` only when **`p(H) >= 0.95`** and `label=0` only when **`p(H) <= 0.05`**. Discard the open middle interval `0.05 < p(H) < 0.95`. Never change these thresholds after observing development results.

Balance separately for DM, MT, and PG. For each task, let `n_keep = min(number of accepted label-1 rows, number of accepted label-0 rows, 4000)`. Retain exactly `n_keep` label-1 rows with highest `p(H)` and `n_keep` label-0 rows with lowest `p(H)`; break equal-probability ties by ascending full sample key. This yields **at most 24,000 pseudo-labeled rows per fold** and permits zero. No minimum yield, resampling, or threshold relaxation is allowed.

Keep `HUMAN` and `PSEUDO` rows distinct. Every future student-training row must carry sample key, task, source type, fold, label, teacher probability for pseudo rows (null/not applicable for human rows), and provenance. Human labels are never overwritten. Provenance for pseudo rows includes the fold teacher, raw-score artifact hashes, detector model/revision pins, and this protocol digest.

## Static feasibility and compute estimate

The NLI `model.safetensors` (870,182,606 bytes) and HHEM `pytorch_model.bin` (737,761,269 bytes), tokenizer/config files, and their frozen implementations are present locally. FactCG and MiniCheck implementations and pinned manifests are present, but their **checkpoint weights are not in these package directories**. Their exact revisions were nevertheless loaded and scored successfully on the A100-80GB in the recorded `phase3-003` runs; a future run must provision the pinned weights again and verify the resolved revision. The present Windows Python is CPU-only; GPU feasibility for all four together is not established by this static check. Running MiniCheck's frozen vLLM/BF16 path requires the compatible Linux CUDA environment recorded in its package. NLI and HHEM existing CPU backends would need execution wrappers for GPU use; altering frozen E6 artifacts is forbidden.

For **28,649** unique unlabeled rows, straightforward linear projection of actual A100-80GB `phase3-003` end-to-end timings gives about **1.67 h MiniCheck** from 120.695 s/575 claim units and **0.62 h FactCG** from 43.805 s/561 whole-hypothesis pairs. These include startup/model load, so scaling them is only a planning approximation. MiniCheck already batches 16 claims; FactCG's frozen path scores one chunk at a time. The available NLI/HHEM benchmarks were on CPU, **not A100**: 1,315 NLI pairs in 1,020.705 s imply about **6.18 CPU-h**, and 754 HHEM pairs in 248.662 s imply about **2.62 CPU-h** at 28,649 pairs. Both pair models can batch on A100, but no project A100 timing exists for them; do not present the CPU projections as GPU measurements.

Budget **roughly 3–11 A100 GPU-hours** for one pass over deduplicated unlabeled inputs, with the lower end dependent on successful batching/acceleration of NLI and HHEM, and allow extra time for the 561 whole-hypothesis human MiniCheck scores, checkpoint downloads, startup, validation, and long-reference variation. This is a planning range, not a guaranteed bound or benchmark. Currency cost is **(billable A100 hours × the provider's rate at execution)** plus any separately billed CPU/RAM/storage; no verified price or billing record is available locally, so a dollar amount would be invented. No Modal job was started.

## Future artifacts and immutable decision

The future run should create `teacher_inputs/` (label-blind detector inputs and human training maps), `raw_detector_scores/` (one deduplicated unlabeled score row per sample plus label-blind human scores), and `fold_1/` through `fold_5/`. Each fold directory must record the held-out ID digest, text-purge counts, ambiguous/rejected count, confidence-accepted counts, balancing discards, kept DM/MT/PG × class counts, accepted pseudo rows with probability and provenance, teacher coefficients/intercept, **training-data-only** teacher diagnostics, software versions, and input/output SHA256 hashes. No held-out accuracy or label-based candidate selection is reported during pseudo-label generation.

After pseudo-label generation starts, the pinned detectors, input sources, locked folds, normalization, purge rules, teacher configuration, confidence thresholds, task/class balancing, and score semantics are immutable. E11 development Accuracy cannot be used to revise them. This protocol does not itself produce any pseudo-labels.

Static verification command from repository root: `python -B RAG/results/phase3_e11_task_adaptation/validate_teacher_protocol.py`. It reads only the three declared data files and existing model/code/report artifacts; it does not fit a model or access the official test.
