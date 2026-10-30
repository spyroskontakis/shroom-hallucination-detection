# Reproducibility and source modes

Full E1-E11 reproduction from the public repository alone is NOT VERIFIED. Full datasets, model assets, feature matrices, OOF vectors, retrieval evidence and other original runtime artifacts are not distributed. Migration hashes and synthetic tests do not confirm the reported numerical results.

## Historical mode

The [compatibility layer](../research/shared_tools/repository_compatibility.py) validates an explicit external read-only snapshot against an exact Git commit, tree and complete file inventory. H1 is the original public layout at 11822d92070cd29360445cb4dacd8d110c655248. P26 is the prior current context at 3dce69dbb6548f42695d971c900ead1ce85b9240. Neither is automatically the original H0 experiment environment.

Original-input checks remain enforceable. Public-safe H1 bytes differing from an H0 expected hash are rejected. Missing datasets, weights, markers and filesystem chronology cannot be reconstructed from Git source identity. Source inspection does not certify historical execution or original timestamps.

## Current mode

The [master catalog](../project_records/current_layout/repository_compatibility_v1.json) independently identifies all 790 original migration entries and their present paths. The compatibility layer composes the existing cross API for E6-v2/v3 and derives independently hashed local library views for E7, E8, FactCG and E11 scoring. AccessGuard class bodies, historical hashes, algorithms and results are preserved.

This is a limited integration scope, not an E1-E11 runner. Do not execute unadapted frozen sources directly at their new paths. Earlier repository_sources_v1/v2/v3 and cross contracts remain pinned to prior milestone contexts; their snapshot checks are not current-tree checks. E6-v4, adapted Module 1/2 and canonical CV retain their own contracts and limits.

A source-only validation command is:

    python research/shared_tools/repository_compatibility.py --expected-sha256 CATALOG_PIN --mode CURRENT

Run from the repository root after reviewing the script. Replace CATALOG_PIN with the independently reviewed master catalog SHA-256 and check it matches CATALOG_SHA256 in the script. This command launches no experiment. Historical validation additionally needs --mode HISTORICAL --snapshot H1 (or P26) and --snapshot-root pointing to the authenticated external read-only snapshot.

## Before any separately approved execution

- Obtain authorized original inputs and verify their hashes and schema. The [public fold projection](../manifests/canonical_fold_assignments.public.csv) documents IDs/folds; it does not replace the full canonical input.
- Select the exact source mode and experiment-specific environment. Check model revision, weights, required markers and source requirements before writes or model loading.
- Use read-only inputs and a new external run directory with reviewed cache/temporary roots. Do not reuse outputs or overwrite historical records.
- Review transitive readers and writers. Working-directory or cache-variable changes alone do not redirect absolute or __file__ paths.
- Keep downloads, API/cloud access, training and inference disabled without separate approval. Stop on missing authentic inputs, path mismatch, unisolated writes or unexpected access.

See [data access](DATA_ACCESS.md), [environments](ENVIRONMENTS.md) and [safe execution](SAFE_EXECUTION.md). These notes authorize no model run.
