# E6-v2 publication audit — 2026-09-12

PASS. Publication of the already completed experiment; no new fits, inference, retrieval, hyperparameter selection or experiment evaluation. The read-only saved-artifact audit was completed on 2026-09-11 and its hashes were checked again before publication preparation.

Verified result: **473/561; Accuracy 0.8431372549019608; Spearman 0.7775058304756869**. Features: 34. Historical RF fits: 5; historical OOF suites: 1; additional baseline verification fits: 0. Publication adds 0 fits and 0 experiment suites.

## Scope and reproducibility

The original protocol, result report, source and other approved frozen files are published byte-for-byte. Statements in those reports that no commit/tag/push occurred describe the original experiment's completion, before this separately authorized publication. No historical baseline or result is rewritten.

22 original files plus 8 publication-only additions are approved: **30 published files**. Local-only originals: **697** (666 class B, 31 class C). The complete original-file classification, byte sizes and SHA-256 values are in publication/artifact_inventory.json. Publication additions are explicitly allowlisted in .gitignore. .gitattributes preserves original bytes, including CRLF, so published frozen-file hashes remain meaningful.

Class B contains model weights/caches/dependencies/temp files. Class C contains row-level CSV/JSONL, raw text, per-ID error lists and local provenance/diagnostics. They are neither staged nor force-added. The raw matrices, OOF predictions and split IDs remain available locally. A fresh clone is not self-contained: exact execution/auditing requires the authorized local data and dependencies referenced by the original manifests. Do not rerun completed experiments to obtain publication output.

publication/configuration.json is an explicitly labeled publication view of config/run_config.json; only runtime.executable is omitted. All RF parameters, feature names/order, versions and methodological settings are retained. The frozen original remains local and unchanged, and its SHA-256 is recorded. publication/aggregate_metrics.json preserves the original aggregate values and omits only corrected_ids and introduced_error_ids. Manifests refer to both published and withheld files; a filename/hash reference does not include that file's content.

## String, security and size review

The reviewed src/hyp occurrences are field names, direction descriptions or artificial test fixtures, not SHROOM source/candidate strings. No HDEV_/HTRIAL_ sample identifiers were found in the approved original files. Frozen files containing the personal Python executable path are withheld rather than edited. Source defaults such as external-artifacts/local-0fb664776e02/Windows are safe operating-system references. Upstream model URLs in provenance contain the pinned public revision and no credential.

No credential/private-key/provider-token pattern was found in the approved content. No model, environment, cache, .git helper, raw feature/prediction matrix or file over 50 MB is in the publication allowlist. This is a scoped content review, not a universal guarantee about arbitrary secret formats. Git-internal audit helpers and their local snapshots remain under .git and are not published.

## Integrity and access evidence

608 protected predecessor files match their frozen hashes; 718 completion-manifest files were verified. Canonical IDs, frozen labels and outer folds align across all 561 rows. Accuracy uses the unrounded prediction >=0.5; Spearman uses predictions rounded to 12 decimals and unrounded p_hallucination. Historical integrity records and guarded code/logs report no official-test access; this audit did not open official-test data. These historical process-local logs are not OS-level access proofs.

- Protocol SHA-256: `a9a8b44e45ae21d91368a90228a7bb422c5879d7222912b0e99878a7be2be81c`.
- Original configuration SHA-256: `a8f75273bfb0026da2b6eeacf3f50740ba4ee7a9ccbb9f60b3293fcd787d4d74`.

The frozen E6-v3 milestone remains 474/561, Accuracy 0.8449197860962567, Spearman 0.7816945786401444. E6-v2, E6-v3, E6-v4, E7 and E8 artifacts and the unrelated Augmentation Pipeline.txt are preserved. No new experiment is authorized by this publication note.

## Method and historical comparison

E6-v2 retains exactly 25 E6-v1 features and appends nine scores from the pinned second NLI evaluator MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli, revision b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7. Entailment/neutral/contradiction are computed for reference→hyp, hyp→reference and the saved selected definition→hyp; missing definitions receive three zeros. This is one 34-feature configuration with five RF fits.

Its historical comparison to E6-v1 (453/561) has 42 corrections, 22 introduced errors, net +20, exact two-sided McNemar p=0.01685819004428113; paired-bootstrap accuracy-difference 95% interval [0.0071301247771836, 0.06417112299465241]. All remain exploratory development-only findings on reused data.

Authorized pinned model download occurred before inference. The subsequent inference/evaluation logs contain zero network attempts. publication/smoke_summary.json removes the private executable path and artificial pair text, preserving the technical smoke results; the original smoke file is unchanged and local-only. The retained INITIAL_NAMING_DRAFT.md is harmless historical documentation, not an alternative final protocol.
