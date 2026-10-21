# E6-v4 protocol — blocked compatibility gate

Status: **BLOCKED_BEFORE_BULK_SCORING**. This document preserves the predetermined specification and the observed technical stop. It is recorded after the artificial compatibility attempt, before any SHROOM scoring or RF fit. It does not certify a passed smoke test or a frozen feature matrix. `execution_allowed=false`.

Use the 561 frozen canonical IDs and five locked folds (113,112,112,112,112). Preserve all 36 E6-v3 features numerically and in their exact saved order, then append the seven ordered names in `config/feature_schema.json` (43 total). The source matrix is verified; no combined matrix has been produced.

Reference is tgt for DM/MT and src for PG; candidate is hyp. Use exact frozen strings. The projected extraction input contains only pair_id, canonical_id, group, premise, hypothesis. No labels, OOF predictions or definitions enter the new feature extraction. Labels are read separately for saved baseline verification only.

Official BERTScore distribution 0.3.13, unmodified wheel, checkpoint/tokenizer `microsoft/deberta-large-mnli@7296194b9009373def4f7c5dad292651e4b5cf4e`. Official mapping supplies num_layers=18; idf=False, rescale_with_baseline=False, all_layers=False, use_fast_tokenizer=False. CPU float32, batch_size=2, four intra/inter-op threads. No selection using SHROOM results. Precision measures candidate coverage by reference; recall measures reference coverage by candidate.

Required artificial smoke cases: identical sentence, omission, addition, number change, negation added/removed. Official matching-function direction assertion passed before the neural smoke call; neural smoke tokenization failed with OverflowError. The six neural cases have no scores. Separate deterministic structural contracts pass. No fallback tokenizer limit, package patch, checkpoint substitution or dependency downgrade is authorized by this protocol.

Frozen intended structural rules, used only on artificial inputs:

```json
{
  "normalization": "Unicode NFC, casefold, U+2018/U+2019 apostrophes -> ASCII apostrophe; structural features only",
  "token_regex": "[^\\W_]+(?:'[^\\W_]+)*",
  "regex_flags": "re.UNICODE",
  "number_regex": "(?<![\\w.,])(?P<number>[+-]?\\d+(?:[.,]\\d+)*)(?:[ \\t]*(?P<percent>%))?(?!\\w)",
  "number_normalization": "Preserve sign, digit spelling, leading/trailing zeros and percent. A single comma separator becomes dot only with 1 or 2 trailing decimal digits. Ambiguous 3+ comma digits or multiple separators are retained verbatim. Whitespace before percent is syntax, excluded from the extracted value.",
  "negation_lexicon": [
    "no",
    "not",
    "never",
    "neither",
    "nor",
    "nobody",
    "nothing",
    "nowhere",
    "without",
    "cannot",
    "can't",
    "won't",
    "isn't",
    "aren't",
    "wasn't",
    "weren't",
    "don't",
    "doesn't",
    "didn't",
    "hasn't",
    "haven't",
    "hadn't",
    "shouldn't",
    "wouldn't",
    "couldn't",
    "mustn't"
  ],
  "negation_suffix": "n't",
  "not_supported": "Spelled-out numbers, fractions, scientific notation and thousands-format interpretation are not resolved; sets ignore repetition and order. Negation flags presence, not scope. No lemmatization or parser.",
  "empty_ratio": "both zero -> 1.0; exactly one zero -> 0.0"
}
```

Length ratio is min(counts)/max(counts), both empty=1, one empty=0. Number-presence mismatch is XOR of nonempty number sets; number-set mismatch is set inequality (both empty=0). Negation mismatch is XOR of literal marker presence. These are surface indicators, not semantic judgments. The numeric rule deliberately retains ambiguous comma formats; it is not a general numeric parser. Lexicon is exactly the user-specified list plus suffix, without additions from labels or error analysis.

Full fixed RandomForestRegressor parameters, copied from E6-v3:

```json
{
  "bootstrap": true,
  "ccp_alpha": 0.0,
  "criterion": "squared_error",
  "max_depth": null,
  "max_features": 1.0,
  "max_leaf_nodes": null,
  "max_samples": null,
  "min_impurity_decrease": 0.0,
  "min_samples_leaf": 1,
  "min_samples_split": 2,
  "min_weight_fraction_leaf": 0.0,
  "monotonic_cst": null,
  "n_estimators": 500,
  "n_jobs": -1,
  "oob_score": false,
  "random_state": 42,
  "verbose": 0,
  "warm_start": false
}
```

Only after a passed compatibility gate, full extraction, per-ID finiteness/truncation checks, exact 36-column equality and a frozen 43-column matrix would five outer-fold fits be permitted. Target p_hallucination; clip [0,1]; binary prediction >=0.5. No baseline fits, tuning, feature selection, router, task-specific models or post-score changes.

Intended evaluation: overall/fold/task/evidence accuracy and Spearman (predictions rounded to 12 decimals for Spearman), corrections/new errors against saved E6-v3, exact two-sided McNemar, paired row bootstrap with 10,000 resamples using numpy.random.default_rng(42), percentile quantiles 0.025/0.975. Definition availability is descriptive and all definitions concern DM. Intervention was selected after error analysis: adaptive exploratory development-only, descriptive statistics, no independent confirmatory test.

**Stopping rule applied:** the user's section 3 requires stopping if the official library is incompatible. See `provenance/compatibility.json` and `E6_V4_RESULTS.md`. No feature matrix or evaluation is frozen. The documentation manifest seals this blocked state only.

All new files remain inside rag_e6_v4. Prior artifacts, error analysis and untracked changes are preserved. No official-test, synthetic changes, retrieval, remote inference, commit/push/tag or other experiment.
