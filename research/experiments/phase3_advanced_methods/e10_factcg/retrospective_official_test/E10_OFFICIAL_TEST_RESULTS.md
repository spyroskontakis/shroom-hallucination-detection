# E10 official-test evaluation — preflight outcome

**FINAL STATUS: FAIL (preflight blocked; no official-test score generated).**

Training protocol: B, exact frozen thesis pool, recommended before gold inspection; execution blocked.

Training examples: 561 planned (493 official validation + 68 trial); 0 final RF fits.

Official test examples: 1,500 verified (DM 563 / MT 562 / PG 375).

Correct: not computed.

Accuracy: not computed.

Spearman: not computed.

DM: n=563; predictions/correct/Accuracy/Spearman not computed.

MT: n=562; predictions/correct/Accuracy/Spearman not computed.

PG: n=375; predictions/correct/Accuracy/Spearman not computed.

Prediction SHA256: not available; no prediction file exists.

Any failures:

1. Frozen lexical evidence has no acquisition record for 557 distinct test terms, affecting 561 of 563 DM examples. This must not be silently treated as verified absence of evidence or replaced with a new lexical source.
2. Fourteen MT source/reference pairs overlap between the canonical training pool and test, with different hypotheses. No exact test example is in the canonical pool, but the requested no-overlap condition is not unambiguously met. The pool and official test were not altered.

Any deviations from frozen E10: none executed. No system was fitted, no feature inference or Modal job was launched, and no gold scoring occurred. A pipeline with additional evidence or altered training membership was not silently substituted.

Internal common-set result: **475/561, Accuracy 0.8467023172905526, Spearman 0.7828092941190203**, reproduced exactly from frozen OOF predictions with the existing metric implementation, zero new model calls and zero fits.

Official-test retrospective result: **not available**. There is no basis for a leaderboard comparison or rank.

The audit was stopped under the instruction to proceed only if all preflight checks pass. Continuing requires a documented decision on source-pair overlap and a frozen acquisition/provenance plan for missing test-term evidence. Do not select either policy using test scores.

Historical caveat: earlier exploratory artifacts already used official test data. A future run may be called “retrospective evaluation on the official labeled SHROOM test set”, but not an official submission or an untouched independent evaluation.

See E10_OFFICIAL_TEST_DATA_AUDIT.md for the seven source-provenance answers, blinding mechanism, official-download verification, phase status and source paths. Five synthetic projection tests passed. All new outputs are isolated in this directory. No commit or push.
