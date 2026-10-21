# Reproducibility

1. Obtain the SHROOM datasets from their authorized source and verify them against the recorded manifests.
2. Recreate the environment required by the selected experiment. Do not assume the copied historical Conda environment is portable.
3. Keep the repository paths unchanged because several scripts use relative paths, dynamic imports or `Path(__file__)` parent traversal.
4. Supply model caches or weights outside the repository and verify the recorded model revision and SHA-256 values.
5. Obtain the full `codex/canonical_fold_assignments.csv` separately, where permitted, for comparisons that claim the fixed 561-example canonical folds. The [public ID/fold projection](../manifests/canonical_fold_assignments.public.csv) documents assignments but does not replace the full input schema. See [data access](DATA_ACCESS.md).
6. Read the experiment protocol and amendments before running its scripts. Some directories preserve initial blocked attempts as well as the later completed run.

Full frozen replay additionally requires row-level features, OOF vectors, retrieval snapshots, annotations and weights that are intentionally absent from publication staging. Their hashes and availability are documented in the public provenance and external-artifact manifests.