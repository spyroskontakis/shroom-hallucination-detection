# E11-D: human-only contrastive task adaptation

Single fixed experiment: the E11-A classifier and five human folds, with weighted cross-entropy plus 0.1 times a pairwise cosine embedding loss. Zero synthetic examples. All design choices were frozen before training.

For label y=0 (not hallucination), the pair loss is 1−cos(a,b). For y=1 (hallucination), it is max(0,cos(a,b)); margin zero. The loss averages over the current minibatch. There is no temperature, projection head, negative mining or cross-example pairing.

The representations are mean-pooled final encoder hidden states for sequence A and sequence B of the original paired forward pass. Fast-tokenizer sequence membership excludes special tokens and padding. The frozen TASK/REFERENCE/HYPOTHESIS text prefixes remain included. These are jointly contextualized cross-encoder representations, not independent sentence embeddings.

The pinned model/revision, binary classification head initialization, human data/order, reference selection, tokenizer, truncation, class weights, optimizer, schedule, seed, five epochs, BF16 precision, accumulation and heldout inference are inherited from E11-A. No additional encoder forward is performed. Classification inference does not compute the auxiliary loss.

## Reproducibility

- `E11D_LOSS_PROTOCOL.json`: fixed objective plus complete inherited settings.
- `E11D_PRETRAINING_AUDIT.json`: human/tokenization/baseline reconciliation and tests before launch.
- `RUNTIME_MANIFEST.json`: explicit upload allowlist and byte hashes; checked inside each worker before training.
- `modal_training.py`: five jobs, automatic retries disabled; refuses a second local launch if returns directory exists.
- `train_fold.py`: narrowly modified copy of E11-A training implementation.
- `verify_saved_checkpoints.py`: independent CPU-only rehash of all saved checkpoint assets and predictions.
- `evaluate.py`: invokes the original E11-A metric function; validates result identity and all 561 OOF rows.
- `private/`: ignored human row-level outputs, return records, logs and preservation snapshot.
- `E11D_MANIFEST.json` and `SHA256SUMS.txt`: final hashes; the latter includes the manifest hash to avoid self-reference.

Training volume: `shroom-e11d-human-contrastive-results`. Fold checkpoints: `/results/e11d-fixed-001/folds/fold_N/e11d-fold-00N/final_checkpoint`.

Do not relaunch completed folds. Reconcile persistent outputs first if the local process is interrupted. There are no teacher clients or official-test data inputs in the runtime bundle. No hyperparameter selection is performed from OOF results.
