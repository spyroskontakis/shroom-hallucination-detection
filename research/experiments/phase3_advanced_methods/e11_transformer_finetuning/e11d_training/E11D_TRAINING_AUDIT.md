# E11-D training audit: PASS

Compared with E11-A, contrastive learning reduces accuracy and reduces Spearman. Descriptive comparison only; no significance test performed.



| Experiment | Human | Synthetic | Contrastive | Correct/561 | Accuracy | Spearman |

|---|---|---|---|---:|---:|---:|

| E11-A | Yes | No | No | 460/561 | 0.8199643493761141 | 0.7172565081322899 |

| E11-C | Yes | Yes | No | 466/561 | 0.8306595365418895 | 0.7270182116026076 |

| E11-D | Yes | No | Yes | 459/561 | 0.8181818181818182 | 0.7006748393613571 |

| E10 | feature-based reference | - | - | 475/561 | 0.8467023172905526 | 0.7828092941190203 |



| D minus | Correct | Accuracy | Spearman |

|---|---:|---:|---:|

| E11-A | -1 | -0.0017825311942958 | -0.0165816687709328 |

| E11-C | -7 | -0.0124777183600713 | -0.0263433722412505 |

| E10 | -16 | -0.0285204991087343 | -0.0821344547576632 |



| Task | Correct/total | Accuracy | Spearman |

|---|---:|---:|---:|

| DM | 165/211 | 0.781990521327 | 0.665318948803 |

| MT | 190/216 | 0.879629629630 | 0.730689505997 |

| PG | 104/134 | 0.776119402985 | 0.600163904152 |



Confusion matrix (rows gold 0/1, columns predicted 0/1): `[[263, 44], [58, 196]]`.



| Fold | Train rows | Correct/heldout | Accuracy | Spearman | Seconds |

|---|---:|---:|---:|---:|---:|

| 1 | 448 | 89/113 | 0.787610619469 | 0.781068220290 | 76.467 |

| 2 | 449 | 88/112 | 0.785714285714 | 0.704587827219 | 76.829 |

| 3 | 449 | 98/112 | 0.875000000000 | 0.733284436690 | 79.077 |

| 4 | 449 | 93/112 | 0.830357142857 | 0.722114960168 | 71.440 |

| 5 | 449 | 91/112 | 0.812500000000 | 0.737117392087 | 71.561 |



Five fits; no reruns; seed 42. Probability range [0.0028449094388633966, 0.9977127313613892]; predicted classes {0: 321, 1: 240}. All OOF identity/finite checks PASS.



Loss: fold-weighted CE + 0.1 * mean((1-y)*(1-cos(a,b)) + y*max(0,cos(a,b))). Margin 0, no temperature. Final-layer mean pooling per sequence, excluding special/padding tokens; existing textual prefixes included. Representations share the original cross-encoder context. No projection head or extra encoder pass.



GPUs: NVIDIA A100 80GB PCIe, NVIDIA A100-SXM4-80GB; summed fit runtime 375.375 seconds. Includes checkpoint saving/hashing; excludes model setup and heldout inference. Concurrent folds, so summed time is not wall time or a billable GPU estimate.



Runtime: `{"python": "3.11.12", "torch": "2.2.1+cu121", "cuda": "12.1", "transformers": "4.38.1", "numpy": "1.26.4", "tokenizers": "0.15.2"}`.



Tests and full loss/epoch diagnostics are recorded in E11D_TRAINING_AUDIT.json and E11D_RESULTS.json. Prior A, C, teacher and E10 artifacts unchanged. No teacher calls, official-test access, tuning, commit, push or E11-E.



All five persisted checkpoints independently rehashed on the Modal volume. Runtime file manifest verified before fitting. Final tests passed; see FINAL_TESTS.json.
