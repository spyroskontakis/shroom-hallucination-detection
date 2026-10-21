# E10 official-test retrospective evaluation — Phases 0–3 audit

**FINAL STATUS: FAIL — preflight incomplete; no training, model inference, Modal execution, predictions or test scoring.**

The canonical pool has no exact official-test example. This is **not** a finding that the 561 rows contain test gold examples. Execution is blocked by unresolved source-pair overlap and incomplete frozen lexical evidence for the new test inputs. Existing E10 results are unchanged.

## Phase 0: origin of the 561 examples

1. **Sources:** the official SHROOM trial release (`trial-v1.json`, 80 rows) and official model-agnostic validation release (`val.model-agnostic.json`, 499 rows). All canonical rows map to their recorded original source index, with identical normalized text, binary label and p(Hallucination).
2. **Validation contribution:** 493 rows.
3. **Trial contribution:** 68 rows. No other source contributes a canonical training row.
4. **Excluded validation rows:** six. Original zero-based indices 418 and 452 form an annotation-conflicting duplicate group. Indices 355, 374, 458 and 483 are exact validation/test overlaps and were removed during historical canonical preparation. They are not members of the 561 pool.
5. **Why 561 rather than 499:** `80 + 499 − 12 duplicate trial rows − 2 conflicting validation rows − 4 validation/test overlaps = 561`. Trial duplicates were dropped in favour of their validation counterparts; annotations were not averaged.
6. **Pre-test public labels:** yes. The official task website identifies the trial release as updated 2 August 2023 and validation as updated 3 November 2023. The official release READMEs describe their human annotations and p(Hallucination). Fresh downloads from the organizers' links match the local source JSONs byte-for-byte, and all 561 retained labels match these sources. This establishes availability of the material; the retrospectively deduplicated 561-row manifest itself is not an official competition split.
7. **Official-test origin:** none. The canonical source mapping contains only validation/trial. A new label-blind text check finds zero `(task, src, tgt, hyp)` overlaps, zero `(task, src, hyp)` overlaps and zero `(task, tgt, hyp)` overlaps against the official test file.

Canonical task counts: DM 211, MT 216, PG 134. The frozen manifest SHA256 is `754b66c6c4eca2e92902d0408db4854e922d7dfb396953a0cc043c5477bd6a9b`.

Official source: https://helsinki-nlp.github.io/shroom/2024.html — organizers' release links, not a third-party mirror. `OFFICIAL_RELEASE_CHECK.json` records the three download URLs, archive hashes, member paths and matching JSON hashes. The labeled test release is dated 2 February 2024 on that page.

## Phase 1: primary training recommendation

**Recommend B: the exact frozen thesis pool of 561 examples**, subject to resolving the preflight blockers below. It preserves the labeled population that selected E10, and all its labels come from public pre-test trial/validation material. This recommendation was made before inspecting any test gold value and is not based on test performance. No RF has been fitted.

**A: strict official development, 499 rows** is a different possible protocol, not an additional run to try. It would change the training population from the frozen E10 experiment. Moreover, its unmodified 499 rows include four exact official-test overlaps. Using 499 unchanged therefore cannot satisfy the requested disjointness condition. Removing them would create a different, explicitly documented protocol rather than “499 official dev only”. Neither A nor B has been executed.

## Phase 2: official test identity and blinding

- Official release and local test JSON match byte-for-byte.
- 1,500 rows; DM 563, MT 562, PG 375.
- 1,500 present and unique official IDs.
- Required input fields `task`, `src`, `tgt`, `hyp` are present and nonempty in all rows.
- Gold key names `label`, `labels`, `p(Hallucination)` are present. **Their values were not decoded, validated or inspected.** Value validation belongs to scoring after predictions are frozen, in accordance with the stronger blinding requirement.
- There are 1,491 distinct normalized full-text keys among the 1,500 official rows. These are repeated text items with distinct official IDs, not duplicate IDs. A future run must retain all 1,500 official rows and must not deduplicate the denominator.
- Test SHA256: `c5c5fe0ce9c402186990b0dde05c0274ac90d10906b169f28d2f2c0cf669f299`.

`audit_data.py` uses a strict input-field allowlist. Values outside it are lexically skipped without JSON-decoding them. Only sanitized dictionaries exist downstream of this projection. The test archives were downloaded and byte-hashed for provenance, without displaying or scoring their gold contents. Five synthetic unit tests passed, including a decoder-observation test confirming that gold values are never decoded.

**Overlap caveat:** 14 canonical MT rows share exactly the same `(task, src, tgt)` with 14 official-test rows, but their hypotheses differ. This is not exact labeled-example contamination; it is shared source/reference content. Consequently the requested no-overlap gate cannot be reported as an unqualified PASS. The matching canonical IDs, original training indices and test IDs are recorded in `OVERLAP_AND_RESOURCE_CHECKS.json`. No rows were silently removed from either population.

## Phase 3: frozen E10 replay and feature provenance

The saved E10 OOF vector was replayed through the existing `e9_common.metric` function, using the saved canonical labels. It reproduced **475/561, Accuracy 0.8467023172905526, Spearman 0.7828092941190203**, exactly. This required zero model calls and zero fits. Feature/OOF SHA256 match the completed E10 report. All first 36 columns of the E10 matrix are numerically identical, in the same order, to E6-v3; the only added column is `factcg_support_probability`. All values are finite. See `E10_DEVELOPMENT_REPLAY.json` and `E10_OFFICIAL_TEST_FEATURE_MANIFEST.json`.

**Resource blocker:** the accepted English Wiktionary acquisition manifest covers 206 terms and the evidence snapshot contains 462 senses for 188 terms. The official test contains 563 DM rows, covering 559 extracted distinct terms. Only two DM rows have a term covered by that acquisition manifest. The other **561 DM rows / 557 distinct terms have no acquisition record**. Absence from this development-scoped cache is not evidence that Wiktionary has no sense for them. Applying the missing-evidence zero fallback to all these rows would silently conflate “never acquired” with “NO_SENSE_FOUND”. Fetching and freezing additional term evidence requires an explicit resource/provenance plan; it cannot be presented as reuse of the unchanged existing lexical snapshot. No new lexical acquisition or substitution was performed.

The legacy NLI/MPNet, NLI2 and HHEM components were frozen with CPU execution; FactCG was frozen with CUDA float32. A future Modal adapter must preserve these numerical semantics or document and validate any device/runtime change before inference, rather than silently replacing all backends with a single new GPU implementation. No such adaptation or model smoke inference was attempted after the failed preflight.

## Historical independence limitation

`codex/evaluation_protocol_decision.md` already documents earlier exploratory use of the labeled official test set in historical artifacts and use of test text for canonical overlap filtering. The new run would be a **retrospective evaluation on the official labeled SHROOM test set**, not an official submission and not a pristine independent test. No new test gold was inspected during this audit. No leaderboard placement or test performance is reported.

## Read-only sources

Paths are relative to ``:

- `codex/canonical_evaluation_data_prep.py`
- `codex/canonical_human_development_manifest.csv`
- `codex/duplicate_group_audit.csv` (training-source duplicate metadata)
- `codex/evaluation_protocol_decision.md`
- `Dev/SHROOM_dev-v2/README-v2.txt`
- `Trial/SHROOM_trial-v1.1/README-v1.1.txt`
- `RAG/results/phase3_e11_task_adaptation/E11_DATA_AUDIT.md`
- `RAG/results/rag_e6_v1/E6_PROTOCOL.md` and `scripts/build_features.py`
- `RAG/results/rag_e6_v2/E6_V2_PROTOCOL.md` and `scripts/nli_backend.py`
- `RAG/results/rag_e6_v3/E6_V3_PROTOCOL.md`, `config/run_config.json`, `features/e6_v3_36_features.csv`, `scripts/hhem_backend.py`
- `codex/canonical_feature_extraction.py` and `codex/canonical_feature_outputs/canonical_feature_extraction_metadata.json`
- `RAG/results/rag_module4/continuation_v1/mpnet_provenance_v2/scripts/module4_build_rag_features_pinned.py`
- `RAG/results/rag_module4/continuation_v1/schannel_run_v1/module4_external_lexical_snapshot.jsonl`
- `RAG/results/rag_module4/continuation_v1/schannel_run_v1/module4_dev_term_manifest.csv`
- `RAG/results/phase3_e9_claim_verification/factcg_gpu/GPU_RUN_MANIFEST.json`, `factcg_backend.py`, `evaluate_e10.py`
- `RAG/results/phase3_e9_claim_verification/features/e10_return/E10.csv`
- `RAG/results/phase3_e9_claim_verification/evaluation/E10/E10_oof.csv` and `E10_metrics.json`
- `RAG/results/phase3_e9_claim_verification/scripts/e9_common.py`

The gold-bearing rows of `excluded_human_test_overlaps.csv` were not inspected; only its header was read. The overlap evidence above was computed independently from sanitized test text.

## Disposition

The “all checks PASS” condition has not been met. Stop before Phase 4. No GPU command was launched, no final RF was fitted, no predictions were generated, and no official-test score exists. The existing experiment directories and thesis DOCX were not modified. No commit or push.

Publication note: the referenced organizer README files remain in the protected research archive; obtain them from the authorized SHROOM distribution. They are not included in this candidate because redistribution permission was not established.
