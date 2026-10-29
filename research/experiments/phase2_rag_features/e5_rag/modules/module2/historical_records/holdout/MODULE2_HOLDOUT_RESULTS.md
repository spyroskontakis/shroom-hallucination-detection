# SHROOM RAG E5 — Module 2 Holdout Results

## Integrity and scope

- Preflight: PASS — 10 rows × 12 columns, complete ordered 10/10 join, unique example/evidence IDs.
- Human-completed SHA-256: `7519ae4988cf2bd5d0678d83523b884936beb6b257b0bff249f0de893531a93e`.
- Blinded SHA-256: `283be261ddfe126b28016f7155db75f8742ca04d9e17530727413f84cb9b03c2`.
- Frozen manifest SHA-256: `f7356c17dbf04e37f6125c13e1484a174490c3e8598596ba253010b846106c22`.
- Selected configuration SHA-256: `f9e8b35417222a97a29c17cd4d27b3140c9658f1c1ef84068eb61b72d63f572c`.
- Deterministic tests: 16/16 passed.
- Frozen configuration: reference-assisted Q_SRC_TGT + BM25; score >= 42.555018684798945; method agreement >= 2; duplicate rejection.
- No retuning or configuration comparison was performed.

## Ungated frozen-retriever top-1

- Strict Relevant@1: 2/10 (20.0%)
- Lenient Relevant@1: 3/10 (30.0%)
- Partially relevant: 1/10 (10.0%)
- Different sense: 0/10 (0.0%)
- Irrelevant: 7/10 (70.0%)
- Unsafe top-1: 7/10 (70.0%)

## Frozen gate

- Accepted coverage: 2/10 (20.0%)
- Abstention rate: 8/10 (80.0%)
- Strict accepted usable coverage: 1/10 (10.0%)
- Lenient accepted usable coverage: 2/10 (20.0%)
- Unsafe accepted evidence / all holdout: 0/10 (0.0%)
- Strict precision among accepted: 1/2 (50.0%)
- Lenient precision among accepted: 2/2 (100.0%)
- Unsafe proportion among accepted: 0/2 (0.0%)
- Strict false abstentions: 1; 1/10 (10.0%) overall; 1/8 (12.5%) among abstained.
- Lenient false abstentions: 1; 1/10 (10.0%) overall; 1/8 (12.5%) among abstained.

### Accepted relevance breakdown (denominator 2)

- `relevant_same_sense`: 1/2 (50.0%)
- `partially_relevant`: 1/2 (50.0%)
- `different_sense`: 0/2 (0.0%)
- `irrelevant`: 0/2 (0.0%)
- `uncertain_review`: 0/2 (0.0%)

### Abstained relevance breakdown (denominator 8)

- `relevant_same_sense`: 1/8 (12.5%)
- `partially_relevant`: 0/8 (0.0%)
- `different_sense`: 0/8 (0.0%)
- `irrelevant`: 7/8 (87.5%)
- `uncertain_review`: 0/8 (0.0%)

## Predeclared decision criteria

- Accepted unsafe evidence = 0%: **PASS** — 0/2 (0.0%).
- Strict accepted usable coverage >= 20%: **FAIL** — 1/10 (10.0%).
- Lenient accepted usable coverage >= 30%: **FAIL** — 2/10 (20.0%).
- Abstain-all prohibited: **PASS** — 2/10 (20.0%) accepted.
- Configuration unchanged: **PASS**.

## Final decision: `NO_GO_FOR_GEMINI`

The safety criterion passes, but strict and lenient accepted usable coverage fail their predeclared thresholds. Thresholds were not relaxed and no alternative configuration was examined.
Gemini is independently blocked because the strict development regression cases `preciosity`, `weary`, and `inconsistent` remain failed.

## Scientific interpretation

This is a very small, reference-assisted holdout. It supports only a diagnostic statement about this frozen configuration and cannot be interpreted as independent external-test evidence or a generalization estimate.

Official test: 0; retrieval/dense runs: 0; Gemini/API/network: 0; downloads/installations: 0; annotation/configuration changes: 0.
