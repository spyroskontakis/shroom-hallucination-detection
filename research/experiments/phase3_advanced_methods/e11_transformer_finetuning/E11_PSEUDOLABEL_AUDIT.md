# E11-B pseudo-label audit

Status: **PASS**. Protocol SHA256: `c0645ef01f885ef22b7abaf5634f8a62d66a3e7174cb0d07aa2a47fba425a5ac`.
Raw run: `e11-full-001`; all four unlabeled score files cover 28,649/28,649 keys; human whole-hypothesis MiniCheck covers 561/561.
Human FactCG, HHEM, and NLI features reuse their previously frozen local sources. HHEM remains a support score and was not inverted.
The locked fold IDs are **1–5**; the requested fold-0-through-4 counts map in that order to folds 1–5. The frozen purge includes the task/source/target pair check in addition to full sample, hypothesis, and task/reference.

| Fold | Training | Class 0 | Class 1 | Eligible | Purged | Accepted | Retained | Uncertain | Balance dropped | Converged |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| 1 | 445 | 246 | 199 | 28575 | 74 | 0 | 0 | 28575 | 0 | yes |
| 2 | 448 | 246 | 202 | 28623 | 26 | 50 | 0 | 28573 | 50 | yes |
| 3 | 449 | 245 | 204 | 28627 | 22 | 0 | 0 | 28627 | 0 | yes |
| 4 | 448 | 244 | 204 | 28611 | 38 | 44 | 0 | 28567 | 44 | yes |
| 5 | 445 | 245 | 200 | 28615 | 34 | 41 | 0 | 28574 | 41 | yes |

| Fold | Task | Eligible | Accepted H | Accepted non-H | Retained H | Retained non-H | Retained total | % eligible retained |
| ---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | DM | 9962 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| 1 | MT | 8615 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| 1 | PG | 9998 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| 2 | DM | 9988 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| 2 | MT | 8635 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| 2 | PG | 10000 | 0 | 50 | 0 | 0 | 0 | 0.00% |
| 3 | DM | 9992 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| 3 | MT | 8635 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| 3 | PG | 10000 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| 4 | DM | 9988 | 0 | 2 | 0 | 0 | 0 | 0.00% |
| 4 | MT | 8624 | 11 | 0 | 0 | 0 | 0 | 0.00% |
| 4 | PG | 9999 | 0 | 31 | 0 | 0 | 0 | 0.00% |
| 5 | DM | 9992 | 0 | 0 | 0 | 0 | 0 | 0.00% |
| 5 | MT | 8624 | 41 | 0 | 0 | 0 | 0 | 0.00% |
| 5 | PG | 9999 | 0 | 0 | 0 | 0 | 0 | 0.00% |

Retained p(H) ranges by fold (min / median / max):

- Fold 1: H {'min': None, 'median': None, 'max': None}; non-H {'min': None, 'median': None, 'max': None}; teacher iterations [19].
- Fold 2: H {'min': None, 'median': None, 'max': None}; non-H {'min': None, 'median': None, 'max': None}; teacher iterations [19].
- Fold 3: H {'min': None, 'median': None, 'max': None}; non-H {'min': None, 'median': None, 'max': None}; teacher iterations [19].
- Fold 4: H {'min': None, 'median': None, 'max': None}; non-H {'min': None, 'median': None, 'max': None}; teacher iterations [18].
- Fold 5: H {'min': None, 'median': None, 'max': None}; non-H {'min': None, 'median': None, 'max': None}; teacher iterations [20].

Cross-fold high-confidence conflicts: **0** sample keys. A conflict means at least one eligible fold teacher accepted H and another accepted non-H; no global resolution or consensus file was made.
Cross-fold acceptance assignments: H 52, non-H 83, uncertain 142916.

Each fold has its own teacher parameters, metadata, eligible-key manifest, complete eligible teacher scores, and retained pseudo-label JSONL in `teacher_stage/fold_<id>/`. Exact hashes, feature order, score-source provenance and software versions are in `E11_PSEUDOLABEL_MANIFEST.json`.

No student training, OOF evaluation, official-test access, GPU inference, Modal function, protocol edit, commit, or push occurred in this stage.

The frozen rules yielded **no retained pseudo-labels** in any fold: each task/fold lacked at least one high-confidence class, so the required within-task 50/50 pairing kept zero. This is insufficient for the planned pseudo-labeled student stage. DM, MT, and PG are all data-starved after balancing; cross-fold label conflicts are not a concern at this yield. The zero yield is a blocker to freezing a student protocol that assumes pseudo-labeled examples. Any different training strategy would require a separate decision and protocol freeze; the 0.95/0.05 thresholds were not changed.
