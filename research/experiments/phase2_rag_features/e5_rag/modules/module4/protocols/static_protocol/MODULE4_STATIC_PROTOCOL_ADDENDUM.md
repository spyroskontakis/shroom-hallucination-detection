# E5 Module 4 — Phase 0C Static Protocol Addendum

This addendum resolves `MODULE4_STATIC_PROTOCOL_BLOCKED_PHASE2B_PARSER_NOT_REPRODUCIBLE` prospectively. It does not reproduce or alter the unknown Module 3 Phase 2B parser. It freezes a new Module 4 parser (`module4-external-parser-v1`) before acquisition, model inference, retrieval ranking, labels, predictions, or metrics.

The authoritative definitions are in `MODULE4_EXTERNAL_PARSER_SPEC.md` and `RAG/scripts/module4_build_external_lexicon.py`. The parser is restricted to official WordNet 3.1 and English Wiktionary, exact term lookup, deterministic normalization, deterministic IDs/deduplication, raw-response preservation, and offline byte-identical reconstruction.

Target-dependent feature definitions remain those approved for Module 4: NLI premise is `candidate_definition`, hypothesis is `tgt`; lexical overlap is Unicode-NFKC/casefold token-set Jaccard using `re.findall(r"[^\W_]+", ..., flags=re.UNICODE)`; missing evidence maps all seven features to the frozen zero policy. None of these features is computed in Phase 0C.

Stage A must pass synthetic tests and its specification/script/test hashes must be recorded before Stage B network acquisition. Stage B locks the canonical 561-row label-free view, complete DM-term accounting, raw sources, deduplicated lexical snapshot, and an offline byte-identical rebuild. Any failed source request blocks the final lock.

## Stage A prospective lock

The following values were recorded after 7/7 synthetic tests passed and before any Stage B network request:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `MODULE4_EXTERNAL_PARSER_SPEC.md` | 3,464 | `c7e5d9398c67bebc93dd5d418591da94afb34923fdf6b2a522a6e3579fe6405a` |
| `RAG/scripts/module4_build_external_lexicon.py` | 17,718 | `db6d3a8ffe595ca875d349b074041c7679328fc9f50df4499a943d129411021e` |
| `RAG/tests/test_module4_external_lexicon.py` | 5,802 | `ace643aab5b29fba7e1859241e81db342e8088a362ef6bd44477040d16b764fb` |
| `RAG/requirements-module4-parser.txt` | 23 | `8ea52aa64e76c5e431833b80cb25b8fcd11e6bac3eda9ad36d31e737ca8fd799` |

Stage A test result: **7/7 PASS**. No network request, model load, label access, prediction, or metric calculation preceded this lock.
