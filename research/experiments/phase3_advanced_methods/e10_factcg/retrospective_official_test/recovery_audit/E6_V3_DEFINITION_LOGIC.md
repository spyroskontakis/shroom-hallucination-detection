# Frozen E6-v3 / E10 definition logic

This is source inspection only. No feature extraction, inference, fit, scoring, network retrieval or Modal execution was performed.

## Source chain

Paths below are relative to the repository. Their frozen hashes are verified in `VERIFICATION.json` against the preceding feature manifest.

- `RAG/scripts/module4_build_external_lexicon.py`: `extract_dm_term`, `term_key`, `parse_wiktionary_html`, `deduplicate`.
- `RAG/results/rag_module4/continuation_v1/scripts/module4_build_wiktionary_lexicon.py`: acquisition and offline reconstruction.
- `RAG/results/rag_module4/continuation_v1/mpnet_provenance_v2/scripts/module4_build_rag_features_pinned.py`: seven original RAG features.
- `RAG/results/rag_e6_v1/scripts/build_features.py`: ranking reconstruction and definition/hypothesis features.
- `RAG/results/rag_e6_v2/scripts/nli_backend.py`: second NLI backend.
- `RAG/results/rag_e6_v3/scripts/hhem_backend.py`: HHEM definition feature.

## Term and external text

Only DM is applicable. `extract_dm_term` strips the source string, takes the first case-insensitive, dot-all `<define>...</define>` match and strips its contents. Its legacy fallback splits on `<define>` and takes the middle part when available. Empty terms are not applicable. The acquisition key uses Unicode NFKC, whitespace collapse and casefold.

The accepted external snapshot is **English Wiktionary only**. Historical WordNet and internal SHROOM evidence are not substitutes. The acquisition script queries the page with redirects enabled, records the revision ID/timestamp/SHA1, and requests parsed HTML for that immutable `oldid`. Saved revision and parse JSON files are reused. Acquisition was live at resource creation; feature construction reads the resulting local frozen snapshot, not current pages.

The HTML parser enters the English section and stops at the next language heading. It tracks allowed part-of-speech headings, extracts direct list-item senses from definition lists, removes nested examples/lists/tables/style/script/reference/citation elements, HTML-unescapes the text, and applies NFKC plus whitespace normalization. Each retained sense has a plain `candidate_definition`, a `candidate_context` of `POS: definition`, and a revision/POS/sense-based `source_entry_id`. Duplicate normalized term/definition keys are consolidated deterministically; provenance is retained. This is not a single manually chosen dictionary definition.

## Multiple senses and ranking

Candidates are matched by the frozen term key. Retrieval embeds `term + "\n" + src` against `candidate_term + "\n" + candidate_context`. Neither hypothesis, target nor labels enter the ranking. The frozen MPNet embeddings are float32; the ranking code converts to float64, renormalizes with an epsilon floor, and uses dot products. Ties are broken by `source_entry_id` then `evidence_id`; up to five senses are retained.

The original seven features use evidence availability/count/top-1 retrieval similarity plus maxima across the selected definitions compared with `tgt`: cosine, NLI entailment, NLI contradiction and lexical Jaccard. Lexical comparison uses normalized, casefolded word-token sets. Definition text is compared without its POS prefix. The E6 additions use the **rank-1** definition against `hyp`; they do not maximize these channels across senses. E6-v1 reconstructs this ranking from frozen evidence; its historical checks establish aggregate consistency, not possession of an original per-example ranking archive for new test rows.

## Missing definitions

Non-DM, non-applicable or no-candidate rows receive the pipeline's zero fallback for definition channels. Acquisition separately distinguishes confirmed `NO_SENSE_FOUND` from `SOURCE_REQUEST_FAILED` and successful `SENSES_FOUND`. Missing cache files for an unacquired test term do **not** establish that Wiktionary had no definition. Applying zeros to all 557 unknown terms would silently change the evidence protocol.

## E10 feature dependency

Exactly 15 of the 37 E10 columns depend on this resource:

| Group | Exact columns |
|---|---|
| Original RAG (7) | `rag_evidence_available`, `rag_sense_count`, `rag_retrieval_top1_cosine`, `rag_target_definition_max_cosine`, `rag_target_definition_max_entailment`, `rag_target_definition_max_contradiction`, `rag_target_definition_max_lexical_overlap` |
| E6-v1 (4) | `rag_definition_hyp_cosine`, `rag_definition_hyp_entailment`, `rag_definition_hyp_neutral`, `rag_definition_hyp_contradiction` |
| E6-v2 (3) | `nli2_definition_hyp_entailment`, `nli2_definition_hyp_neutral`, `nli2_definition_hyp_contradiction` |
| E6-v3 (1) | `hhem_definition_hyp_consistency` |

The remaining 22 columns, including FactCG and reference/hypothesis channels, do not require this dictionary resource. MPNet is pinned to `e8c3b32edf5434bc2275fc9bab85f82640a19130` (max length 256); first NLI to `microsoft/deberta-large-mnli@7296194b9009373def4f7c5dad292651e4b5cf4e` (512); NLI2 uses its frozen backend/config (512, longest-first); HHEM uses `58383384656cbaec2949a75a41f20e891e90a73b` (512, sigmoid once). Retain the full existing feature manifest for all backend settings; no alternative implementation is proposed here.

## Exact reconstructibility

Frozen acquisition evidence exists for `marrow` (revision 91472322; seven senses) and `bountiful` (revision 89284011; one sense), covering **2/563** official DM examples. The other **557 distinct terms cover 561 DM examples**. No qualifying frozen content was recovered for them. A stored internal example definition is insufficient: exact reconstruction requires the original external sense set, text and provenance that determine ranking.

The count 2 is **resource-level reconstructibility**, not a claim that two complete 37-column test vectors were generated or numerically verified. No test feature vectors were built. MT/PG have non-applicable definition channels, so dictionary absence does not block their 937 examples. A resource-eligible strict subset would therefore contain at most 939/1500 examples, subject to all other frozen-feature checks.
