# E11-C fixed two-stage experiment

This directory is isolated from the frozen E11-A and E11-C teacher artifacts.
The sole experimental addition is homogeneous gpt-5.6-sol synthetic supervision.
Azure gpt-5-mini rescue judgments, uncertain answers, and technical failures are
excluded. No GPT/Azure call is made here.

`prepare_training.py` verifies teacher responses and provenance, replays exact
E11-A/E10 metrics, checks the pinned model/tokenizer and locked human folds, and
prepares five synthetic subsets. Duplicate model inputs are removed in frozen
candidate order; all rows in conflicting identical-input groups are excluded.
Per-fold exclusions match normalized, case-folded hypothesis, reference, source,
target, source-pair, or complete text to that fold's human validation rows.
The row-level exclusion maps are private. No held-out labels or scores determine
which synthetic rows survive. Split-scoped row indices are not assumed to be
shared upstream source IDs; unknown semantic ancestry cannot be certified.

The current user instruction to use the full definitive pool after safety
exclusions supersedes the earlier teacher-preparation cap/balancing plan. That
older protocol is preserved unchanged. The new training protocol records this
choice and its own content hash before training.

There are five independent fold jobs. Each initializes the pinned E11-A base
encoder and seeded binary head, trains for one fixed synthetic epoch, saves the
checkpoint, resets optimizer/scheduler/seed, and trains on the identical E11-A
human outer-training rows for five epochs. Human Stage 2 preserves E11-A's
optimizer, learning rate, batches, accumulation, schedule, weighted loss,
BF16 precision, clipping, tokenization, and final-checkpoint selection. Stage 1
uses those same settings with its own class counts and one epoch. There is no
early stopping, tuning, threshold optimization, or contrastive loss.

`train_stages.py` retains E11-A's optimizer/training loop verbatim, tested by source
comparison. `modal_training.py` uses the original dependency lock, one A100-80GB
per fold, and a separate persistent volume. Model fits require a passing saved
pretraining audit. Remote checkpoint hashes and runtime versions are in returned
stage summaries. Ten fits are expected, with no additional smoke training.

`evaluate_training.py` uses the original E11-A `metric` function (Spearman over
probabilities and human p(Hallucination), accuracy at the original 0.5 threshold).
It checks all 561 IDs/folds, checkpoint transfer, finite probabilities, and
training summaries before reporting. E10 uses its existing 12-decimal rounding
convention when replaying the baseline. No significance claim is made.

All prepared rows, returned model outputs, exclusion records and consolidated OOF
predictions live under git-ignored `private/`. Checkpoints remain on Modal volume
`shroom-e11c-fixed-two-stage-results`, prefix `e11c-fixed-001/fold_N/stage_S/`.
Public reports contain aggregate metrics, configuration, provenance and hashes.

Execution used `python -m modal run .../modal_training.py` with
`PYTHONIOENCODING=utf-8` for the Windows console. An initial console encoding
failure created an empty app with zero tasks; that app was stopped before any
fit. The successful launch is recorded in the execution audit. Do not blindly
repeat training: output-directory guards reject existing run IDs.

No E11-D/E work, official-test access, teacher API calls, commit, or push is part
of this experiment.
