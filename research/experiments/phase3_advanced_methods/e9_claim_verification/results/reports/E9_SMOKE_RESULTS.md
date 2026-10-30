# E9 three-sample smoke test — FAIL

API access succeeded; the nonempty-claim requirement failed for two samples.
Exactly three API calls were made, one per canonical development DM/MT/PG sample.
All three returned gpt-4o-2024-08-06 at requested temperature zero; all JSON parsed.
No retries, replacement samples, fallback claims or downstream inference were run.

| Task | Parsed claims | Input tokens | Output tokens | Total tokens |
|---|---:|---:|---:|---:|
| DM | 0 | 369 | 15 | 384 |
| MT | 0 | 369 | 15 | 384 |
| PG | 1 | 365 | 60 | 425 |
| Total | 1 | 1103 | 90 | 1193 |

Three successful API responses; one of three samples meets the nonempty-claim
criterion. Empty results are retained for audit, so no sample disappeared.
DM and MT report unresolved ambiguity. Hypothesis-only inspection of the PG
claim found preserved meaning/negation and no factual correction or added fact.
Its speaker remains identified only as the speaker in the original hypothesis.
No positive semantic conclusion is claimed for absent DM/MT claims.

Prompt leakage checks PASS. Persisted request payloads contain only task and hyp
as sample data. Canonical IDs and split metadata remain local. Selection used the
first sorted canonical ID per task restricted to development_model_agnostic.
The canonical file matched its previously verified SHA-256. No official test file
was accessed. No labels, references, E6 predictions or definitions entered prompts.

Structured output adds claim_index to the original E9 claim schema, with zero-based
consecutive indices. The isolated smoke version is e9-hyp-only-v1-indexed-smoke;
the original full-run decomposer/configuration is unchanged. This avoids enabling
or silently approving a full run based on this failed smoke test.

Cost calculated from actual reported usage: **USD 0.0036575**. Cached input tokens: 0.
Rates per million tokens: USD 2.50 input, USD 1.25 cached input, USD 10.00 output,
from [official GPT-4o pricing](https://developers.openai.com/api/docs/models/gpt-4o).
Actual billed cost is not returned by Chat Completions and was not independently
verified against the billing ledger; the figure above is usage-priced cost.

Observed mean: 367.6667 input and 30 output tokens per sample. Simple projection:
0.0036575 / 3 * 561 = **USD 0.6839525**. This assumes the same mean lengths/cache
fraction and one call per sample. Two empty outputs make it a weak estimate for a
successful full decomposition; retries or longer claims would increase cost.

STOPPED after smoke. Full decomposition, E9-A/E9-B evaluation, NLI, MiniCheck and
Random Forest were not run. No commits or pushes. The key was never printed or
stored. Raw responses, request bodies (without authentication headers), inputs and
parsed outputs remain ignored under claims/smoke_three_v1/. Aggregate final audit:
reports/smoke_three_review.json. The prior blocked/preparation reports are historical
checkpoints; this report records the latest smoke attempt.
