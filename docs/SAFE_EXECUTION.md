# Safe execution and reproducibility

This repository contains research code, protocols and historical results. It is not a single application that can safely be run from a clean clone. Full reproduction from the public files alone has not been verified.

## Before running research code

Do not run historical notebooks, experiment scripts or release tools directly inside a Git checkout. Some scripts create directories or logs during import. Others write to fixed locations beside their source, recreate old CSV filenames, update provenance records or launch external services. A command called `preflight`, `verify` or `--help` is not automatically free of side effects.

Keep original datasets, predictions, reports, model weights and frozen artifacts unchanged. Verify their recorded hashes and use read-only inputs. Never regenerate authoritative folds, replace an expected hash or remove a completion marker to make a run pass. Public-safe manifests may omit fields required by the original experiment; they are not substitutes for its original inputs.

## Use a separate run directory

A future controlled test needs a fresh scratch/run directory outside every Git repository, backup and historical archive. Keep its working files, outputs, caches, logs and temporary files separate from its read-only inputs. Do not reuse an existing output directory or overwrite an earlier result.

Before starting a process, review the selected entry point, its imports and all input and output paths. Resolve relative paths, absolute paths, `__file__` paths, environment overrides and input-existence fallbacks. Check that links or junctions cannot redirect a write into protected files. Include model caches, plotting caches, temporary files and import-time writes in this review.

Changing the working directory or setting `TEMP` and cache variables is not sufficient when code uses fixed paths or overrides those variables itself. The canonical CV output override does not cover every possible write; E6-v4 also sets temporary paths inside its execution tree. If every write cannot be confined to the approved run directory, stop. A separately reviewed execution layout is required; do not disable integrity checks or modify frozen source to bypass this problem.

## Control side effects

Downloads, API calls, cloud execution and training require separate explicit approval. Use offline mode and deny network access for tests that do not need it. Offline environment variables are useful settings, not a complete network or filesystem sandbox. Do not provide provider credentials to an offline test.

Review even CPU-only verification tools: the E11 remote checkpoint verifiers launch Modal functions. Model loading, notebook setup cells and dependency initialization can also access the network or write files. Do not run a notebook with “Run All” as a safety check.

A future test must have an approved scope, environment, input hashes, allowed write paths, time limits and stop conditions. Stop on an unexpected write, network request, hash mismatch, missing input, conflicting output or uncontrolled retry. Preserve incomplete outputs and diagnostics without automatically retrying or cleaning them up.

## Preserve the scientific context

Keep these evaluations separate:

- Historical experiments on 499 development examples.
- Canonical experiments using 561 development examples and out-of-fold predictions.
- Older synthetic ablations evaluated with labeled test data.
- Retrospective official-test reconstruction, with its documented limitations.

A rerun can recreate an old filename without reproducing the same experiment. Store new outputs separately and record the exact source, inputs, environment, folds and protocol. Do not promote them into historical records automatically.

## What can be reproduced here?

The public repository supports inspection of implementations, protocols, selected aggregate results and provenance documentation. It does not include all original datasets, model weights, row-level predictions, feature matrices, retrieval caches or generated artifacts. Some historical checks also require original source bytes, package versions or execution layouts that the public files do not satisfy.

A future synthetic helper test or source-only check may be feasible after its imports and isolation have been reviewed. Passing such a test would not establish full E1-E11 reproducibility. Static inspection and migration hash checks are not new executions or independent confirmations of the reported metrics.

Compare complete file inventories before and after any approved test, including ignored and untracked files, together with Git refs, index state and protected input hashes. A clean `git status` and `.gitignore` rules alone cannot prove that no protected or ignored file was changed.

For the code locations, see the [research index](../research/README.md). The detailed static review is in the [historical execution matrix](https://github.com/spyroskontakis/shroom-hallucination-detection/blob/11822d92070cd29360445cb4dacd8d110c655248/project_records/migrations/execution_safety_20261027/EXECUTION_MATRIX.md) and [output-path risk review](../project_records/migrations/execution_safety_20261027/OUTPUT_PATH_RISKS.md). These documents describe prerequisites; they do not authorize execution.

## Source modes after physical relocation

Select an authenticated historical snapshot or a supported current binding explicitly; see [source modes](REPRODUCIBILITY.md). Raw relocated frozen files retain their old paths and writers internally. Do not run them directly in the checkout. The compatibility layer covers selected libraries and E6 bindings only, not a complete runner. Public snapshots do not supply missing original data, weights, markers or timestamps.
