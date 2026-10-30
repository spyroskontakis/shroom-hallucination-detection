# E9 Protocol Amendment 01 — hypothesis semantic propositions

This clarification was authorized after the label-blind three-sample smoke test
and **before any E9 model evaluation**. The trigger was zero extracted claims for
DM and MT, not E9 accuracy, human labels or paired outcomes. No human labels were
inspected for sample selection or this clarification. Earlier E6-v3 baseline
verification used its saved evaluation metadata; that is separate from this
label-blind decomposition change. No E9 scores exist.

For SHROOM, a claim is an atomic semantic proposition explicitly expressed by the
hypothesis. It need not be an independently world-verifiable encyclopedic fact.
DM definitional statements/fragments and MT/PG semantic utterances are valid.

- Preserve the hypothesis meaning exactly, including negation, uncertainty,
  quantities, attribution, ambiguity, odd wording and factual errors.
- A single proposition must be returned as the complete hypothesis verbatim,
  exactly once. The validator rejects a single reworded claim.
- Multiple propositions may be split into atomic self-contained claims using only
  hypothesis-internal linguistic context. No external disambiguation or invented
  headword, speaker identity, corrected translation or missing referent is allowed.
- If a faithful split would require invented context, preserve the complete
  hypothesis. This does not establish atomicity of a compound fallback.
- Up to three total attempts (initial plus two controlled retries) are allowed
  for invalid/empty output. If no valid claims remain, preserve the complete
  hypothesis as one claim and record decomposition_fallback=1. Valid original
  single-proposition claims have decomposition_fallback=0.
- API/model unavailability stops execution; it never silently becomes a fallback.

Model and temperature remain gpt-4o-2024-08-06 and 0. Sample input remains exactly
hyp and task. No source, target, labels, hallucination probabilities, predictions,
definitions or test data may enter the prompt. Structured output includes
claim_index and claim_text, with exact supporting quotes and quality flags.
The self_contained flag may be false only for the unchanged complete hypothesis;
this prevents rejection of definitional fragments solely for missing headwords.
Schema checks do not prove semantic entailment; each smoke output is reviewed
against its hypothesis alone.

Prompt version: e9-hyp-only-semantic-v2. Cache keys include the updated version,
full prompt and schema. Old caches and the failed three-sample outputs remain
unchanged. The previous decomposer is archived as scripts/decomposer_v1.py;
the original three-sample runner continues to import that version.

Amended smoke selection: first three canonical IDs per task, in sorted order,
restricted to the frozen development_model_agnostic portion (493 rows). Exactly
nine hypotheses: three DM, three MT, three PG. Split and ID are local selection
metadata only. No label-based selection, reference inspection or replacement of
difficult examples. The earlier three hypotheses are included by this rule.

Only this nine-sample smoke is authorized now. Full decomposition, E9-A/E9-B,
NLI, MiniCheck and RF evaluation remain unstarted. No official test access,
committing or pushing is authorized. All 36 baseline features, folds, RF settings,
E9 feature definitions and model-selection rules remain unchanged.

Reproduction: use scripts/smoke_nine.py --run-api-calls with the frozen Python
environment and -B. API calls are disabled without the explicit flag. The runner
uses persistent versioned caches and saves raw responses immediately. Row-level
examples remain ignored under claims/smoke_nine_v2/; aggregate reports contain no
labels, references or prediction values.
