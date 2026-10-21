# Private integration and future publication

> Historical private-integration record, retained for traceability. Its references to Git ancestry, staging counts and private push describe the source repository, not this file-only candidate. No Git history or identities were copied. See the [current release review](PUBLIC_RELEASE_REVIEW.md). Do not change the private repository's visibility.

This tree integrates the E1-E11 implementation into the existing Git ancestry. The remote repository was confirmed private during preparation. No commit, push or visibility change was performed in this phase.

The current source tree and the reachable Git history have separate privacy assessments. The known historical exposure remains a **PUBLICATION BLOCKER**: 38 reachable blobs contain personal local paths. Author/tagger metadata also require review in any future public release. No tokens or private-key signatures were identified by the scoped history scan; this is not a guarantee about every possible secret.

Changing repository visibility to PUBLIC is prohibited until a separately approved audit and remediation of historical personal information across **all branches and tags** is completed. Keeping this repository private does not authorize adding unnecessary private information to its current tree. No history rewriting was performed.

Four inherited thesis drafting/QA documents were removed from the current tree after verifying their full historical blobs and private preservation copies. They contain no implementation source. Eleven other inherited files were retained: five Git attribute policies, five narrowly amended ignore policies, and one empty historical log. The public integration manifest records all 15 decisions without reproducing personal paths from document contents.

All 15 approved notebooks, RAG Modules 1-4, E1-E11 source/configuration/evaluation files, the independent solution snapshot, 23 historical snapshots and the recovered MPNet test remain. Full datasets, private predictions, weights, environments and private audit records are excluded.

The known historical E8 report syntax error remains documented; `RAG/results/rag_e8_rf_tuning_v1/scripts/report_e8_render_fixed.py` is the separately retained corrected renderer. No model code or evaluation was run. Frozen artifacts and the environment required for reproduction are obtained separately under their applicable permissions.

No project-wide license has been selected. Existing third-party notices remain in place. A project license and dataset/third-party rights must be resolved before public release. Commit and private push each require explicit approval after review.

`manifests/file_inventory.public.json` describes this integration tree. `manifests/source_provenance.public.json` distinguishes original artifact hashes from current public-safe derivatives. Earlier PHASE 3C.1 reports describe the upstream publication candidate; its originals remain unchanged.

Git attributes preserve exact reviewed bytes and recognize CRLF line endings. The staged whitespace check still reports 275 pre-existing findings in 24 unchanged upstream files (271 trailing-space findings and four blank final lines). These include Markdown formatting and historical source. They are recorded for commit review; source bytes were not reformatted and the check is not claimed to pass.
