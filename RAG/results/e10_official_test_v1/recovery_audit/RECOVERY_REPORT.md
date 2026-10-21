# E10 official-test prerequisite recovery

**RECOVERY STATUS: C. EXACT RECOVERY IMPOSSIBLE with the locally available frozen material.**

The strict training proposal contains 547 examples after 14 MT source/target-pair exclusions. All removed hypotheses differ from their matching test hypotheses; no exact example is shared. See the strict manifest and MT overlap audit for all IDs and indices.

## Recovery search

The search included ignored local files, all repository experiment/cache/raw-source/manifest directories, cleanup backups, previous runs, notebook source/output JSON, text/HTML, package archives, all branches/tags/remotes/reflogs, historical blobs, and unreachable Git blobs. `SEARCH_INVENTORY.json`, `SUPPLEMENTARY_SEARCH.json` and `GIT_UNREACHABLE_INVENTORY.txt` record scope and evidence. The first pass examined 375 archive objects, 2,606 archive members and 611 historical Git blobs. The additional pass examined 1,009 unreachable blobs and rescanned local text for generic definition mappings. Counts include repeated/duplicate content; they are not unique recovered resources.

No qualifying frozen material was recovered for the 557 missing terms (561 DM rows). `WIKTIONARY_RECOVERY_TABLE.csv` has exactly one row for each missing term, with its required test IDs, verdict, and available candidate provenance. Blank source/timestamp/hash fields mean that no frozen source was found, not that an empty definition was verified.

The only candidate term, `bottomful`, appears as evidence ID 17437 in three Module3 annotation CSVs. Its candidate context is an internal SHROOM example, the query term is `preciosity`, and it is marked irrelevant in completed annotations. These files provide neither the frozen external sense set nor Wiktionary revision provenance. They are rejected as exact E6/E10 recovery. Their file hashes and available filesystem timestamps remain in the recovery table; timestamps are Unix seconds, not authenticated acquisition times.

Known acquired terms are `marrow` and `bountiful`, covering two DM examples. Their revision/parse hashes were verified against actual local files (`VERIFICATION.json`). Hence **2/563 DM examples have the required frozen lexical material**, while **0 new full test feature vectors have been produced or numerically verified**. The distinction matters: this audit establishes resource coverage, not completed inference.

Scope limitations are explicit: dependency environments, `.git` working internals (searched separately through Git), and this output directory are excluded from the filesystem content pass. The 21 files over 100 MB are model/optimizer binaries, not lexical text resources. Arbitrary model binaries were not unpickled. No archive-reader errors occurred. Referenced raw source names and hashes are retained in the scanned manifest inventory; no manifest establishes a historical acquisition for any of the 557 missing terms. There is no claim to have searched unavailable remote storage or files outside this repository.

## Exact feature logic

See `E6_V3_DEFINITION_LOGIC.md`. Fifteen of E10's 37 features depend on the frozen dictionary sense set. Unknown acquisition cannot be silently interpreted as confirmed absence and zero-filled.

## Permissible alternatives, not executed

**Option 1 — strict frozen evaluation.** Restrict evaluation to examples for which all frozen features can be reconstructed. Dictionary coverage permits at most 939 examples (937 MT/PG plus 2 DM), pending the remaining feature checks. This is a strongly task-skewed subset and cannot yield an official 1,500-example leaderboard-comparable score. Report its composition and scope explicitly.

**Option 2 — reconstructed retrospective evaluation.** With a separate explicit decision, acquire missing terms using the SAME Wiktionary procedure: identical term extraction, redirects/revision capture, revision-bound parsing, English/POS extraction, normalization, deduplication, ranking and downstream feature definitions. Only the acquisition population needs extending beyond the original development terms. Preserve existing frozen content and save new content/provenance separately. Today's dictionary content may differ, so this is a documented deviation from frozen E10, even if the code is unchanged. Do not describe it as exact frozen reproduction or as an independent test evaluation.

Recommendation: keep the full evaluation blocked; select and document one alternative before any execution. No live retrieval was attempted here.

## Prior exposure

See `PRIOR_TEST_USE_AUDIT.md`: historical official gold inspection, test-derived CV, and synthetic-ratio/weight evaluation are directly evidenced. The historical 1,500-row feature CSV matches the official input IDs/texts. Later development-only fits do not restore independence. Test-input overlap filtering also directly affects the shared canonical training population. Use **retrospective evaluation on the official labeled test set**.

## Preservation and actions

All new work is confined to this recovery directory. Existing parent audit checksums and frozen source hashes pass; the inventoried existing files retain size and modification time. No training, inference, test scoring, new predictions, Modal, live retrieval, commit or push occurred. See `TEST_RESULTS.txt` for offline validation and `SHA256SUMS.txt` for the resulting audit artifacts.
