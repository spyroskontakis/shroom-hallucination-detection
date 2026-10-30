# E7 v1 — Selective / Agentic RAG without LLM

**COMPLETED — DEVELOPMENT-ONLY.** One frozen five-fold OOF evaluation; no post-score redesign or rerun.

## Actual result

| Group | Correct / N | Accuracy | Spearman |
|---|---:|---:|---:|
| E3 | 445/561 | 0.7932263815 | 0.7390395613 |
| E5 | 446/561 | 0.7950089127 | 0.7421719692 |
| E6 | 453/561 | 0.8074866310 | 0.7444205394 |
| E7 | 448/561 | 0.7985739750 | 0.7402641043 |

The frozen selective policy did not improve E6 on this development pool.

## Frozen architecture and training

A deterministic controller loads cached E6 ranking metadata. Each sample follows START → RETRIEVE → ASSESS_EVIDENCE → one routing action → PREDICT → END. There is exactly one decision. RETRIEVE performs no external request.

For each outer fold, tau is numpy.quantile(top1_cosine of evidence-bearing outer-training rows, 0.5, method="linear"). Evidence available and score >= tau selects USE_EXTERNAL_EVIDENCE (fresh E6 path); all other rows select FALLBACK_TO_BASE (fresh E3 path). Inference receives only evidence_available and top1_cosine. No labels, hypothesis, correctness or predictions determine routing. No inner search, tuning, retry or supervised router target exists.

The accepted Module 4 run_cv code ran unchanged, with an estimator wrapper checking and logging train/validation arrays and IDs. E3 uses 14 predictors; E6 uses the frozen 25. Each RF uses 500 trees, random_state=42, n_jobs=-1 and all frozen defaults, target p_hallucination, clipping [0,1], binary threshold >=0.5. Exactly ten RF fits (5 E3 + 5 E6); zero MPNet/DeBERTa extraction or pretrained-model training. Both paths were computed for this audit; no inference-cost saving is claimed.

## Training-fold medians and fold results

| Fold | Train evidence N | Median tau | E6 route | E3 fallback | Correct / N | Accuracy | Spearman |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 156 | 0.5419563233966094 | 22 | 91 | 93/113 | 0.8230088496 | 0.7661590635 |
| 2 | 156 | 0.5545786341668592 | 14 | 98 | 82/112 | 0.7321428571 | 0.7283152630 |
| 3 | 154 | 0.5428183280799617 | 22 | 90 | 90/112 | 0.8035714286 | 0.7480004755 |
| 4 | 153 | 0.5528261876243299 | 16 | 96 | 87/112 | 0.7767857143 | 0.7242423950 |
| 5 | 153 | 0.5427257538441697 | 23 | 89 | 96/112 | 0.8571428571 | 0.7305244600 |

## Route distribution

| Group | E6 route | E3 fallback |
|---|---:|---:|
| All rows | 97 | 464 |
| DM | 97 | 114 |
| MT | 0 | 216 |
| PG | 0 | 134 |
| With evidence | 97 | 96 |
| Without evidence | 0 | 368 |

## Task, evidence and route metrics

| Group | Correct / N | Accuracy | Spearman |
|---|---:|---:|---:|
| DM | 158/211 | 0.7488151659 | 0.6437204817 |
| MT | 185/216 | 0.8564814815 | 0.7960447809 |
| PG | 105/134 | 0.7835820896 | 0.6961810929 |
| Group | Correct / N | Accuracy | Spearman |
|---|---:|---:|---:|
| With evidence | 146/193 | 0.7564766839 | 0.6539022173 |
| Without evidence | 302/368 | 0.8206521739 | 0.7662242801 |
| Group | Correct / N | Accuracy | Spearman |
|---|---:|---:|---:|
| FALLBACK_TO_BASE | 371/464 | 0.7995689655 | 0.7470992222 |
| USE_EXTERNAL_EVIDENCE | 77/97 | 0.7938144330 | 0.6959730616 |

Spearman uses target p_hallucination and predictions rounded to 12 decimals. It is undefined for fewer than two observations or a constant target/rounded prediction. Subgroup metrics are descriptive.

## Paired comparisons

| Baseline | Corrections | Regressions | Net correct | Δ accuracy (pp) | Exact McNemar p | Bootstrap 95% CI (pp) |
|---|---:|---:|---:|---:|---:|---|
| E6 | 2 | 7 | -5 | -0.891266 | 0.1796875000 | [-1.960784, +0.178253] |
| E3 | 3 | 0 | +3 | +0.534759 | 0.2500000000 | [+0.000000, +1.247772] |

E6 is the primary baseline; E3 is secondary. Exact two-sided McNemar uses binomtest(b,b+c,0.5), or p=1 for no discordance. Paired bootstrap uses 10,000 resamples of 561 paired correctness differences, default_rng(42) freshly initialized per baseline, percentile 2.5/97.5. No multiple-comparison or research-selection correction is claimed.

E7 vs E6 corrections from fallback: 2; regressions from fallback: 7. E6-route rows retain the reproduced E6 predictions. IDs of every correction/regression are in e7_metrics.json; paired_row_diagnostics.csv covers all 561 rows.

## Post-execution numerical ceiling

Actual saved OOF files show no-evidence E3=302/368 versus E6=304/368, hence mandatory fallback changes the correct count by -2. Globally there are 2 E3-correct/E6-wrong rows. These establish the loose bound 453 -2 + 2 = 453/561.

The tighter bound is 452/561 (0.8057040998): 1 of those potential corrections already occurs in the mandatory no-evidence fallback and is included in its net change. Only 1 additional E3-only correct row is in the evidence group. Equivalently, sum E3 correctness on no-evidence rows and max(E3 correctness,E6 correctness) on evidence rows. This oracle ceiling is an after-the-fact descriptive limit on these fixed OOF predictions, not a deployable router, not a tuned experiment and not a generalization bound. It was never used to change thresholds or actions.

## Technical history and execution chronology

The initial preflight stopped with three blocked writes and no fit/score. A separately authorized import-only diagnostic traced them to Windows NUL stdio for platform.py shell probes (ver / command /c ver / cmd /c ver). The process-local adapter suppresses that optional probe and uses the native Windows fallback; no filesystem allowlist was widened. ACCESS_REPAIR_REPORT.md and historical failure/security records remain. The original failure report is preserved at history/INITIAL_PREFLIGHT_FAILURE.md.

Protocol freeze: 2026-09-09T15:53:49.8464243Z. Routes frozen: 2026-09-09T18:14:21.720402+00:00. Evaluation/source freeze: 2026-09-09T18:14:21.777792+00:00. First-suite marker: 2026-09-09T18:14:50.534408+00:00. Completed: 2026-09-09T18:15:07.307157+00:00.

Full E7 contracts: 28 PASS. The later pre-evaluation preflight passed with no operational guard violation. Labels and saved predictions were projected only after the routing freeze; prior integrity reads hashed frozen bytes without using their contents for decisions.

## Reproduction and final integrity

Protocol SHA-256 unchanged: `0491505c0f98a2a4d2a0896370adbbc3674c6fdf873b96a8a31833e587923002`. All 481 protected E3/E5/E6/Module 4 files are unchanged. Evaluation source/config hashes, exact ID/fold alignment, all trajectories, 561 valid OOF values and ten completed fit records passed final audit. Network attempts during contracts/preparation/evaluation/reporting: zero; no official-test dataset access. The guard is process-local defense-in-depth, not OS isolation.

E3: fresh vs frozen predictions match per canonical ID within 1e-12; actual max absolute difference 2.2204460492503131e-16. Binary predictions and ranks after 12-decimal rounding are identical; metrics reproduce. This goes beyond aggregate-count agreement.

E6: fresh vs frozen predictions match per canonical ID within 1e-12; actual max absolute difference 3.3306690738754696e-16. Binary predictions and ranks after 12-decimal rounding are identical; metrics reproduce. This goes beyond aggregate-count agreement.

## Interpretation and limitations

The experiment adds explicit evidence assessment and a conditional action to the E6 retrieval-plus-semantic-verification pipeline. A training-only median is interpretable, but it is a relative cosine cutoff, not a calibrated estimate that evidence will improve prediction. The same development pool informed earlier experiments; fold-safe threshold fitting does not erase adaptive research history. Bootstrap intervals condition on fixed OOF values and omit retraining uncertainty. Non-significance is not evidence of equivalence.

Evidence is DM-only. E6 retains reference-assisted E5 features and historical provenance/label-exposure caveats. Reconstructed aggregate consistency does not establish the historical complete ranking. E6 can improve no-evidence predictions through a different RF feature space; mandatory E3 fallback discards those improvements. No independent official-test generalization claim is made.

The repository clone is not self-contained: authorized local canonical inputs, fold/feature/OOF files and ranking are required. E7 did not load MPNet or DeBERTa; it reused verified frozen matrices. No E8, synthetic-data change, thesis/PowerPoint edit, commit, push or tag occurred.

## Artifacts

scripts/: controller, guarded preflight, freeze preparation, accepted-evaluator audit wrapper, one-shot evaluation and read-only reporting. tests/: router, data-alignment, runtime and access contracts. routing/: label-free observations and frozen actions. config/: hashes, thresholds, contracts, security logs and final integrity/completion manifests. evaluation/: fresh E3/E6 predictions, E7 OOF predictions, 561 agent trajectories, paired diagnostics, metrics, ceiling analysis and ten fit-start/fit-completion pairs. Existing history/repair logs remain; earlier manifests describe their historical snapshots.

Branch: agentic-rag-e7, originating at frozen rag-e6-v1 commit 0a1ef3e792867796c412070087095274b0206849. STOP after this single E7 execution.
