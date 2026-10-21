# E11-E results: PASS

Single fixed ablation. Exact E11-C two-stage data/settings plus the unchanged E11-D contrastive objective in both stages. No tuning or additional configuration.

| Experiment | Human | Synthetic | Contrastive | Correct/561 | Accuracy | Spearman |
|---|---|---|---|---:|---:|---:|
| E11-A | Yes | No | No | 460/561 | 0.8199643493761141 | 0.7172565081322899 |
| E11-C | Yes | Yes | No | 466/561 | 0.8306595365418895 | 0.7270182116026076 |
| E11-D | Yes | No | Yes | 459/561 | 0.8181818181818182 | 0.7006748393613571 |
| E11-E | Yes | Yes | Yes | 466/561 | 0.8306595365418895 | 0.7150820586520120 |
| E10 | feature-based reference | - | - | 475/561 | 0.8467023172905526 | 0.7828092941190203 |

| E11-E minus | Correct | Accuracy | Spearman |
|---|---:|---:|---:|
| E11-A | +6 | +0.0106951871657754 | -0.0021744494802779 |
| E11-C | +0 | +0.0000000000000000 | -0.0119361529505956 |
| E11-D | +7 | +0.0124777183600713 | +0.0144072192906549 |
| E10 | -9 | -0.0160427807486631 | -0.0677272354670083 |

| Task | Correct/total | Accuracy | Spearman |
|---|---:|---:|---:|
| DM | 170/211 | 0.805687203791 | 0.706896395207 |
| MT | 190/216 | 0.879629629630 | 0.741728178510 |
| PG | 106/134 | 0.791044776119 | 0.626004585651 |

Confusion matrix, gold rows/predicted columns ordered 0/1: `[[264, 43], [52, 202]]`.

| Fold | Synthetic | Human | Correct/heldout | Accuracy | Spearman | Stage 1 s | Stage 2 s |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 11787 | 448 | 91/113 | 0.805309734513 | 0.752779359159 | 241.432 | 51.053 |
| 2 | 11791 | 449 | 95/112 | 0.848214285714 | 0.743505340541 | 424.455 | 91.510 |
| 3 | 11795 | 449 | 95/112 | 0.848214285714 | 0.734293718352 | 239.600 | 52.090 |
| 4 | 11787 | 449 | 95/112 | 0.848214285714 | 0.748625131122 | 246.752 | 51.713 |
| 5 | 11790 | 449 | 90/112 | 0.803571428571 | 0.681358831274 | 495.069 | 104.652 |

Probability range: [0.0010322310263291001, 0.9992563128471375]; predicted class counts: {'0': 316, '1': 245}. 561 unique complete IDs; no NaN/Inf, missing IDs, duplicates or fold class collapse.

## Descriptive interpretation

- E11-C minus E11-A: accuracy improved (+0.010695187166, +6 correct); Spearman improved (+0.009761703470).
- E11-D minus E11-A: accuracy decreased (-0.001782531194, -1 correct); Spearman decreased (-0.016581668771).
- E11-E minus E11-C: accuracy unchanged (+0.000000000000, +0 correct); Spearman decreased (-0.011936152951).
- E11-E minus E11-D: accuracy improved (+0.012477718360, +7 correct); Spearman improved (+0.014407219291).

Highest E11 accuracy: E11-C, E11-E. Highest E11 Spearman: E11-C.
E11 variants exceeding E10 accuracy: []; Spearman: [].
These are descriptive development comparisons. No statistical significance test performed.

Loss in BOTH stages: weighted CE + 0.1 × mean[(1−y)(1−cos(a,b)) + y·max(0,cos(a,b))]. y=1 denotes hallucination; margin 0, no temperature. Byte-identical E11-D implementation: final-layer mean pooling by fast-tokenizer sequence membership, special/padding tokens excluded, textual prefixes retained, cosine L2 normalization with eps=1e-8. Both representations share the original cross-encoder context. No projection head or additional forward pass.

Exactly ten fits (five Stage 1, five Stage 2), no reruns. Seed 42. Summed recorded fit runtime 1998.325 s; Stage 1 1647.308 s; Stage 2 351.017 s. Per-stage time from training loop through checkpoint saving and hashing; excludes model setup and heldout inference. Concurrent sums are not wall time or billing duration.
GPUs: NVIDIA A100-SXM4-80GB. Runtime: `{"python": "3.11.12", "torch": "2.2.1+cu121", "cuda": "12.1", "packages": {"transformers": "4.38.1", "tokenizers": "0.15.2", "numpy": "1.26.4", "safetensors": "0.4.5"}}`.

Final tests: 111 passed, zero skips. All ten persisted checkpoint hashes and five predictions independently verified. Stage-2 initial hashes match their own fold's Stage-1 checkpoints. 550 protected prior files unchanged.
No teacher calls, official-test access, threshold/hyperparameter tuning, commit, push or E11-F.
