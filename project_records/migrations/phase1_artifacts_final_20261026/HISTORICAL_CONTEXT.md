# Contemporary reading guide for the preserved Phase 1 records

Date: 2026-10-26. This guide explains archival context; it does not amend the
historical records or authorize experiment execution.

## Four historical Markdown reports

The following original files all lived in codex/ and are moved together,
byte-for-byte, to project_records/thesis_verification/phase1_protocol_history/:

- chapter6_audit.md
- chapter6_conflict_report.md
- source_map.md
- thesis_integrity_audit.md

These reports describe earlier thesis-writing and protocol decisions. They are
not current execution instructions or the current project source map. In
particular, source_map.md and thesis_integrity_audit.md include statements that
RAG was future work/not implemented, older TODOs and earlier document titles.
Those statements belong to their historical stage; they must not be read as a
description of the final E1-E11 implementation. Later E10 retrospective work is
not invalidated by an older report saying no final authorized test run existed
at that earlier point. Preserve these records rather than silently modernizing
their claims or metrics.

The reports contain inline code citations, not active relative Markdown links.
Moving a document nevertheless changes the filesystem base someone might
incorrectly assume for those citations. **Do not reinterpret a literal citation
as relative to the new archive directory.** Keep the original codex/ document
context and distinguish repository-root citations from document-relative ones.

Examples of paths retaining the old context:

- canonical_cv_outputs/... and canonical_feature_outputs/... in chapter6 reports
  refer to the original codex/ artifact context, not new folders inside the archive.
- evaluation_protocol_decision.md, evaluation_data_manifest.md and
  methodology_component_manifest.md remain under codex/. They are not moved here.
- chapter6_conflict_report.md and source_map.md, when cited as sibling filenames,
  are now siblings in the same four-file archive cohort.
- Paths beginning data/... in source_map.md cannot all be assumed to mean the
  repository root: for example, the cited final-implementation notebook exists
  under codex/data/... in this checkout. Other historical citations may name
  external/private or no-longer-included inputs. A missing citation target is not
  permission to create it, duplicate a notebook or substitute a different variant.
- Earlier checked_thesis(...).docx filenames and their hashes refer to earlier
  document versions. They do not identify the current protected thesis PDF/DOCX.

candidate_recheck.json records all 133 extracted filename/path code citations with
old-document-relative, new-document-relative and repository-root existence probes.
inline_reference_resolution.json retains the contextual old path and maps any
actually relocated targets without modifying the historical text. Existence
probes are diagnostic evidence, not proof of intended path semantics. No symlink,
compatibility duplicate, canonical-artifact move or frozen-record edit is needed.

## Three CSV records

development_experiment_summary.csv remains one combined E1-E4 table. Its new
location is:
research/experiments/phase1_baselines/e1_e3_baselines/results/development_499/development_experiment_summary.csv.
The table includes E4 as diagnostic-only, with selection_eligible=No. Its
development-499 values are preserved historical results, not canonical-561 values.

The ratio and weight CSVs belong to the earlier Trial + Synthetic sweeps evaluated
using labeled-test-derived features. Their new locations are under
research/experiments/phase1_baselines/e4_augmentation/historical_ablation/.
Do not use those scores as canonical development results or evidence of an
unseen/pristine test-set evaluation. No metrics or protocols are changed.

E10 recovery_audit/finalize_audit.py reads the distinct original paths
codex/data/7. Ablation Synthetic Data/ablation_synthetic_ratio_results.csv and
codex/data/7. Ablation Synthetic Data/ablation_synthetic_weight_results.csv.
This migration relocates only the public data/7. Ablation Synthetic Data/... files.
There is no reparse-point alias between those namespaces. E10's codex/data targets
were already absent and remain absent. Identical recorded SHA-256 values do not
authorize substituting the public archive for E10's original input paths or
rewriting the E10 records. That existing prerequisite gap is not repaired here.

## Future notebook execution and verification records

The RAG notebook's summary writer uses a basename relative to kernel CWD. The
historical ablation notebook writes ratio/weight results through DATA_DIR:
Path.cwd() when the expected evaluation feature input is there, otherwise the
SHROOM_PROJECT_ROOT/data/7. Ablation Synthetic Data fallback. The unchanged
producers can recreate outputs at old locations if run with suitable inputs.
No notebook was run, and no old-path duplicate was produced during this phase.

Future replay remains BLOCKED pending separate approval and proof of an external
per-run sandbox/launcher. It must pin read-only inputs, inspect resolved outputs
and fallbacks, deny repository/archive writes, and retain generated outputs in a
new run directory for independent comparison. CWD alone is insufficient. Never
automatically replace or merge historical outputs. Runtime isolation and numerical
reproduction are NOT VERIFIED here; no such mechanism was implemented.

Old public-release inventories, detached checksums and provenance records remain
unchanged historical layout records. They are not current-layout validation
manifests. Earlier audit helpers and release builders are one-shot tools for their
recorded stage, not active E1-E11 consumers. Do not rerun them against the
reorganized tree, refresh frozen hashes, or regenerate the release to hide path
changes. The release builder also rejects a Git checkout. A future approved
integration phase must produce a separate current-layout inventory and update
only live documentation links, keeping original records intact.

Inline old-layout citations in E10 PRIOR_TEST_USE_AUDIT.md, methodology records,
previous audits and the root README are documentation/provenance history or
deferred navigation work, not a newly broken runtime dependency. They were not
edited. No ADAPT/KEEP/BLOCKED path is moved by this phase.
