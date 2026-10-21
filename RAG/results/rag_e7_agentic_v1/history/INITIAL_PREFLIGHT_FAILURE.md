# E7 v1 — STOPPED at preflight; no experimental score

**Status: FAIL / STOPPED_PREFLIGHT_SECURITY_FAILURE. DEVELOPMENT-ONLY design; evaluation NOT RUN.**

The branch `agentic-rag-e7` was created from frozen tag `rag-e6-v1`, commit `0a1ef3e792867796c412070087095274b0206849`. No commit, push or tag was created for E7.

## Frozen proposed architecture

Deterministic training-evidence-median top-1 cosine router. In each outer fold, use E6 when evidence is available and top1_cosine >= the median of evidence-bearing outer-training rows; otherwise use E3. Exact decision inputs: evidence_available and top1_cosine. Quantile 0.5 is fixed a priori, with no label-based threshold search or inner tuning. No actual fold thresholds or route decisions were fitted/generated.

Protocol SHA-256: `0491505c0f98a2a4d2a0896370adbbc3674c6fdf873b96a8a31833e587923002`.

Protocol freeze UTC: `2026-09-09T15:53:49.8464243Z`, before the failed preflight. See `config/protocol_freeze.json`.

## Failure and stopping decision

The label-free preflight reached its final `assert not guard.events` and failed. The process-local Python audit guard recorded three `open` events rejected with `E7 write outside output directory forbidden`, at `2026-09-09T15:55:53.280756+00:00`. The guard blocked those writes. Operational network attempts: **0**.

The current guard log records event/reason/time, but not destination paths or call stacks. Therefore the originating component and intended write destinations are **not established**. Runtime temporary-file discovery is a possible explanation, not a verified diagnosis. No diagnostic rerun or guard relaxation was performed. A future explicitly authorized repair should improve path/call-site logging and confine runtime temporary files to E7 before imports, without changing the frozen router design.

The internal data/hash/runtime assertions returned without failure, but overall preflight **did not PASS**. No `config/preflight.json` success record was written. This report does not claim completion of the requested contract suite. Implementation stopped at common utilities and initial preflight; the router/evaluator/report scripts and contract tests remain unimplemented.

Per the user's explicit STOP instruction on a critical preflight failure, no final evaluation was started and no repair/retry was attempted.

## Requested results unavailable

- E7 outer evaluation suites: **0**; RF fits: **0**.
- Fitted fold thresholds, route counts, E7 correct/561, accuracy and Spearman: **not computed**.
- E7 vs E6 corrections/regressions, McNemar and paired-bootstrap CI: **not computed**.
- E7 DM/MT/PG, evidence/no-evidence and per-route/fold metrics: **not computed**.
- Frozen E6 reference only: 453/561, accuracy 0.8074866310, Spearman 0.7444205394. These are not E7 measurements.

No score-driven selection or redesign occurred. No official-test dataset was accessed; data parsing used the named development files with label-free projections. Hash verification also read frozen artifact bytes (including saved development outputs), without loading predictions/labels for routing or scoring. No model inference, new retrieval, LLM call, E8 or thesis edit occurred. The authorized setup `git fetch origin` was outside the offline preflight.

## Final integrity

The independent post-failure SHA-256 audit verified all **481** protected files unchanged, including frozen E3/E5/E6 and Module 4 release/provenance. The E7 protocol hash is unchanged. There is no evaluation-started marker. See `config/failure_audit.json` and `config/security_preflight.json`.

All created files are under `RAG/results/rag_e7_agentic_v1/`. Existing untracked `Augmentation Pipeline.txt` remains untouched. No commit, push, tag, move or deletion was performed.
