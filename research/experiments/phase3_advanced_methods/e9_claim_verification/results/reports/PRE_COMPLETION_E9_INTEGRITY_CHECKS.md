# Latest execution checkpoint

Frozen prompt/validator/Amendment hashes and all baseline input hashes remain PASS. Every persisted full-run request matches the fixed hyp/task payload. 90 cached samples have nonempty validated outputs; full 561-row coverage is PENDING. HTTP 429 stopped the run. E9-A/E9-B training and inference did not start. The original offline preparation audit below remains historical.

# E9 integrity checkpoint

PASS: 561 unique canonical IDs, 493 development + 68 trial; exact row order across
baseline components and OOF. Five original folds match the canonical assignments,
saved OOF, frozen fold copy and canonical metadata.

PASS: exact 36-column order, finite values, byte hashes, numerical identity of
the first 34 columns to E6-v2 and the last two columns to the saved HHEM additions.
Recomputed saved OOF overall, per-fold and per-task metrics equal historical values.
Runtime package versions match the baseline; no baseline refit was performed.

PASS, preparation only: decomposition rejects all input fields except hyp/task;
API absence is detected without a request; cache validation rejects corruption;
row failures fall back rather than vanish; unavailable API hard-stops; append-only
feature checks reject missing/reordered IDs and wrong column order. Synthetic tests
cover threshold boundaries, NLI argmax ties, singleton standard deviation, invalid
probabilities, controlled retries and paired statistics.

PENDING: real label-blind smoke validation, semantic entailment review, full
canonical claim coverage, real cache reuse, NLI inference/truncation review,
44/49-column matrices and fold-separated E9 training. No claim is made that offline
schema checks prove semantic entailment. E9-B preflight has not run.

Official test: no access, loading, inspection, evaluation or use. Population
protection relies on the frozen trusted development manifest and its SHA-256;
the official test is deliberately not re-opened to compute an overlap check.

No OOF values are passed to claim extraction or feature builders. The evaluation
component uses saved OOF only for paired comparisons and baseline checks. It has
no learned preprocessing; each fit explicitly indexes only training rows/targets.
Those runtime contracts are implemented but remain unexercised on E9 data.

Git publication protection: the new directory's .gitignore excludes all claims and
features, in addition to the repository-wide CSV/JSONL rules. No historical file,
tracked root .gitignore, or .git/info/exclude was changed in this continuation.
Nothing has been staged, committed or pushed.
