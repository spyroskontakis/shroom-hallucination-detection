> Historical review, superseded for license status by [PHASE 4D](PHASE4D_REPORT.md). Prior pending copyright/rights decisions below were resolved by the explicit PHASE 4D approval; Git identity and publication remain pending.

# Public portfolio candidate review

> PHASE 4C update: this is a separate final-preparation working copy. The verified 903-file PHASE 4B candidate remains unchanged. See [the final preparation report](PHASE4C_REPORT.md) for current decisions, checks and blockers.

This file-only candidate derives from the reviewed private main. It has no Git history, tags, identities, objects or archives. The private repository and all preservation sources remain unchanged. Creation of a public repository is not authorized by this review.

## Preservation and transformations

All 892 approved source-tree files are represented at their original relative paths. All existing Python, notebook, JavaScript and shell source files remain byte-identical. No experiment logic was changed, and no significant E1–E11 implementation file was omitted. Historical snapshots, failed variants, protocols, tests and aggregate results remain.

The root README now presents purpose, technical work, architecture, E1–E11, development results, separate retrospective test results, an example setup and reproducibility limits. Earlier preservation and integration reports are labeled as historical context. Internal audit documents remain available but are no longer the main navigation path.

The two minimal compatibility diagnostics replace 12 third-party source excerpts and five traceback-frame snippets with source hashes and pinned upstream references. Exceptions, traceback locations, model identifiers, dependency versions and pre-existing hashes are retained. Full original diagnostics remain private. The source excerpt hash is computed from its UTF-8 text; it need not equal an upstream file hash. A version tag/reference is not proof that a locally inspected package was byte-identical to upstream.

[Transformations](../manifests/public_release_transformations.json) record field-level removals. [Release provenance](../manifests/public_release_provenance.json) records original and candidate SHA-256 for every inherited file. No full source file is excluded; Git administration and private artifacts were outside the approved source-tree selection.

## Manifest semantics

[Current inventory](../manifests/file_inventory.public.json) describes this candidate. `SHA256SUMS.public.txt` independently covers every other file, including the inventory; its own hash is reported outside the file to avoid circular hashing.

`source_provenance.public.json` retains earlier origin/transform records and updates the current hash where an inherited public artifact changes. Historical experiment manifests keep their historical hashes unchanged: they describe original frozen runs, not the sanitized candidate. Do not use an old experiment manifest as a checksum list for these derivatives. The release provenance and current inventory bridge that distinction.

## Verification and limits

- [Static checks](../manifests/public_release_checks.json) cover all candidate files without a size cutoff; Python is parsed, not imported or executed.
- All 15 notebooks and their 767 code cells are checked structurally and parsed with IPython syntax transformation. No cells are executed. The optional nbformat validator is unavailable; no packages were installed.
- The sole inherited syntax exception is `RAG/results/rag_e8_rf_tuning_v1/scripts/report_e8.py`; the corrected renderer is retained separately.
- Imports and dynamic-import locations are inventoried. Source hashes and positions are unchanged, so this phase introduces no source-path relocation. External frozen artifacts and environment imports are not claimed to resolve on a fresh machine.
- Local Markdown targets and heading anchors are checked. External URLs are references; universal HTTP availability is not asserted.
- Six JSONL files are empty historical records. CSVs are aggregate summaries except the explicitly public ID/fold projection. No dataset text, row-level predictions, model weights, environments or binary caches were added.
- Privacy matches in the audit utility itself are literal scanner patterns, not actual personal paths. Pattern checks do not guarantee detection of every possible secret.
- Credential-related filenames in examples are generic sanitized placeholders, not actual key filenames. Windows system-tool paths and path-injection test fixtures are portability/test data, not personal home directories. The three dataset download identifiers in `OFFICIAL_RELEASE_CHECK.json` were matched to the organizers' public 2024 source page; no dataset download was performed.
- Root README results are checked against the saved metric JSON files and RESULTS. No metrics were recomputed by running models.

## Rights and publication gates

The [per-file license inventory](../manifests/license_inventory.public.json) distinguishes MIT-noticed FactCG/BERTScore from project-origin material with ownership approval pending. The organizer and parser material previously withheld for uncertain rights remains absent. The two diagnostic source dumps are no longer distributed; no standalone Transformers source was identified.

**Publication remains blocked** pending confirmation of rights and scope for the project-origin material, and the exact copyright holder and year. MIT is approved in principle for code the owner is entitled to license; this is not blanket confirmation for all files. Dataset/model terms remain separate; their full artifacts are not distributed. Approve the exact public Git name and GitHub-provided noreply email before future commits. No identity was selected automatically.

After those decisions, perform a final review of the release files, initialize clean history only with approval, and obtain separate authorization to create/publish the public repository. Preserve the existing private repository and archival tags intact.

PHASE 4C verdict: **PUBLIC RELEASE BLOCKED** while the required copyright and rights-scope details remain unresolved. This does not indicate missing thesis implementation or a failed file copy.
