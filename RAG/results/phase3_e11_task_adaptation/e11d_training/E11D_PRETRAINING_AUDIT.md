# E11-D pretraining audit: PASS

Human-only: same 561 rows, exact E11-A input bytes and five folds. No synthetic examples or official test access. Baselines recomputed from repository OOF artifacts.

Cosine embedding loss, lambda 0.1, margin 0; mean pooled final-layer paired-sequence representations, excluding padding/special tokens and including existing text prefixes. Joint cross-encoder context; no projection or extra model forward.

All E11-A model/revision, tokenizer, 512-token limit, seed 42, AdamW, LR 1e-5, weighted CE, batch 8/accumulation 2, five epochs, BF16, scheduler, final checkpoint and probability extraction settings are unchanged. Full configuration and hashes are in the JSON audit and loss protocol.

Offline tests passed before freezing. Exactly five fits authorized. No search or extra smoke fit.
