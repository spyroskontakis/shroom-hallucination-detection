# Single reconstructed retrospective E10 evaluation

Evaluation wording: reconstructed retrospective evaluation on the official labeled SHROOM test set.

## Frozen method and population

Use all 561 canonical labeled examples (493 validation + 68 trial) and the existing exact 561 x 37 E10 matrix. Retain the 14 MT source/target overlaps, whose hypotheses differ. No exact test example overlaps the canonical pool. Do not use the proposed 547-row pool for any fit, selection or comparison.

Use the exact E6-v3 36 columns plus FactCG, in their original order. One RandomForestRegressor fit, 500 trees, seed 42, all parameters checked against the existing E10 manifest. Target p_hallucination, predictions clipped to [0,1], threshold 0.5, original evaluator rounding to 12 decimals for Spearman.

The sole intended methodological deviation is acquisition in 2026 of missing Wiktionary resources using the original endpoint, revision acquisition, immutable-revision parse, normalization, English/POS sense extraction, deduplication and ranking functions. Existing frozen dictionary records remain unchanged. Technical retrieval failures and confirmed no-sense outcomes remain separately reported; only the original missing-definition zero behavior applies.

## Execution boundary

The lexical reconstruction is completed and its coverage reported before neural extraction. CPU backends retain the local original environment, model hashes, float32, four threads, batch size two for NLI1/NLI2/HHEM and original MPNet batching. Base14 MPNet uses the checkpoint default of 384 tokens; RAG MPNet uses the original explicit 256-token limit. FactCG alone uses Modal A100-80GB with its original pinned Linux/CUDA environment, float32, batch size one, no TF32/autocast/quantization, and the original chunking/instruction/scoring adapter.

Only id/task/src/tgt/hyp enter the feature pipeline. The official source is projected by the existing lexical gold-skipping parser. A complete 1,500 x 37 matrix must pass order, identity, finite/range and missing-definition checks. One RF fit then freezes the full prediction JSON and SHA256. Only the separate score action may load official gold after verifying that file and all 1,500 IDs. Scoring occurs once; there is no post-score tuning or alternate system.

## Provenance and interpretation

No verified exact full E10 test-feature cache was found in the prior recovery audit. Historical test base-feature CSVs are not substitutes for verified pinned complete E10 provenance. Reuse the frozen training matrix and identity-checked extraction checkpoints. Parser replay reproduces the original frozen lexical snapshot byte-for-byte.

Prior test gold inspection, test-derived exploratory CV/sweeps, and test-input overlap filtering are documented in the recovery audit. This run is neither independent holdout validation nor competition participation. Published comparisons are descriptive, use the organizer paper Table 1(a), and confer no official rank. Original experiment and thesis artifacts remain unchanged; all new artifacts are confined to reconstructed_v1. No commits or pushes.
