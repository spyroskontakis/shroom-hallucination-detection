# E11-A frozen training protocol

Protocol content SHA256: `518c2df610a1483472b94e8baf3c0c4b277275f351e7448822e35d9dc871772d`. Frozen before any E11-A training or OOF result.

E11-A tests direct, human-only adaptation of the pinned MoritzLaurer DeBERTa-v3-large encoder to the binary SHROOM label. It is separate from the frozen zero-yield E11-B detector-teacher experiment.

Canonical input: `codex/canonical_human_development_manifest.csv` (SHA256 `754b66c6c4eca2e92902d0408db4854e922d7dfb396953a0cc043c5477bd6a9b`), 561 unique samples: DM 211, MT 216, PG 134. Locked folds: `codex/canonical_fold_assignments.csv` (SHA256 `f5a5964923806a23dd34a8bcc137f3cf489437e033d645e9d0845bf40792eb5d`), IDs 1–5, sizes 113/112/112/112/112. Labels: 0=Not Hallucination, 1=Hallucination.

Exact tokenizer pair: sequence A is `TASK: {task}\nREFERENCE:\n{reference}`; sequence B is `HYPOTHESIS:\n{hyp}`. The backslash-n markers here denote literal newline characters. Reference is `tgt` for DM/MT and `src` for PG. The complete original hypothesis is used. Tokenization adds standard model special tokens, truncates longest-first to 512, and pads dynamically per batch.

Base: `MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli@b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7` from the hash-verified local safetensors mirror. The 3-way NLI classifier head is replaced by a seeded two-class head; output class 1 is hallucination.

Training: AdamW; learning rate 1e-5; weight decay 0.01; five fixed epochs; microbatch 8; gradient accumulation 2 (effective batch 16); evaluation batch 16; warmup ratio 0.1 with ceil rounding; linear decay; max gradient norm 1.0; seed 42; BF16 autocast on A100; no quantization, oversampling, early stopping or sweep. Save the final epoch checkpoint only.

Loss is weighted cross-entropy. For each fold, `weight_c = N_train / (2 * N_class_c)` using only its training labels. No held-out label contributes to model fitting, weighting, scheduling or checkpoint selection.

| Held-out fold | Train rows | Train class 0 | Train class 1 | Held-out rows | Weight 0 | Weight 1 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 448 | 246 | 202 | 113 | 0.910569106 | 1.108910891 |
| 2 | 449 | 246 | 203 | 112 | 0.912601626 | 1.105911330 |
| 3 | 449 | 245 | 204 | 112 | 0.916326531 | 1.100490196 |
| 4 | 449 | 245 | 204 | 112 | 0.916326531 | 1.100490196 |
| 5 | 449 | 246 | 203 | 112 | 0.912601626 | 1.105911330 |

For each fold, train on all other canonical folds, then predict the held-out fold with the final checkpoint. `p(H)` is softmax class 1 and the fixed classification threshold is 0.50 (`>=` predicts 1). The eventual OOF union must have 561 unique IDs. No held-out-based checkpoint choice or hyperparameter selection is permitted.

The separate A100 smoke uses 32 fold-1 training rows, two optimizer steps and one checkpoint write. It produces no held-out predictions or E11-A score. It must pass before any full fold run is allowed. This preparation does not launch that smoke.

Official test, unlabeled/pseudo-labeled rows, detector scores, RF outputs, MPNet, BERTScore, claim decomposition and external definitions are prohibited. E11-B remains unchanged.
