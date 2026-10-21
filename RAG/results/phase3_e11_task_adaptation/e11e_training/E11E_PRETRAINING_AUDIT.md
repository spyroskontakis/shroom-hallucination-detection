# E11-E pretraining audit: PASS

Exact E11-C prepared bytes replayed from the homogeneous 11,887 gpt-5.6-sol labels. Excluded 109 uncertain, four Azure judgments, and the same 82 duplicate/conflicting rows. Validation exclusions 18/14/10/18/15; synthetic sizes 11,787/11,791/11,795/11,787/11,790. Human folds unchanged.

E11-D cosine loss implementation copied byte for byte: lambda 0.1, margin zero, no temperature, final-layer sequence mean pooling with textual prefixes retained and special/padding tokens excluded. Applied in both stages.

Exact C model, tokenizer, 512-token truncation, seed 42, optimizer, class weights, batch/accumulation, BF16, scheduler, one synthetic epoch and five human epochs. Ten fits only. All four baselines recomputed using the authoritative evaluator.

Pretraining tests passed. No teacher calls or official-test access. Full provenance, exact loss and settings are in E11E_TRAINING_PROTOCOL.json and the JSON audit.
