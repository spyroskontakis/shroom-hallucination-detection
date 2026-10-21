# E9 final multi-proposition smoke — PARTIAL PASS

The frozen decomposer can split natural SHROOM hypotheses: 3/12 samples produced
multiple claims (two MT samples produced four each; one PG sample produced two).
All 12 samples were retained. There are 19 final claims: nine single-claim samples
and three multi-claim samples. No prompt, validator or Amendment 01 change was made.
Their SHA-256 hashes match the pre-run freeze; baseline input hashes also match.

Strict atomicity/self-containment is not universally satisfied. One split claim
combines priesthood and multiple chess-player attributes. Compound fallbacks and
unresolved pronouns/deictic expressions remain. One split resolves an ambiguous
modifier attachment using a plausible local interpretation; unconditional entailment
cannot be certified for that interpretation. No clear external factual addition or
fact-correction was observed. These are limitations of the frozen output, not fixes
applied after inspecting it. All outputs remain as originally generated/fallbacked.

Selection was fixed before calls: four samples per task, ranking hypothesis text
by word count plus weighted conjunctions, sentence boundaries, semicolons and
relative-clause markers. Ties use hypothesis text, then canonical ID. Only canonical
development rows were eligible. Some heuristics select coordinated phrases or
alternatives rather than independent propositions; no samples were replaced.

- API calls/successful responses: 15/15; model gpt-4o-2024-08-06; temperature 0.
- Fresh samples: 11. Cache hits: 1 (a matching previous fallback, reused after selection).
- New retries: 4. Fallbacks: 3 (two new, one cached). Previous retries are not counted again.
- Input tokens: 7,559. Output tokens: 1,867. Total: 9,426. Cached API input tokens: 0.
- Estimated cost: USD 0.0375675 for this run, including retries and excluding historical cache creation.
- Rates: USD 2.50/million input, USD 1.25/million cached input, USD 10/million output,
  from [official GPT-4o pricing](https://developers.openai.com/api/docs/models/gpt-4o).
  Actual billed dollars were not separately obtained.
- Leakage checks: PASS. Only hyp/task sample data were sent; selected input columns
  were canonical_id/source_split/task/hyp. No labels, references, predictions,
  external definitions or correctness information were used for selection.

Full per-sample task, canonical ID, hypothesis, final claims, counts, fallback and
review are retained locally in claims/smoke_multi12_v2/TWELVE_SAMPLE_AUDIT.md.
The reviewed structured equivalent is claims/smoke_multi12_v2/reviewed_samples.json.
Public aggregate review: reports/smoke_multi12_review.json.

STOPPED after this test. No full 561-row decomposition, E9-A/E9-B, NLI, MiniCheck,
Random Forest, official-test access, commit or push. The API-only summary is a
pre-review checkpoint; the final semantic findings above supersede its pending status.
