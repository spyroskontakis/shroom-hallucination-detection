# E9 final integrity

PASS: 561 canonical development/trial IDs and order preserved, 575 final claims,
all samples have at least one claim. Frozen prompt, validator, configuration and
Amendment 01 hashes are unchanged. Persisted requests match hyp/task only.

PASS: exact 36 E6-v3 columns preserved in value and order, eight frozen NLI features
appended (44 total). All 575 claim scores/aggregates reconstructed and checked.
DM/MT use target as premise; PG uses source. Claim is always NLI hypothesis.
No truncations. No prediction or label is provided to decomposition/NLI.

PASS: exact five locked folds, original RF parameters, five fits, 561 OOF predictions.
Training manifests and hashes confirm only training-row features and targets used.
Saved E6-v3 OOF: 474/561, accuracy 0.8449197860962567, Spearman 0.7816945786401444.
E9-A: 471/561, accuracy 0.839572192513369, Spearman 0.7804191219308901.
No post-score tuning. Accepted semantic atomicity/self-containment limitations
remain; structural integrity checks do not establish universal semantic entailment.

BLOCKED_MINICHECK: hardware/dependency preflight completed after E9-A; zero E9-B fits.
See reports/minicheck_preflight.json. No alternative model or quantization used.

Audit evidence: reports/E9-A_pre_fit_integrity.json and reports/E9-A_final_integrity.json.
The official 1,500-row test was never opened, hashed, inspected or evaluated.
Population protection uses the trusted canonical development manifest hash.
No commit or push. Prior checkpoint retained in reports/PRE_COMPLETION_E9_INTEGRITY_CHECKS.md.
