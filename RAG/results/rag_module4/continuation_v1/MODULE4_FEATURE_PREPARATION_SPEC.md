# Module 4 Continuation v1 — Frozen RAG Feature Specification

This specification was written after the disclosed historical label incident, but before any new mixed-E3 CSV content access, real inference, training, prediction, or score evaluation in continuation v1.

- Input: the 561-row label-free locked Module 4 CSV only.
- Evidence: locked English-Wiktionary-only snapshot; exact normalized-term eligibility.
- Query: `term + "\n" + src`.
- Candidate text: candidate term plus the frozen parser context containing POS and definition.
- Ranking: normalized MPNet cosine, descending; deterministic tie-break by `source_entry_id`, then stable `evidence_id`; `top_k=5`.
- MPNet: `sentence-transformers/all-mpnet-base-v2@e8c3b32edf5434bc2275fc9bab85f82640a19130`, max sequence length 256, normalized embeddings, cosine as dot product, float32 model policy.
- NLI: `microsoft/deberta-large-mnli@7296194b9009373def4f7c5dad292651e4b5cf4e`; premise is candidate definition, hypothesis is `tgt`; truncation enabled, max length 512; indices 0 contradiction, 1 neutral, 2 entailment.
- Target-definition cosine: maximum normalized MPNet cosine between `tgt` and each selected definition.
- Lexical overlap: maximum Unicode-NFKC/casefold token-set Jaccard using `re.findall(r"[^\W_]+", ..., re.UNICODE)`.
- Sense count: number of candidates in the final top-five ordered list, range 0–5.
- Zero evidence: all seven features exactly zero. MT/PG always use the same seven-zero fallback.
- Output order: locked 561-row input order; one identifier metadata column plus exactly seven numeric features.
- Determinism: seed 42; model `eval()`/inference mode; batch-size changes are execution-only; CSV is UTF-8 BOM with LF and fixed column order.
- Cache identity: input, snapshot, model/revision and resolved model-file hashes, tokenizer identity, code/spec hashes, and input-text hashes. Cache reuse requires schema, provenance, and content-hash validation.
- Forbidden pipeline inputs: E3 mixed CSV, labels, probabilities, folds, OOF predictions, holdout, official test, and annotations.
