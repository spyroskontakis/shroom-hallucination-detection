# E11-E: synthetic supervision plus the frozen E11-D contrastive objective

One fixed ablation: E11-C's exact two-stage pipeline and prepared fold subsets, with E11-D's unchanged cosine embedding loss in **both stages**. Five independent fold jobs perform one synthetic epoch followed by five human epochs, for ten model fits. There is no configuration search, threshold tuning or extra smoke fit.

`contrastive.py` is a byte-identical copy of E11-D. The total loss is weighted cross-entropy plus 0.1 × mean[(1−y)(1−cos(a,b)) + y·max(0,cos(a,b))], where y=1 denotes hallucination. Margin zero, no temperature. Final-layer representations are mean pooled separately for the two original tokenizer sequences; special/padding tokens are excluded, textual prefixes retained. Cosine uses L2 normalization with eps=1e-8. Both representations share the original cross-encoder context; there is no new projection or independent encoder pass.

## Reproducibility

- `prepare.py` replays the original definitive teacher outcomes, homogeneous export, duplicate/conflict removal and fold leakage exclusions without writing prior experiments. It requires exact E11-C prepared bytes, reconstructs all four authoritative baselines and verifies sequence masks. `--freeze` requires passing pretraining tests before sealing the audit/runtime manifest.
- `E11E_TRAINING_PROTOCOL.json` contains the complete inherited Stage-1/Stage-2 configuration and frozen loss definition. Synthetic sizes are 11,787 / 11,791 / 11,795 / 11,787 / 11,790. All 109 uncertain outcomes and four Azure judgments remain excluded.
- `train_stages.py` is a narrow modification of E11-C. Stage 2 initializes from its own fold's Stage-1 weights and resets the optimizer/scheduler exactly as E11-C does.
- `modal_training.py` uploads only explicitly prepared stage files and the pinned model, validates runtime hashes, disables retries and refuses duplicate local launches. Checkpoints persist on the dedicated volume after each stage.
- `verify_saved_checkpoints.py` independently rehashes all checkpoint files and verifies the five initialization chains using CPU only.
- `evaluate.py` invokes the unchanged E11-A metric function and rejects wrong folds/protocols, incomplete/duplicate IDs, invalid probabilities or class collapse. Spearman uses gold p(Hallucination).
- `run_tests.py` runs prior E11 and new offline tests; `--final` also requires completed returns with zero skips.
- `private/` contains gitignored prepared data, row-level OOF predictions, returns and logs. `E11E_MANIFEST.json` hashes final artifacts; `SHA256SUMS.txt` includes the manifest hash without self-reference.

Modal volume: `shroom-e11e-fixed-two-stage-contrastive-results`.
Checkpoint path: `/results/e11e-fixed-001/fold_N/stage_S/final_checkpoint`.

If interrupted, inspect existing app jobs and volume outputs before doing anything else. Do not relaunch completed fits. No teacher clients, official-test inputs or E11-F work are part of this experiment.
