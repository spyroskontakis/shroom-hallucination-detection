# E10 retrospective official-test protocol — execution blocked

Status: **BLOCKED_PREFLIGHT**. This document fixes the recommendation before test gold inspection; it is not an execution-complete declaration.

Primary recommendation: **B, exact canonical 561-row thesis training pool**, comprising 493 official validation and 68 official trial examples. These labels were public pre-test material. Do not try a second training population and choose on test scores. The 499-row alternative changes the frozen training pool and contains four exact test overlaps before cleaning.

The source-pair overlap condition and frozen lexical resource coverage must be resolved before this protocol becomes executable. Do not silently drop training rows, convert unacquired terms to no-evidence zeros, substitute resources, or extend the frozen snapshot without documenting the new acquisition boundary. See E10_OFFICIAL_TEST_DATA_AUDIT.md.

If those prerequisites are resolved in a separately recorded continuation:

1. Retain the exact 37 ordered predictors and RF parameters recorded in E10_DEVELOPMENT_REPLAY.json. Fit exactly one final RandomForestRegressor to allowed training p_hallucination, with random_state=42 and no feature selection, imputation, calibration or tuning.
2. Keep test gold outside the inference process. Preserve every one of the 1,500 official IDs and its original index, including repeated text items with different IDs. Predictions must be finite, clipped to [0,1], with Hallucination defined by p>=0.5.
3. Freeze and SHA256-hash the model/feature manifests and complete predictions before allowing any scoring process to decode gold values.
4. Score once using the fixed metric policy, including the inherited 12-decimal probability rounding for Spearman. Report overall/task counts, Accuracy, Spearman, confusion matrix and class counts. Never change the system after this score.
5. Label any published-score comparison “retrospective comparison”, not an official submission or rank. Disclose earlier historical test exposure and post-competition resources/checkpoints.

No fit, inference, Modal launch or test scoring has occurred under this protocol. No prediction or metrics file is created as a placeholder.
