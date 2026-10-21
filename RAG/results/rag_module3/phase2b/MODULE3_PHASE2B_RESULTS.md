# SHROOM RAG E5 — Module 3 Phase 2B Human-Only Results

**Status:** `EVALUATED_HUMAN_ONLY`  
**Evaluation date:** 2026-08-28  
**Frozen Phase 2B decision:** `PROCEED_TO_FINAL_GATED_RAG`  
**Final gated RAG execution:** not performed

## 1. Scope and evaluation order

This report closes only the human-only evaluation of the Module 3 Phase 2B external lexical-KB candidate set. It uses the canonical completed human file `module3_phase2b_external_kb_blinded_human_completed.csv`. No AI-completed annotation file was opened or used.

The evaluation was deliberately separated into two ordered stages:

1. The blank and human-completed CSVs were checked, joined, and used to compute and freeze all human-only metrics. Provenance was not opened during this stage.
2. Only after the metric lock was fixed was the hidden provenance opened for deterministic join verification, source attribution, and the prespecified reference-overlap audit.

The canonical human-only metric payload—including input hashes, ordered IDs, category/confidence counts, per-example counts, strict-positive examples, frozen rule, and decision—has SHA-256:

```text
73ffdd5cab790e5aa31e4d5167fb8745a5a9a5b5e3220c480f41388876c6ebdc
```

The post-lock provenance audit did not alter or recompute that payload.

## 2. Integrity preflight

| Input artifact | Bytes | SHA-256 | Result |
|---|---:|---|---|
| `annotation/module3_phase2b_external_kb_blinded.csv` | 9,576 | `5601166860ca7d37872720b0188f590ac3684b71e84003bced1f654d796c05fe` | PASS |
| `annotation/module3_phase2b_external_kb_blinded_human_completed.csv` | 10,024 | `3f5a4f74fe96525b4e7678c1ffd68fb46bee546f454c9da3158ff4619deb19e3` | PASS |
| `MODULE3_PHASE2B_PLAN.md` | 13,297 | `966e0ce44296429c9d5b2f147b485a1a3e29d49693bdfa41b0f3fb5d327d7733` | PASS |
| `external_kb/MODULE3_PHASE2B_SOURCE_MANIFEST.json` | 16,758 | `9d91c599fabbd6782e92b13cb7f8fa6e2f984c464242b02a578792d1de893ece` | PASS |
| `annotation/module3_phase2b_external_kb_provenance.jsonl` | 50,886 | `8b34a6805f0f8f73b8d9cd86b730d175e7617fd4f0e9a8badb2408abdfad4a4d` | opened only after metric lock; PASS |

The completed CSV passed every preflight assertion before provenance access:

- 21/21 data rows and 12/12 exact columns;
- expected completed-file SHA-256 matched exactly;
- the first nine columns were value-for-value identical to the blank CSV in 21/21 ordered rows;
- ordered `annotation_id` values were unchanged in 21/21 rows;
- 21/21 unique `annotation_id` values;
- 21/21 unique `evidence_id` values;
- 21/21 unique `(example_id, evidence_id)` pairs;
- category and confidence were present and valid in 21/21 rows;
- annotation notes were nonblank in 0/21 rows.

## 3. Locked human-only metrics

### Candidate-level relevance

| Relevance category | Count / denominator | Rate |
|---|---:|---:|
| `relevant_same_sense` | 6/21 | 28.57% |
| `partially_relevant` | 1/21 | 4.76% |
| `different_sense` | 14/21 | 66.67% |
| `irrelevant` | 0/21 | 0.00% |
| `uncertain_review` | 0/21 | 0.00% |

### Annotation confidence

| Confidence | Count / denominator | Rate |
|---|---:|---:|
| High | 21/21 | 100.00% |
| Medium | 0/21 | 0.00% |
| Low | 0/21 | 0.00% |

### Per-example relevance distribution

| Term | Candidates | Strict | Partial | Different sense | Irrelevant | Uncertain | Strict-positive example |
|---|---:|---:|---:|---:|---:|---:|---|
| preciosity | 3/21 | 1/3 | 0/3 | 2/3 | 0/3 | 0/3 | YES |
| bandslash | 1/21 | 1/1 | 0/1 | 0/1 | 0/1 | 0/1 | YES |
| nonentertainment | 1/21 | 1/1 | 0/1 | 0/1 | 0/1 | 0/1 | YES |
| continuous | 5/21 | 1/5 | 1/5 | 3/5 | 0/5 | 0/5 | YES |
| foreboding | 5/21 | 0/5 | 0/5 | 5/5 | 0/5 | 0/5 | NO |
| tetaniform | 1/21 | 1/1 | 0/1 | 0/1 | 0/1 | 0/1 | YES |
| keen | 5/21 | 1/5 | 0/5 | 4/5 | 0/5 | 0/5 | YES |
| **Total** | **21/21** | **6/21** | **1/21** | **14/21** | **0/21** | **0/21** | **6/7** |

At least one strict candidate was found for 6/7 examples (85.71%). `foreboding` was the only example without a strict candidate in the selected external top-five set.

## 4. Frozen rule and Phase 2B decision

The rule was registered before annotation:

- at least 4/7 strict-positive examples → `PROCEED_TO_FINAL_GATED_RAG`;
- fewer than 4/7 strict-positive examples → `CLOSE_RAG_AS_CONTROLLED_NEGATIVE_RESULT`.

The observed human-only result is 6/7 strict-positive examples. Therefore the rule is satisfied and the official Phase 2B decision is:

```text
PROCEED_TO_FINAL_GATED_RAG
```

This decision authorizes the separately controlled next experiment; it is not evidence that a final gated RAG system is already safe or effective. No final gated RAG was executed in this evaluation.

## 5. Post-lock provenance verification

After the human metric lock, the hidden provenance was opened and checked. It contains 44 records: 21/44 selected candidates, 3/44 excluded prior-human exact duplicates, and 20/44 rank-limit exclusions. The selected subset joined in the same order to 21/21 human rows by `annotation_id`, `example_id`, and `evidence_id`; candidate term, definition, and context also agreed in 21/21 rows.

The frozen preparation metadata confirms:

```text
retrieval/ranking query fields = term, src
tgt used for selection = false
tgt fields materialized before selection lock = 0
selection SHA-256 = 13b2b66d5cfc52896fadda0c5381d21c8c9bfd6019073e679af68c53853a00c3
```

No provenance record contains a `tgt` field. This preserves the documented procedural ordering: candidate retrieval and ranking were locked before `tgt` was joined into the annotation view.

## 6. Explicit reference-overlap audit

The audit normalized `candidate_definition` and `tgt` independently using Unicode NFKC normalization, Unicode casefolding, whitespace collapse, and outer whitespace removal. Exact equality after normalization occurred in 6/21 rows (28.57%). These six rows were exactly the six `relevant_same_sense` rows:

- overlap among strict rows: 6/6 (100.00%);
- overlap among non-strict rows: 0/15 (0.00%);
- strict rows without overlap: 0/6 (0.00%);
- overlap rows with a non-strict label: 0/6 (0.00%).

| Term | Evidence ID | Retrieval rank | External source | Human category | Definition = `tgt` after normalization |
|---|---|---:|---|---|---|
| preciosity | `M3P2B-EV-76C476BE4C2C5494` | 3/3 | English Wiktionary | `relevant_same_sense` | YES |
| bandslash | `M3P2B-EV-3748F1517BED8137` | 1/1 | English Wiktionary | `relevant_same_sense` | YES |
| nonentertainment | `M3P2B-EV-21B7CF66F8DE8F13` | 1/1 | English Wiktionary | `relevant_same_sense` | YES |
| continuous | `M3P2B-EV-75BC4AACF08F2FC8` | 1/5 | English Wiktionary | `relevant_same_sense` | YES |
| tetaniform | `M3P2B-EV-4F1FCA933E9BF586` | 1/1 | English Wiktionary | `relevant_same_sense` | YES |
| keen | `M3P2B-EV-FE7B8B85321CBB1A` | 1/5 | English Wiktionary | `relevant_same_sense` | YES |

All 6/6 normalized overlaps came from the exact English Wiktionary pages; WordNet contributed 0/6 overlap rows.

## 7. Scientific interpretation

There was no procedural leakage in candidate generation: `tgt` was not used in retrieval, filtering, ranking, deduplication, or candidate selection, and the selection hash was fixed before `tgt` was made available for annotation. The human-only metrics were also locked before provenance inspection.

Nevertheless, the overlap audit reveals strong external-source/reference overlap. Every strict-positive row reproduces its `tgt` definition after normalization, and every such row comes from English Wiktionary. Consequently, the 6/7 strict-positive result demonstrates that the selected external lexical source covers six reference definitions in this small development diagnostic. It does not demonstrate semantic generalization to independently written references, unseen samples, or an external test distribution.

This distinction is central: absence of procedural leakage preserves the validity of the acquisition and ranking process as implemented, but reference/source identity limits the interpretation of the observed strict relevance. The result is evidence of lexical coverage and source concordance, not proof of generalizable word-sense retrieval or downstream RAG safety.

Additional limitations are the seven-example development scope, the reference-assisted annotation view, the five-candidate cap for polysemous terms, one human annotator, and absence of inter-annotator agreement. The unanimous high-confidence annotations describe this annotator's certainty; they do not replace independent agreement or broader validation.

## 8. Artifact hygiene

This evaluation created only `MODULE3_PHASE2B_RESULTS.md`. The blank CSV, canonical human-completed CSV, provenance, source manifest, snapshot, preparation plan, prior Module 1/2/3 artifacts, E1–E4 artifacts, and all annotations remained unchanged.

Evaluation accounting: AI annotation files opened/used 0; annotations modified 0; official test accesses 0; network/API calls 0; Gemini/LLM calls 0; notebook executions 0; retrieval executions 0; dense/model/reranker executions 0; installations/downloads 0; final gated RAG executions 0.

The report's SHA-256 is computed after file closure and reported externally to avoid a self-referential hash.
