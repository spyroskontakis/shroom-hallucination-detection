# E11 data and protocol audit — development only

**Status: AUDIT COMPLETE; E11 strategy and input format are not frozen.** No model was trained, no pseudo-labels or synthetic examples were generated, no API or Modal job ran, and the official 1,500-example SHROOM test files were not opened. The companion `E11_DATA_MANIFEST.json` records absolute paths, SHA-256 hashes, schemas, counts, and overlap results for every inspected candidate file. Counts below are from local read-only inspection unless explicitly marked historical metadata.

## 1. Frozen 561-row development population

The exact population used by E6-v3, E9, and E10 is canonical_human_development_manifest.csv (row-level artifact supplied separately where permitted; see repository docs/DATA_ACCESS.md), SHA-256 `754b66c6c4eca2e92902d0408db4854e922d7dfb396953a0cc043c5477bd6a9b`. It contains 561 rows and 561 distinct `HDEV_...` canonical IDs: 493 retained model-agnostic development rows and 68 trial rows. The raw 80 trial plus 499 model-agnostic development rows are **not** 579 independent training examples: prior canonical preparation removed trial/development duplicates, an internally conflicting development duplicate group, and four development rows with exact official-test overlap (the latter fact comes only from the existing preparation audit). The original preparation scripts and artifacts were not rerun.

| Task | Total | Hallucination (`label_bin=1`) | Not Hallucination (`label_bin=0`) |
|---|---:|---:|---:|
| DM | 211 | 107 | 104 |
| MT | 216 | 97 | 119 |
| PG | 134 | 50 | 84 |
| **Total** | **561** | **254** | **307** |

The exact locked file is canonical_fold_assignments.csv (full historical schema supplied separately where permitted; the public ID/fold projection is in manifests/canonical_fold_assignments.public.csv), SHA-256 `f5a5964923806a23dd34a8bcc137f3cf489437e033d645e9d0845bf40792eb5d`. Its 561 IDs match the canonical manifest in order and its fold IDs are exactly 1–5. [`codex/canonical_fold_generation_metadata.json`](../../../codex/canonical_fold_generation_metadata.json) records the original stratification by task and binary label, shuffle, and seed 42. No folds were created or modified.

| Fold | Total | DM | MT | PG |
|---|---:|---:|---:|---:|
| 1 | 113 | 43 | 44 | 26 |
| 2 | 112 | 42 | 43 | 27 |
| 3 | 112 | 42 | 43 | 27 |
| 4 | 112 | 42 | 43 | 27 |
| 5 | 112 | 42 | 43 | 27 |

Canonical fields are `canonical_id`, `source_split`, `original_row_index`, `task`, `src`, `tgt`, `hyp`, `label`, `label_bin`, `p_hallucination`, `labels`, `model`, `ref`, `exact_text_key`, `source_pair_key`, and `task_reference_key`. `src`, `tgt`, and `hyp` are nonempty for every canonical DM/MT/PG row. The label fields are outcomes, never text-model inputs. `model` is blank in every canonical DM and MT row and in 125/134 PG rows, so it is not a reliable E11 input. Raw `ref` is `tgt` for DM and `either` for MT/PG; the **frozen E6/E9/E10 operational reference policy** is `tgt` for DM and MT, `src` for PG. These are distinct facts and should not be conflated.

Per the supplied SHROOM trial/development READMEs, DM `src` is the context with a `<define>`-marked term, `tgt` the intended definition, and `hyp` the generated definition. MT `src` is the text to translate, `tgt` the gold translation, and `hyp` the generated translation. PG `src` is the sentence to paraphrase, `tgt` an intended paraphrase when supplied, and `hyp` the generated paraphrase. The unlabeled model-agnostic PG split has an empty `tgt` in all 10,000 rows, so E11 cannot require PG target text for auxiliary training.

## 2. Other SHROOM data and historical augmentation

Primary paths below are relative to ``; the JSON manifest contains their full absolute paths and full column lists. `data/` and `codex/data/` copies and CSV/JSONL representations with identical rows are aliases, not additional examples.

| Candidate | Path | Rows; unique explicit IDs | DM / MT / PG | Labels | Exact canonical overlap |
|---|---|---|---|---|---:|
| Raw trial | `Trial/SHROOM_trial-v1.1/trial-v1.json` | 80; no ID field | 36 / 35 / 9 | Human | 80 rows (12 duplicate development text keys) |
| Raw model-agnostic development | `Dev/SHROOM_dev-v2/val.model-agnostic.json` | 499; no ID field | 187 / 187 / 125 | Human | 493 rows |
| Raw model-aware development | `Dev/SHROOM_dev-v2/val.model-aware.v2.json` | 501; no ID field | 188 / 188 / 125 | Human; different track | 0 |
| Unlabeled model-agnostic training | `Unlabeled train/SHROOM_unlabeled-training-data-v2/train.model-agnostic.json` | 30,000; no ID field | 10,000 / 10,000 / 10,000 | **None** | **0** |
| Unlabeled model-aware training | `Unlabeled train/SHROOM_unlabeled-training-data-v2/train.model-aware.v2.json` | 30,000; no ID field | 10,000 / 10,000 / 10,000 | **None** | **0** |
| Historical balanced synthetic | `codex/data/6. Feature Extraction on Augmented Training Data/filtered_synthetic_data_balanced.csv` | 518; 390 unique *source* `sample_id` values | 99 / 228 / 191 | Generated/heuristic, 259/259 | 0 |
| Canonical E4 diagnostic synthetic | `codex/canonical_synthetic_diagnostic_manifest.csv` | 505 unique `synthetic_id`; 380 source `sample_id` values | 97 / 218 / 190 | Generated/heuristic, 252/253 | 0 |
| Historical combined trial + synthetic | `codex/data/6. Feature Extraction on Augmented Training Data/augmented_training_data.csv` | 598; no ID field | 135 / 263 / 200 | Mixed human/generated | **80** |

The raw labeled files have `hyp`, `ref`, `src`, `tgt`, `model`, `task`, `labels`, `label`, and `p(Hallucination)`; the unlabeled files have only `hyp`, `tgt`, `src`, `ref`, `task`, and `model`. Neither supposedly unlabeled file contains any `label`, `labels`, `label_bin`, `p(Hallucination)`, or `p_hallucination` key. The model-agnostic unlabeled `model` is empty in all 30,000 rows. Model-aware development is a separate evaluation track and cannot be silently appended to this model-agnostic 561-row protocol.

Historical augmentation is a *pipeline*, not independent corpora to concatenate. The `5. Augmentation` subdirectories for 5, 20, 50, and 200 sampled sources per task contain raw generated, filtered, balanced, and combined-with-trial stages; `6. Feature Extraction on Augmented Training Data` repeats the final 200-source stages. Raw generated stages have respectively 30, 120, 300, and 1,200 rows; filtered stages 20, 75, 198, and 763; balanced stages 18, 62, 146, and 518; combined stages 98, 142, 226, and 598. Each candidate path, task distribution, ID uniqueness, fields, labels, hash, and canonical overlap appears separately in the JSON manifest. The 518-row final balanced CSV has SHA-256 `51ba397e280070496de074bca0b3ec895306f82aeecf8980b3f7e74e83a4a971`; the 505-row canonical diagnostic manifest has SHA-256 `a131a7b2fde22cd65b90729baee1251c501093467039b3fcd92cff75ac63cf90`.

No standalone historical pseudo-label corpus was found in the scoped development/training paths. Historical OOF and ablation prediction files exist, including test-derived artifacts. They are **predictions, not ground truth**, and were not opened or admitted as E11 labels. Historical synthetic generation/filtering and ratio experiments have prior test-exposure caveats; the synthetic labels are not human SHROOM annotations.

## 3. Leakage findings and fold isolation

Duplicate and overlap comparisons normalize text with Unicode NFC and collapsed whitespace. A full sample key is `(task, src, tgt, hyp)`; a source/target pair is `(task, src, tgt)`. These are exact/obvious-duplicate checks, not semantic near-duplicate detection.

| Dataset | Unique hypotheses | Extra duplicate-hypothesis rows | Extra duplicate source/target-pair rows | Extra duplicate full-sample rows | Full-sample overlap with canonical |
|---|---:|---:|---:|---:|---:|
| Canonical human 561 | 555 | 6 | 0 | 0 | self |
| Unlabeled model-agnostic 30,000 | 27,587 | 2,413 | 2,213 | 1,351 | 0 |
| Unlabeled model-aware 30,000 | 29,360 | 640 | 0 | 0 | 0 |
| Historical balanced synthetic 518 | 518 | 0 | 128 | 0 | 0 |
| Canonical diagnostic synthetic 505 | 505 | 0 | 125 | 0 | 0 |

The model-agnostic unlabeled split shares 34 hypothesis rows, 80 `(task,src,tgt)` pair rows, and 180 task-specific reference rows with the canonical 561, despite zero exact full-sample overlap. The 518-row balanced synthetic file shares one source/target pair with the canonical set. The 598-row combined historical file contains 80 human trial rows that match canonical text exactly. Raw unlabeled splits have **no explicit IDs**; `sample_id` in historical synthetic data is an index into the unlabeled model-agnostic source file, not a unique synthetic-example ID (518 rows use 390 source IDs; 505 canonical synthetic rows use 380). Thus matching numeric source IDs do not indicate an HDEV ID collision, while repeated source IDs do indicate related generated examples. No current official-test ID overlap claim is possible without opening a safe test-ID-only inventory, which was not found.

Within the 561 canonical rows, five repeated-hypothesis groups and five repeated task-reference groups exist. Three groups of each type cross locked folds; there are **no** duplicate full samples or `(task,src,tgt)` pairs. For a future E11 fold, keeping validation membership fixed but removing training rows with an identical validation hypothesis or task reference leaves 445, 448, 449, 448, and 445 human training rows for folds 1–5 respectively, versus 448/449 before this purge. This is a proposed fold-specific leakage guard, **not an implemented or frozen fold change**. For auxiliary unlabeled data, exact/hypothesis/pair/reference filtering against each validation fold leaves 28,575–28,627 unique full samples, or 27,716–27,766 unique source/target pairs if restricted to one per pair. More subtle paraphrases and shared provenance remain unmeasured.

Existing [`codex/evaluation_protocol_decision.md`](../../../codex/evaluation_protocol_decision.md) reports that canonical preparation excluded four exact development/test overlaps; an older metadata audit reports five balanced-synthetic/test source-pair overlaps and zero exact balanced-synthetic/test full-sample overlaps. Those are **historical metadata only**, not new test checks. Neither document establishes current test ID disjointness for the unlabeled corpora. No official test row or test-derived feature/prediction content was read during E11.

## 4. Existing model/runtime infrastructure and feasibility

| Component | Existing implementation and frozen identity | Existing use |
|---|---|---|
| MoritzLaurer DeBERTa-v3-large NLI | [`RAG/results/rag_e6_v2/scripts/nli_backend.py`](../rag_e6_v2/scripts/nli_backend.py), model `MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli` at `b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7`; local safetensors and config under `rag_e6_v2/model/` | CPU FP32 inference, 3 NLI logits, paired tokenizer inputs, 512-token longest-first truncation, batch 2. |
| FactCG | [`factcg_gpu/factcg_backend.py`](../phase3_e9_claim_verification/factcg_gpu/factcg_backend.py), `yaxili96/FactCG-DeBERTa-v3-Large` at `0430e3509dbd28d2dff7a117c0eae25359ff3e80` | Frozen CUDA FP32 support scoring; not a task-adapted E11 training implementation. |
| HHEM | [`rag_e6_v3/scripts/hhem_backend.py`](../rag_e6_v3/scripts/hhem_backend.py), `vectara/hallucination_evaluation_model` at `58383384656cbaec2949a75a41f20e891e90a73b` | CPU FP32 reference/hypothesis consistency inference. |
| MiniCheck | [`minicheck_gpu/run_minicheck_gpu.py`](../phase3_e9_claim_verification/minicheck_gpu/run_minicheck_gpu.py), `bespokelabs/Bespoke-MiniCheck-7B` at `1ed7786bcda3fa1dc35f7c4ed9e3f36b785d33b8` | Frozen Linux CUDA BF16/vLLM claim scoring. |
| E6-v3/locked CV | [`rag_e6_v3/scripts/evaluate_v3.py`](../rag_e6_v3/scripts/evaluate_v3.py), canonical_fold_assignments.csv (full historical schema supplied separately where permitted; the public ID/fold projection is in manifests/canonical_fold_assignments.public.csv) | Five saved development folds; 36-feature RF baseline. E9/E10 inherited this fold and metric setup. |

The pinned MoritzLaurer config specifies 24 layers, hidden size 1,024, 16 heads, vocabulary 128,100, and maximum positional embeddings 512; its local safetensors file is about 870 MB in FP16. The observed `phase3-003` device was an **NVIDIA A100-SXM4-80GB**, compute capability 8.0, CUDA 12.1. MiniCheck's remote BF16 preflight passed. Thus **full fine-tuning DeBERTa-v3-large at 512 tokens is hardware-feasible on that A100**, subject to a later training dry run and memory measurement. Approximate model/gradient/FP32-master/Adam state storage is ~7–10 GiB before activations and workspace; a conservative planning envelope is ~20–45 GiB with 512-token microbatches of roughly 4–16, depending on padding, optimizer, checkpointing, and implementation. Gradient accumulation may be needed for an effective batch of 16–64. These are estimates, not measured training limits; long references and truncation need a future input-length audit.

The frozen local evaluation environment is Python 3.11.9 with **CPU-only** torch 2.11.0 and Transformers 5.5.4; `accelerate`, `datasets`, and `peft` were not detected there. The successful remote GPU environments are frozen **inference** environments, not a validated training setup. E11 would require a separate CUDA training environment and new output checkpoint, leaving all E6/E9/E10 packages and artifacts untouched. Replacing the 3-way NLI classifier head with an E11 hallucination objective/loss remains a protocol decision, not an action taken here.

## 5. Unfrozen strategies and proposed input format

**A — human training folds only.** Each locked fold has 448 or 449 labeled training rows, or 445–449 after the proposed exact hypothesis/reference purge. It adds zero auxiliary examples, five independent fold-specific fine-tunes, and the least pseudo-label/generation risk. The small sample size makes overfitting a material concern and does not guarantee improvement over E10.

**B — human folds plus pseudo-labeled unlabeled training data.** The model-agnostic unlabeled pool has 30,000 rows, 28,649 unique exact samples, and 27,787 unique source/target pairs. After fold-specific validation-text filtering, at most 28,575–28,627 unique exact rows (or 27,716–27,766 one-per-pair rows) are available *to attempt labeling* for each fold; the number of reliable accepted pseudo-labels is unknown until a separately frozen teacher/quality rule is audited. A fold-specific teacher may see only that fold's human training labels and permitted task/reference/hypothesis text; an unchanged external pretrained teacher may see the filtered unlabeled text but no canonical labels. A teacher trained on **all** 561 labels, or on E10's pooled development predictions, would leak validation information. Duplicate source groups, shared hypotheses/references, teacher errors, and model-aware/domain mixing are main risks. Teacher inference over up to ~30,000 rows per fold plus five DeBERTa training runs could dominate GPU time/cost; no pseudo-labels were generated.

**C — human folds plus controlled synthetic examples.** The available 505 canonical diagnostic examples are a concrete historical scale (505 distinct synthetic IDs from 380 unlabeled source IDs); their labels are generated/heuristic and their prior test-exposed pipeline makes them unsuitable to assume as clean human supervision. A fresh, fold-isolated plan could draw, for example, 500 eligible unlabeled source pairs and request up to two variants each (~1,000 candidates per fold **before** filtering), but this is an estimate, not a frozen quota or generated dataset. The generator may see only filtered, label-free task/source/target/hypothesis text from the allowed fold-specific pool and a fixed generation instruction; it must not see any development labels, validation texts, official test content, OOF predictions, or post-result diagnostics. Keep all siblings of one source row in one training-only group and filter against each validation fold. Generator/API cost, review, filtering, and five training runs are additional costs; exact yield is unknown.

**Provisional recommendation for a later freeze: A** as the first E11 task-adaptation comparison, with the per-fold duplicate purge explicitly decided and documented before training. Its cleanest attribution is valuable given the 561-label limit and historical synthetic/test-exposure risk. B and C remain legitimate *options* but need a separate teacher/generator, acceptance, grouping, and cost protocol before they could be frozen. This recommendation is **not** a strategy selection or implementation.

**Proposed, not frozen, DeBERTa pair input:** use the existing two-sequence tokenizer interface. Sequence A is task-aware context/reference; sequence B is the complete original hypothesis. Literal bracketed tags below are text delimiters, not newly installed special tokens:

```text
DM sequence A: [TASK] DM\n[SOURCE] {src}\n[REFERENCE:TARGET] {tgt}
MT sequence A: [TASK] MT\n[SOURCE] {src}\n[REFERENCE:TARGET] {tgt}
PG sequence A: [TASK] PG\n[REFERENCE:SOURCE] {src}
All sequence B: [HYPOTHESIS] {hyp}
```

This uses only fields actually present in the corresponding canonical and model-agnostic unlabeled rows, respects the existing DM/MT-target and PG-source reference policy, and never inserts `label`, `labels`, `label_bin`, `p_hallucination`, `model`, fold ID, predictions, or external definitions into the model text. Whether to retain DM/MT `src`, the exact truncation policy, objective, maximum length, and handling of repeated references must be frozen before any training. The original `hyp` must remain whole.

## 6. Reproducibility and stop point

Key SHA-256 values: canonical `754b66c6c4eca2e92902d0408db4854e922d7dfb396953a0cc043c5477bd6a9b`; folds `f5a5964923806a23dd34a8bcc137f3cf489437e033d645e9d0845bf40792eb5d`; unlabeled model-agnostic `dead22eb9b11bbd5bf8e895d01e11ab517a7a7dcebe82f82c6349a3f235d86a3`; unlabeled model-aware `dfe3b6706bb598648e61c3feb667cdd8ab30dd88fc7db98462dfc34927814d54`; historical balanced synthetic `51ba397e280070496de074bca0b3ec895306f82aeecf8980b3f7e74e83a4a971`. The JSON manifest holds all other hashes and the exact per-candidate metadata.

This audit stops before training, pseudo-labeling, synthetic generation, fitting, API calls, Modal GPU execution, or official test access. Existing E6-v3, E9, and E10 files were not changed. No commit or push was made.
