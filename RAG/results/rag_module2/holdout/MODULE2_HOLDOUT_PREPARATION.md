# SHROOM RAG E5 — Module 2 Blinded Holdout Preparation

## Status

Prepared only. No holdout relevance annotation or holdout metric was created or computed.

## Frozen inputs

- Pre-existing holdout split: 10 examples, fixed before development annotation/metrics.
- Frozen query/retriever: reference-assisted `Q_SRC_TGT` + `BM25`.
- Frozen gate: BM25 score >= `42.555018684798945`, method agreement >= 2, duplicate rejection.
- Selected-config SHA-256: `f9e8b35417222a97a29c17cd4d27b3140c9658f1c1ef84068eb61b72d63f572c`.
- No threshold, weight, method, query variant, margin rule, or tie-breaking was recomputed.

## Deliverables and integrity

- Blinded CSV: 10 rows x 12 columns, one frozen top-1 candidate per holdout example.
- Accepted and abstained top-1 candidates are both included; gate diagnostics remain only in the internal manifest.
- Annotation columns are blank; method/rank/score/agreement/gate fields are absent.
- Separate offline UI validates the exact ordered annotation IDs.
- Blinded CSV SHA-256: `283be261ddfe126b28016f7155db75f8742ca04d9e17530727413f84cb9b03c2`.
- Frozen manifest SHA-256: `f7356c17dbf04e37f6125c13e1484a174490c3e8598596ba253010b846106c22`.
- Holdout UI SHA-256: `d47cf6a3012ddfa884dded22c2a20722e6993666b88d0a1364526288d63c2c04`.

## Predeclared future evaluation criteria

- Accepted unsafe evidence: 0%.
- Strict accepted usable coverage: at least 20%.
- Lenient accepted usable coverage: at least 30%.
- Abstain-all: failure.
- Configuration changes after holdout annotation disclosure: prohibited.
- These are descriptive thresholds for a small holdout, not an external test claim.
- Gemini remains blocked while mandatory strict regression cases fail.

## Guards

Official test: 0; API/network: 0; retrieval/dense execution: 0; downloads/installations: 0; holdout labels: 0; holdout metrics: 0.
