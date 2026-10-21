# E7 publication scope

This milestone publishes the reviewed protocols, reports, original source code, available tests, frozen manifests, aggregate metrics and technical provenance. It preserves the experiment's development-only interpretation. Publication does not rerun training, inference, routing or evaluation and does not modify frozen results.

## Local-only artifacts

The repository's existing conservative policy excludes row-level research data. Small canonical-ID/numeric features and OOF prediction CSVs contain no raw prose, but remain local-only in this milestone: no broad permission to redistribute labels or row-level data was inferred. No force-add or broad git add was used. Aggregate metrics may contain a small list of canonical correction/regression IDs; these are identifiers, not raw text or per-row labels.

Raw reference/hypothesis strings, external definitions, routing trajectories, complete train/validation ID lists, row-level features/predictions, detailed operational logs and attachment copies remain local. Generated chunks, caches, temporary files, third-party package copies, dependency wheels and virtual environments are excluded. The per-directory .gitignore is an explicit allowlist.

Original manifests retain hashes and references to excluded files; they describe the complete local experiment, not only this GitHub subset. A fresh clone is therefore **not self-contained**. Reproduction requires separately authorized local data/model assets and, for E6-v4, the separately verified local E6-v3 baseline. E6-v3 has no verified commit/tag in this repository at publication time and requires its own future freezing step; this milestone does not create one.

## Review evidence

Inventory before publication metadata: A=31 reviewed files; B=0 generated/cache/environment files; C=44 per-row/raw/local diagnostic artifacts. No file over 50 MB is included. Candidate code/text was scanned for private keys, service/API credentials and common provider-token formats, with no findings. This is a focused automated/manual publication review, not a guarantee that any secret scanner can establish universally.

Unnecessary full diagnostic dumps and local environment copies remain excluded. Absolute paths retained in frozen configuration, aggregate-runtime provenance and compatibility traceback documentation identify the exact tested interpreter/cache or explain the failure. They are not credentials; they were reviewed and retained to avoid silently rewriting frozen evidence. Local path layouts may need adaptation in a separately authorized reproduction.

`publication_manifest.json` records exact hashes of the published original artifacts and this publication documentation. `publication_verification.json` records fresh read-only OOF/hash checks. Original experimental manifests are historical snapshots and are not rewritten to include publication metadata. No dataset, third-party model/package code, weight, credential or new experimental variant is published.

The original `Augmentation Pipeline.txt` remains untouched and untracked. Prior untracked E6-v2/E6-v3/E8 artifacts are outside this publication. The commits/tags intentionally represent separate E7 and E6-v4 research milestones.

The local `.gitattributes` disables automatic line-ending conversion for this milestone, preserving exact frozen bytes and SHA-256 in Git objects and future checkouts. Original experiment files are not rewritten.
