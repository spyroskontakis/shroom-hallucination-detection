# SHROOM RAG E5 — Module 3 Phase 2B Preparation Plan

**Status:** `PREPARED_FOR_HUMAN_ANNOTATION`  
**Preparation date:** 2026-08-27  
**Scope:** development-only, offline after controlled source acquisition  
**Phase 2B relevance annotations / metrics / decision:** not produced

## 1. Aim and bounded scope

Module 3 Phase 2B is a small external lexical-knowledge-base coverage experiment for the same seven difficult development examples used in the preceding diagnostics, in this fixed order:

1. `preciosity` — `EX-590A0B447A17`
2. `bandslash` — `EX-1AA2C1DAFB9C`
3. `nonentertainment` — `EX-7565997D951E`
4. `continuous` — `EX-D4E131D57443`
5. `foreboding` — `EX-C47370FB429F`
6. `tetaniform` — `EX-1E6E8BDB9874`
7. `keen` — `EX-6681F3007742`

The experiment asks only whether exact lexical entries from Princeton WordNet 3.1 and English Wiktionary provide candidates worth subsequent human same-sense assessment. It does not estimate generalization and is not an external test. The official test was neither opened nor used.

The Phase 2A trigger is preserved as context: 0/35 `relevant_same_sense`, 5/35 `partially_relevant`, 30/35 `irrelevant`, and 0/7 strict-positive examples, yielding the already-published `EXTERNAL_KB_EXPANSION_REQUIRED`. No Phase 2A result was recomputed or altered. The required SHA-256 of `MODULE3_PHASE2A_RESULTS.md` was verified before and after preparation as `b8bcfee1b093e776e8cbfd3fbee6a2e5b6fae9dd5eb733b277a31b98ec6c2d30`.

## 2. Frozen external-source acquisition

Only the following sources were admitted:

- Princeton WordNet 3.1, first-priority source; WordNet License.
- English Wiktionary exact pages for the seven terms, fallback source; CC BY-SA 4.0 and GFDL.

No verified local WordNet 3.1 snapshot was present. The available NLTK WordNet archive identified itself as version 3.0 and was rejected. One fixed official WordNet 3.1 archive was therefore downloaded from `https://wordnetcode.princeton.edu/wn3.1.dict.tar.gz` on 2026-08-27. The archive contained 16,358,468 bytes and has SHA-256 `3f7d8be8ef6ecc7167d39b10d66954ec734280b5bdcd57f7d9eafe429d11c22a`. The license reference is `https://wordnet.princeton.edu/license-and-commercial-use`.

Exactly seven official MediaWiki API requests retrieved the exact English Wiktionary pages. Each raw API response was saved in the external temporary directory and hashed before extraction. To honor the fixed five-artifact boundary, the raw payloads were removed with that temporary directory after their immutable revision metadata and hashes had been recorded in the source manifest and associated snapshot records.

| Term | Page ID | Revision ID | Revision timestamp | Raw bytes | Raw-response SHA-256 |
|---|---:|---:|---|---:|---|
| preciosity | 639893 | 92192861 | 2026-08-24T04:42:49Z | 7,307 | `75a3105b1bbfa1de4d3b96a211e56c24f79a19edfaba6f556ce0f349de19c0f5` |
| bandslash | 4079032 | 81279567 | 2024-08-19T03:40:44Z | 2,026 | `097a108a50d3633e52fa4d15e63a31a8130d7492431f7b88e84463ca10937544` |
| nonentertainment | 2472071 | 81109404 | 2024-08-18T23:11:54Z | 1,026 | `ab334c6ecff63ccfd4ba03736c90086d36a30f197ed4bb0ae1c5dc1b9270ad19` |
| continuous | 8891 | 92174256 | 2026-08-24T01:13:06Z | 12,020 | `7efd37de0f03721292862952498d352e67afc69c9bd40efd6465730d55990c69` |
| foreboding | 67999 | 92124742 | 2026-08-23T00:44:26Z | 4,031 | `f728651f7485adbdac121ed00213dca19632102a3087ea87d1bc8549c40ea198` |
| tetaniform | 4216675 | 82053369 | 2024-09-28T04:33:30Z | 412 | `ffb3507c31b8aa1476237ff151e4f2cf20fe3e72d46e045051bf5b798cb58f3f` |
| keen | 38950 | 92333256 | 2026-08-26T10:05:26Z | 20,616 | `016ab4694299c13c78fb3e059a15e932ac879fca077f1e04936f0dc24c166190` |

Acquisition accounting is exact: 8 HTTP GET requests in total (1 WordNet and 7 Wiktionary), 0 redirects, 0 general-web searches, and 0 other network requests. All later extraction, deduplication, ranking, locking, joins, and validation were offline. No Wikipedia, search-engine snippets, commercial dictionary, whole Wiktionary dump, Gemini, other LLM/API, FAISS, or vector database was used.

## 3. Leak-free candidate generation and selection lock

The retrieval and selection view materialized exactly `example_id`, `term`, and `src`. Its canonical input SHA-256 is:

```text
c44b5ec9c73bed5f5d8682b82c907e2472e34464c0769d03b316e1ef0eafa593
```

For each term, preparation extracted every exact-lemma English sense present in WordNet 3.1 and every English lexical sense on the exact Wiktionary page. It did not use approximate spellings, related terms, nearest neighbours, or padding. Deterministic external deduplication required equality of the NFKC/casefold/whitespace-normalized candidate term, definition, and usage example.

Previous canonical human-completed CSVs were consulted only through their first nine non-annotation columns to identify already-seen exact normalized candidate definitions within the same example. In total, 158 rows were scanned, 138 belonged to the seven-example scope, and 0 annotation fields were accessed. No AI-completed annotation file was opened. No previous human label was copied to the Phase 2B artifacts.

When at most five eligible senses remained, all were retained without padding. When more than five remained, the already-local frozen `sentence-transformers/all-mpnet-base-v2` snapshot `e8c3b32edf5434bc2275fc9bab85f82640a19130` ran on CPU with `local_files_only=true` and `max_seq_length=256`. The query text was `term + "\n" + src`; candidate text contained term, part of speech, definition, and usage example. Ranking used cosine similarity and deterministic tie-breaking by WordNet-before-Wiktionary source priority, original sense order, and stable evidence ID.

An initial offline pass was discarded before any project output after parser QA exposed incomplete handling of nested Wiktionary markup. The parser was corrected without inspecting `tgt` or any relevance label, and the same frozen retrieval configuration was rerun. Honest model accounting across both passes is: 2 selection-pipeline executions, 2 local model loads, 4 encode calls, 6 query texts, and 70 candidate texts. The final frozen pass accounts for 1 model load, 2 encode calls, 3 query texts, and 35 candidate texts. There was no model download or package change.

The ordered selected payload was locked before `tgt` was materialized:

```text
selection_sha256 = 13b2b66d5cfc52896fadda0c5381d21c8c9bfd6019073e679af68c53853a00c3
tgt fields materialized before lock = 0
tgt used for retrieval, filtering, ranking, sense selection, or deduplication = false
```

Only after verifying this hash was the reference-assisted `tgt` field joined into the blinded CSV. Its presence supports later human reference-assisted annotation; it is not external-validation evidence.

## 4. Candidate and coverage accounting

The immutable external snapshot contains 44 lexical source records: 13 WordNet 3.1 senses and 31 English Wiktionary senses. Three candidates were excluded because their normalized term and definition exactly duplicated a candidate in a prior canonical human artifact; their prior labels were neither accessed nor included. No exact duplicate existed within the external snapshot. Of the 41 eligible candidates, 21 were selected and 20 were excluded only by the top-five rank limit.

| Term | WN senses | WKT senses | Prior-human duplicate exclusions | Eligible | Selected WN | Selected WKT | Selected total | Rank-limit exclusions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| preciosity | 1 | 4 | 2 | 3 | 1 | 2 | 3 | 0 |
| bandslash | 0 | 1 | 0 | 1 | 0 | 1 | 1 | 0 |
| nonentertainment | 0 | 1 | 0 | 1 | 0 | 1 | 1 | 0 |
| continuous | 2 | 6 | 1 | 7 | 2 | 3 | 5 | 2 |
| foreboding | 3 | 4 | 0 | 7 | 2 | 3 | 5 | 2 |
| tetaniform | 0 | 1 | 0 | 1 | 0 | 1 | 1 | 0 |
| keen | 7 | 14 | 0 | 21 | 0 | 5 | 5 | 16 |
| **Total** | **13** | **31** | **3** | **41** | **5** | **16** | **21** | **20** |

The three hidden duplicate records are: two Wiktionary senses for `preciosity`, matching prior evidence IDs `15708` and `17462`, and one Wiktionary mathematical sense for `continuous`, matching prior evidence ID `17226`. The hidden provenance records only the duplicate relationship and explicitly records `previous_labels_included=false`.

## 5. Blinding and provenance boundary

The blinded CSV has exactly 21 data rows and the required 12 columns. It uses UTF-8 with BOM and standard CSV quoting. The last three annotation columns contain 63/63 empty cells. Its stable order is the fixed seven-example order, then retrieval rank, then evidence ID. It contains 21 unique `annotation_id` values, 21 unique `evidence_id` values, and 21 unique example/candidate tuples.

The blinded view contains only:

```text
annotation_id, example_id, term, src, tgt, evidence_id,
candidate_term, candidate_definition, candidate_context,
relevance_category, annotation_confidence, annotation_notes
```

It contains no source name or URL, WordNet/Wiktionary marker, similarity score, retrieval rank, revision identifier, prior label, AI label, or suggestion. The provenance is hidden from the annotator. Its 44 records consist of 21 selected candidates, 3 prior-human exact-duplicate exclusions, and 20 rank-limit exclusions. Filtering its `record_type` to `selected_candidate` gives an ordered 1:1 join to all 21 blinded rows through `annotation_id`, `example_id`, and `evidence_id`; every provenance record also joins to exactly one stored external snapshot record by `evidence_id`.

The existing unmodified `RAG/tools/relevance_annotation_ui.html` accepts the exact 12-column schema, arbitrary positive row counts, blank annotation fields, unique IDs and unique `(example_id, evidence_id)` pairs. It therefore accepts this 21-row file. When used later, it will export `module3_phase2b_external_kb_blinded_human_in_progress.csv` and `module3_phase2b_external_kb_blinded_human_completed.csv`. Only the blinded CSV—not the provenance or source manifest—is intended for the annotator.

## 6. Frozen Phase 2B stop rule — recorded, not applied

Before any Phase 2B annotation, the following rule is frozen:

- If at least 4/7 examples obtain one or more `relevant_same_sense` candidates, the subsequent decision may be `PROCEED_TO_FINAL_GATED_RAG`.
- If fewer than 4/7 examples obtain a strict candidate, the subsequent decision must be `CLOSE_RAG_AS_CONTROLLED_NEGATIVE_RESULT`.

This preparation does not count strict-positive examples, calculate human metrics, or apply the rule. No Phase 2B decision has been produced.

## 7. Integrity and validation

Independent validation confirmed:

- 7/7 fixed development examples and no official-test access;
- 44/44 unique snapshot evidence IDs and 44/44 source/provenance joins;
- 21/21 blinded rows, 12/12 exact columns, and 63/63 blank annotation cells;
- 21/21 unique annotation IDs, evidence IDs, `(example_id, evidence_id)` pairs, and normalized example/candidate tuples;
- 21/21 ordered blinded-to-selected-provenance joins;
- 0 candidates generated by an LLM and 0 AI annotations opened or used;
- `tgt` materialization only after verification of the frozen selection hash;
- generic offline UI compatibility without changing the UI;
- unchanged hashes for all 11 recorded input artifacts before and after preparation.

The four data artifacts already fixed when this plan was written are:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `external_kb/MODULE3_PHASE2B_SOURCE_MANIFEST.json` | 16,758 | `9d91c599fabbd6782e92b13cb7f8fa6e2f984c464242b02a578792d1de893ece` |
| `external_kb/module3_phase2b_external_kb_snapshot.jsonl` | 39,483 | `87356e9c2d6ae8893767c55c66901ce9449f15605d5eb8b5c7c25b687ddd4825` |
| `annotation/module3_phase2b_external_kb_blinded.csv` | 9,576 | `5601166860ca7d37872720b0188f590ac3684b71e84003bced1f654d796c05fe` |
| `annotation/module3_phase2b_external_kb_provenance.jsonl` | 50,886 | `8b34a6805f0f8f73b8d9cd86b730d175e7617fd4f0e9a8badb2408abdfad4a4d` |

The plan's own hash is reported after file closure so that it is not self-referential.

## 8. Artifact hygiene and scientific limitations

Exactly the five authorized Phase 2B preparation artifacts were created. No new UI, notebook, metrics file, results report, cache, duplicate CSV, or project-local script was created. Existing Module 1, Module 2, Module 3 Phase 0/1/2A, E1–E4, human annotations, and experimental artifacts remained unchanged.

This is a small, development-only, reference-assisted diagnostic. Exact lexical lookup can miss multiword, morphological, encyclopedic, domain-specific, or absent lexical senses. The top-five cap can also omit a valid sense when a page contains many senses, while the local semantic ranker is not a word-sense verifier. Wiktionary content is revision-specific and community-edited. Subsequent relevance judgments will come from human annotation, but no Phase 2B annotation has yet occurred. Accordingly, this preparation supports only a controlled coverage check and no claim about downstream RAG safety, superiority, or generalization.

Final preparation accounting: official test accesses 0; AI annotations opened/used 0; annotation labels created 0; Phase 2B metrics 0; Phase 2B decisions 0; Gemini/LLM/API calls 0; package changes 0; model downloads 0; existing experimental artifacts modified 0.
