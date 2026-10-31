# E9 Amendment 01 smoke results — PASS with two fallbacks

The semantic-proposition clarification was recorded before this smoke and before
any E9 evaluation. Selection used the first three sorted canonical development IDs
per task, without labels or reference fields. Nine samples were processed.

- API authentication/model access: PASS. Returned model gpt-4o-2024-08-06.
- Temperature: 0. Successful calls: 13/13 (nine initial calls, four retries).
- JSON parsing: 13/13. Seven samples directly validated; two required fallback.
- Final claim counts: DM [1,1,1], MT [1,1,1], PG [1,1,1].
- Fallback counts: DM 0, MT 1, PG 1. No samples dropped; 9/9 have >=1 claim.
- Tokens: 6,353 input + 694 output = 7,047 total. Cached input: 0.
- Usage-priced cost: USD 0.0228225, including all retries.
- Projected 561-sample cost: 0.0228225 / 9 * 561 = USD 1.4226025.
- Cache hits: 0. Offline tests: 14 passed. Baseline input hashes unchanged.

Costs use actual returned usage and standard rates of USD 2.50 per million input,
USD 1.25 cached input, and USD 10 output from
[official GPT-4o pricing](https://developers.openai.com/api/docs/models/gpt-4o).
Billing ledger dollars were not available. Projection assumes the observed average
including retries; this small deterministic smoke is not a guaranteed budget.

All retained claims equal their complete hypotheses verbatim. Thus wording,
negation, uncertainty and ambiguity are preserved, without retained corrections
or unsupported additions. The raw model did attempt to reinterpret an ambiguous
MT utterance on all three attempts; validation rejected those outputs. One PG
question returned zero claims three times. The exact-hypothesis fallback preserved
both samples. A fallback question is not asserted to be a world-verifiable fact.
Multi-proposition splitting was not exercised and is not validated by this smoke.

Leakage checks PASS: persisted API bodies exactly match the fixed prompt/schema
and hyp/task projection. IDs and development split metadata remained local. No
source, target, label, probability, prediction, external definition or test data
entered any prompt. The canonical development manifest passed its frozen hash.

Row-level examples with canonical IDs are local-only in
claims/smoke_nine_v2/SMOKE_EXAMPLES.md. All raw responses, prompts without headers,
cache records and outputs remain ignored there. Aggregate audit:
reports/smoke_nine_review.json. Previous smoke reports remain historical records.

STOPPED after this smoke. No full decomposition, E9-A/E9-B, NLI, MiniCheck or RF.
No official test access. No staging, commits or pushes. A passing fallback/coverage
check does not authorize a full run.
