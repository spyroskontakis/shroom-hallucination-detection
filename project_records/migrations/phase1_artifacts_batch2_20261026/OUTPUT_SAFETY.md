# Historical output safety gate - Phase 10

Recorded before the new archival moves, 2026-10-26. No execution authorized.

The Phase 9 ablation notebook still writes its five aggregate CSVs to DATA_DIR.
Cell 2 chooses Path.cwd() only when the evaluation feature input is found there;
otherwise it falls back to SHROOM_PROJECT_ROOT (default '.') plus
data/7. Ablation Synthetic Data. Cells 12, 14, 16 and 24 create the five aggregates.
Thus a later run with restored inputs can recreate old-path outputs beside the
moved historical archive. Setting CWD alone cannot guarantee isolation because
the input-existence fallback changes DATA_DIR. No producer was changed or run.

The five development-499 tables selected for Phase 10 have the same general risk:
RAG/shroom_ensemble.ipynb cells 118 and 133 write basenames in CWD; cell 142 sets
OUTPUT_DIR=Path('.') and writes e3_cv_path; cell 164 writes e4_cv_path and
e4_task_path. Static inspection of these aliases across the notebook finds only
assignment, to_csv and printed-path uses, not input readers. The combined summary
uses in-memory results rather than reading these CSV files. The detailed cell
sources and aliases are preserved in producer_review.json and supplementary_review.json.

This is a future regeneration hazard, not an observed broken input dependency or
loss of archived results. The selected archival renames may proceed independently
of replay. **Future notebook replay is BLOCKED pending a separate execution plan.**
This document records that gate; it does not implement an execution sandbox.

Before any separately authorized rerun:

1. Preserve the historical source, archive SHA-256 and original scientific context.
2. Review a launcher that uses a fresh external run directory and read-only copies
   of authorized inputs. Do not launch from either Git repository or an archive.
3. Resolve every input/output path and DATA_DIR fallback before execution. Deny
   writes outside the per-run sandbox; fail if a repository/archive path is selected.
   A future approved wrapper may pin paths without editing frozen notebook bytes.
4. Prove that contract with safe synthetic path checks before any real experiment;
   check external dependencies, offline/network rules and generated-artifact exclusions.
   Merely moving a notebook or changing its kernel CWD is insufficient.
5. Keep generated CSVs and row-level predictions in the new run's private output
   directory. Hash and compare aggregates independently; never overwrite, merge,
   automatically mirror, or relabel the historical records.
6. Record differences and obtain approval before any future documentation or source
   adaptation. Do not modify historical expected hashes to certify new outputs.

Keep three contexts separate: historical 499-example development CV; canonical
561-example OOF evaluation; and older labeled-test synthetic ablation. No number,
label, fold, feature or protocol is changed by this migration. Existing ignore gaps
for some OOF/prediction files remain pending; no such output is generated here.
