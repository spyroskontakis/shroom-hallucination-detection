# SHROOM RAG E5 — Module 2 Phase B Results

## Scope

Offline evaluation using only locked human relevance annotations. `Q_SRC_TGT` is reference-assisted and is not independent external validation.

## Preflight and tests

- Preflight checks: 213/213 passed
- Deterministic tests: 12/12 passed
- Human annotations: 83 rows, 83 unique IDs, 10 development examples
- Stable Phase A appearance joins: 192/192
- Annotation SHA-256: `3f1f0a6d3eb9a75de69344f6e1df13b88745e464c98f94e1ce87997302669ed5`

## Retrieval metrics

| Query | Method | Strict R@1 | Lenient R@1 | Unsafe top-1 | Eligible@3 |
|---|---|---:|---:|---:|---:|
| Q_SRC | exact | 10.0% | 30.0% | 20.0% | 40.0% |
| Q_SRC | bm25 | 10.0% | 30.0% | 70.0% | 50.0% |
| Q_SRC | dense | 10.0% | 50.0% | 50.0% | 70.0% |
| Q_SRC | rrf | 10.0% | 40.0% | 60.0% | 60.0% |
| Q_SRC_TGT | exact | 10.0% | 30.0% | 20.0% | 40.0% |
| Q_SRC_TGT | bm25 | 10.0% | 60.0% | 40.0% | 80.0% |
| Q_SRC_TGT | dense | 10.0% | 60.0% | 40.0% | 70.0% |
| Q_SRC_TGT | rrf | 10.0% | 60.0% | 40.0% | 70.0% |

Precision@4/@5 and full MRR are `NA` wherever retrieved positions are not fully annotated. MRR@3 is retained in the CSV only as an explicitly truncated diagnostic.

## Gate sensitivity and Pareto frontier

- Deterministic grid configurations: 780
- Non-trivial Pareto configurations: 16
- Selection status: **PRELIMINARY_DEVELOPMENT_SELECTION**
- Configuration: `Q_SRC_TGT|bm25|score=q25|margin=none|agree=2|exact=0|dedup=1`
- Evidence coverage: 50.0%
- Strict / lenient usable coverage: 10.0% / 50.0%
- Unsafe evidence rate (accepted / all): 0.0% / 0.0%
- Abstention rate: 50.0%

### Pareto frontier (unique operating points)

| Usable lenient | Unsafe/all | Abstention | Example configuration |
|---:|---:|---:|---|
| 60.0% | 10.0% | 30.0% | `Q_SRC_TGT|dense|score=q25|margin=none|agree=1|exact=0|dedup=1` |
| 60.0% | 40.0% | 0.0% | `Q_SRC_TGT|bm25|score=none|margin=none|agree=1|exact=0|dedup=1` |
| 50.0% | 0.0% | 50.0% | `Q_SRC_TGT|bm25|score=q25|margin=none|agree=2|exact=0|dedup=1` |

## Regression cases

| Term | Decision | Human category | Pass |
|---|---|---|---|
| preciosity | accept | partially_relevant | False |
| dateliner | accept | relevant_same_sense | True |
| continuous | abstain | different_sense | True |
| weary | accept | partially_relevant | False |
| inconsistent | accept | partially_relevant | False |

## Limitations

- Ten development examples are insufficient for a stable estimate or generalization claim.
- Only three annotated candidates are strict relevant; one annotation has medium confidence.
- The grid is tuned on the same development subset used for reporting and therefore is optimistic.
- `uncertain_review` is neither relevant nor unsafe; none was forced into either class.
- Holdout remains sealed. No Gemini/API, retrieval, dense encoding, download, package change, official test, Module 3, or E3 integration was performed.
