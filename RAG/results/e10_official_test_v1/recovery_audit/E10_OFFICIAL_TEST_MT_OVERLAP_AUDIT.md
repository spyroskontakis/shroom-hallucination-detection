# MT overlap audit

Proposed strict pool: **547** (479 development + 68 trial; DM 211, MT 202, PG 134). No model was fit.

All 14 removed rows are MT development examples. Indices are zero-based. Every matched hypothesis differs, and no exact `(task,src,tgt,hyp)` example is shared anywhere in the original 561-row pool. Equality uses the existing audit NFC/whitespace normalization, preserving case. Labels are not used to select exclusions.

| Canonical ID | Canonical index | Original source index | Source | Test ID | Different hypothesis | Exact example shared |
|---|---:|---:|---|---|---|---|
| HDEV_0318_b7b68e48521d | 317 | 317 | development_model_agnostic | 175 | Yes | No |
| HDEV_0333_697ef5a72a77 | 332 | 332 | development_model_agnostic | 1370 | Yes | No |
| HDEV_0363_34fdff732038 | 362 | 363 | development_model_agnostic | 505 | Yes | No |
| HDEV_0366_20aed6bd704a | 365 | 366 | development_model_agnostic | 383 | Yes | No |
| HDEV_0369_214ad3377267 | 368 | 369 | development_model_agnostic | 1364 | Yes | No |
| HDEV_0378_706d26208e3b | 377 | 379 | development_model_agnostic | 2565 | Yes | No |
| HDEV_0384_2097b26cb26b | 383 | 385 | development_model_agnostic | 2878 | Yes | No |
| HDEV_0396_029188d4e168 | 395 | 397 | development_model_agnostic | 92 | Yes | No |
| HDEV_0413_ca10023a883f | 412 | 414 | development_model_agnostic | 513 | Yes | No |
| HDEV_0416_cee0dc4d7a20 | 415 | 417 | development_model_agnostic | 1864 | Yes | No |
| HDEV_0441_ed51c218d54f | 440 | 443 | development_model_agnostic | 1171 | Yes | No |
| HDEV_0463_f689e69a1247 | 462 | 467 | development_model_agnostic | 836 | Yes | No |
| HDEV_0468_92dac8e11b38 | 467 | 472 | development_model_agnostic | 1454 | Yes | No |
| HDEV_0473_58171c0672e3 | 472 | 477 | development_model_agnostic | 840 | Yes | No |

The retained rows are copied unchanged from the canonical manifest, including their existing training labels. The proposed manifest does not replace the canonical 561-row development artifacts. Removing these 14 rows is a stricter training-population choice, not a new E10 CV result.
