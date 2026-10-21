# E8 publication audit — 2026-09-12

PASS. Publication of the already completed experiment; no new fits, inference, retrieval, hyperparameter selection or experiment evaluation. The read-only saved-artifact audit was completed on 2026-09-11 and its hashes were checked again before publication preparation.

Verified result: **452/561; Accuracy 0.8057040998217468; Spearman 0.7528866687040761**. Features: 25. Historical RF fits: 95; historical OOF suites: 1; additional baseline verification fits: 0. Publication adds 0 fits and 0 experiment suites.

## Scope and reproducibility

The original protocol, result report, source and other approved frozen files are published byte-for-byte. Statements in those reports that no commit/tag/push occurred describe the original experiment's completion, before this separately authorized publication. No historical baseline or result is rewritten.

18 original files plus 11 publication-only additions are approved: **29 published files**. Local-only originals: **33** (0 class B, 33 class C). The complete original-file classification, byte sizes and SHA-256 values are in publication/artifact_inventory.json. Publication additions are explicitly allowlisted in .gitignore. .gitattributes preserves original bytes, including CRLF, so published frozen-file hashes remain meaningful.

Class B contains model weights/caches/dependencies/temp files. Class C contains row-level CSV/JSONL, raw text, per-ID error lists and local provenance/diagnostics. They are neither staged nor force-added. The raw matrices, OOF predictions and split IDs remain available locally. A fresh clone is not self-contained: exact execution/auditing requires the authorized local data and dependencies referenced by the original manifests. Do not rerun completed experiments to obtain publication output.

The initial staged whitespace check identified an existing final blank line in frozen scripts/e8_common.py. A file-specific .gitattributes exception disables only blank-at-eof for that file; other whitespace checks remain enabled. The source and its recorded SHA-256 are unchanged.

publication/configuration.json is an explicitly labeled publication view of config/configurations.json; only runtime.executable is omitted. All RF parameters, feature names/order, versions and methodological settings are retained. The frozen original remains local and unchanged, and its SHA-256 is recorded. publication/aggregate_metrics.json preserves the original aggregate values and omits only corrected_ids and introduced_error_ids. Manifests refer to both published and withheld files; a filename/hash reference does not include that file's content.

## String, security and size review

The reviewed src/hyp occurrences are field names, direction descriptions or artificial test fixtures, not SHROOM source/candidate strings. No HDEV_/HTRIAL_ sample identifiers were found in the approved original files. Frozen files containing the personal Python executable path are withheld rather than edited. Source defaults such as external-artifacts/local-0fb664776e02/Windows are safe operating-system references. Upstream model URLs in provenance contain the pinned public revision and no credential.

No credential/private-key/provider-token pattern was found in the approved content. No model, environment, cache, .git helper, raw feature/prediction matrix or file over 50 MB is in the publication allowlist. This is a scoped content review, not a universal guarantee about arbitrary secret formats. Git-internal audit helpers and their local snapshots remain under .git and are not published.

## Integrity and access evidence

557 protected predecessor files match their frozen hashes; 50 completion-manifest files were verified. Canonical IDs, frozen labels and outer folds align across all 561 rows. Accuracy uses the unrounded prediction >=0.5; Spearman uses predictions rounded to 12 decimals and unrounded p_hallucination. Historical integrity records and guarded code/logs report no official-test access; this audit did not open official-test data. These historical process-local logs are not OS-level access proofs.

- Protocol SHA-256: `80e90226cd5cc323d6b649767c615f5d34861637a16af6872bfb8d4ae6f39feb`.
- Original configuration SHA-256: `32a04c03616186388640ff7e9b4e3cf70ad9e2af2401e38dec5a8ea83c3f255e`.

The frozen E6-v3 milestone remains 474/561, Accuracy 0.8449197860962567, Spearman 0.7816945786401444. E6-v2, E6-v3, E6-v4, E7 and E8 artifacts and the unrelated Augmentation Pipeline.txt are preserved. No new experiment is authorized by this publication note.

## Historical E8 baseline and selection

The original baseline is **E6-v1, the 25-feature E6**, at 453/561, Accuracy 0.8074866310160428 and Spearman 0.744420539373989. E6-v3 was not its original baseline. The frozen E8_PROTOCOL.md and E8_RESULTS.md retain the original comparison: 2 corrections, 3 introduced errors, net -1; exact McNemar p=1.0; paired-bootstrap 95% accuracy-difference interval [-0.008912655971479501, 0.0053475935828877]. This is a completed exploratory negative accuracy result.

The fixed grid is C0=(leaf 1, max_features 1.0), C1=(3,1.0), C2=(5,1.0), C3=(1,0.5), C4=(3,0.5), C5=(5,0.5). All other 18-parameter dictionary entries are preserved, with 500 trees and random_state=42. C0 exactly equals the accepted E6-v1 configuration. Each of five locked outer-training sets uses three shared StratifiedKFold inner splits, shuffle=True, random_state=42, stratified by task plus approved binary label. Select pooled inner accuracy, then Spearman, then earliest candidate; undefined Spearman ranks last among equal-accuracy candidates.

Outer folds 1–5 select **C4, C4, C0, C5, C4**. Frequencies: C0=1, C1=0, C2=0, C3=0, C4=3, C5=1. The saved records verify 90 inner fits + 5 selected outer fits = 95, one nested suite and zero baseline verification fits. The read-only audit checked all 15 inner partitions, all 30 pooled inner candidate scores, all five selections and 285 input-array hashes. No CV was rerun. Aggregated inner scores and decisions are published without training-ID lists.

Operational network attempts and access violations were zero in the recorded prepare/evaluate/report guards. The original report_e8.py parse failure is retained, along with the already frozen narrowly repaired report_e8_render_fixed.py and report_render_repair.json; no fit was repeated for that repair. It is a historical rendering issue, not a publication-time code change.

The separate E8_POSTHOC_E6_V3_COMPARISON.md documents the newly requested retrospective saved-OOF comparison. It is not part of the original E8 selection protocol and did not inform redesign or tuning.
