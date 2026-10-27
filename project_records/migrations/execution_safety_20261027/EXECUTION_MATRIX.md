# Phase 15 - Execution matrix

Date: 2026-10-27. Static inspection only. No research entry point, import, notebook, model or service was executed.

This matrix covers 53 procedure families or modes, not 53 independently runnable pipelines. The source survey covered 281 Python/notebook files and 11 dependency specifications. Historical snapshots and transitive helpers are not assumed to be standalone entry points. Dynamic imports, conditional branches and third-party initialization prevent a static survey from proving a complete runtime dependency closure.

## Status definitions

| Category | Meaning in this review |
|---|---|
| STATIC_ONLY | Inspect only in this phase; the selected path has prohibited cloud/network/training effects, an unresolved historical role or another explicit execution limitation. |
| REQUIRES_ISOLATION | Any future test requires a reviewed environment and enforced scratch-only writes before imports. Isolation has not been implemented here. |
| BLOCKED_MISSING_INPUTS | Required original data, row artifacts, model assets or intermediate results are absent from the public release. |
| BLOCKED_PROVENANCE | Frozen checks, original-source differences, protected locations or historical execution contracts prevent an exact replay in the current layout. |
| CANDIDATE_FOR_FUTURE_TEST | A narrow source-only or synthetic test might be considered later; no runtime PASS or approval is implied. |

Categories are cumulative. A primary category is used only for counting. “No model required” applies to the described stage, not every transitive import. Missing prerequisites below refer to public availability, not whether a separate private archive exists. No private archive was opened or restored.

## Procedure index

| ID | Procedure | Categories |
|---|---|---|
| canonical_prepare | Canonical data preparation | BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| canonical_features | Canonical NLI and similarity extraction | BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| canonical_cv | Canonical E1-E4 CV | BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| canonical_folds | Canonical fold-generation procedure | BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| descriptive_eda | Descriptive development EDA | BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| baseline_nb_1 | Historical baseline notebook variant: RAG/shroom_ensemble.ipynb | BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| baseline_nb_2 | Historical baseline notebook variant: data/2. EDA/shroom_ensemble.ipynb | BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| baseline_nb_3 | Historical baseline notebook variant: codex/data/2. EDA/shroom_final_implementation/shroom_ensemble.ipynb | BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| baseline_nb_4 | Historical baseline notebook variant: codex/data/2. EDA/shroom_final_implementation/shroom_ensemble_colab.ipynb | BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| baseline_nb_5 | Historical baseline notebook variant: codex/data/shroom_ensemble.ipynb | BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| augmentation_5 | Historical augmentation setting 5 samples per task | BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| augmentation_20 | Historical augmentation setting 20 samples per task | BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| augmentation_50 | Historical augmentation setting 50 samples per task | BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| augmentation_200 | Historical augmentation setting 200 samples per task | BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| historical_ablation | Older labeled-test synthetic ablation | BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| module1_main | E5 Module1 notebook | STATIC_ONLY; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| module1_trial | E5 Module1 notebook | STATIC_ONLY; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| module2_retrieval | E5 Module2 retrieval | BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| module2_phase_b_evaluation | E5 Module2 phase_b_evaluation | BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| module2_holdout_evaluation | E5 Module2 holdout_evaluation | BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| module3 | Module3 diagnostic/preparation history | STATIC_ONLY |
| module4_prepare-inputs | Module4 lexical builder mode prepare-inputs | BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| module4_acquire | Module4 lexical builder mode acquire | STATIC_ONLY; REQUIRES_ISOLATION |
| module4_offline-build | Module4 lexical builder mode offline-build | BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| module4_schannel | Module4 Schannel transport acquisition/build | STATIC_ONLY; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| module4_fusion | Module4 pinned features and fusion evaluation | BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| module4_source_verify | Source-only Module4 verifier candidate | CANDIDATE_FOR_FUTURE_TEST; REQUIRES_ISOLATION |
| e6_v1 | E6-v1 preparation/features/evaluation/report stages | BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| e6_v2 | E6-v2 preparation/features/evaluation/report stages | BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| e6_v3 | E6-v3 preparation/features/evaluation/report stages | BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| e6_acquisition | E6 acquisition/bootstrap utilities | STATIC_ONLY; REQUIRES_ISOLATION |
| e6_v4_initial | Initial E6-v4 compatibility diagnostic | STATIC_ONLY; BLOCKED_PROVENANCE; REQUIRES_ISOLATION |
| e6_v4_amended | Amended E6-v4 encoding/evaluation | BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| e7 | E7 preparation/evaluation/report chain | BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| e8 | E8 preparation/evaluation/report chain | BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| e8_original_report | Historical E8 report syntax failure | STATIC_ONLY; BLOCKED_PROVENANCE |
| e9_prepare | E9 baseline/preparation stages | BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| e9_api | E9 full decomposition API | STATIC_ONLY; BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| e9_evaluate | E9 claim NLI/evaluation/reporting | BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| minicheck | MiniCheck GPU scoring and return | STATIC_ONLY; BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| factcg_development | FactCG development scoring/return/evaluation | STATIC_ONLY; BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| e10_test | Retrospective test reconstruction/extraction/scoring | STATIC_ONLY; BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| e11a_prepare | E11-A preparation/validation | BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| e11a_train | E11-A fold worker | BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| e11b | E11-B scoring and teacher feasibility | BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| e11c_labels | E11-C API/batch labels and alternate rescue | STATIC_ONLY; BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| e11c_training | E11-C preparation/training/evaluation | BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| e11d_training | E11-D preparation/training/evaluation | BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| e11e_training | E11-E preparation/training/evaluation | BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION |
| remote_jobs_downloads | E11 Modal launch, remote CPU verification and downloads | STATIC_ONLY; BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS |
| prototype_help_config | Prototype help/config-only future isolation scope | REQUIRES_ISOLATION |
| future_helpers | Future pure/synthetic helper candidates, not whole-suite permission | CANDIDATE_FOR_FUTURE_TEST; REQUIRES_ISOLATION |
| archival_probes | Archived probes and historical tools | STATIC_ONLY; REQUIRES_ISOLATION |

## Cross-cutting dependencies

- Canonical data preparation supplies the original row manifests and folds; feature extraction supplies NLI/MPNet matrices; canonical CV consumes them. The public fold projection does not include the full original runtime schema.
- RAG Module2 protects the baseline notebook and depends on original retrieval/annotation/cache state. Module4 lexical and pinned feature artifacts feed E6; E7/E8 depend on E6-v1/Module4 provenance and fixed source locations.
- E6-v2/v3 and later feature/OOF baselines feed E9/E10. E10 retrospective extraction dynamically loads canonical and E6 helpers and compares original source hashes.
- E11 protocols depend on exact canonical normalization and teacher/detector identities. Local training workers remain training code even when separated from Modal launchers.
- Recorded requirements and model revisions are historical evidence, not permission to install packages or use a newer substitute. The current installed environment was not probed.

## Source-backed procedure records

## canonical_prepare - Canonical data preparation

**Categories:** BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [codex/canonical_evaluation_data_prep.py](<../../../codex/canonical_evaluation_data_prep.py>)

**Required inputs:** `codex/data/Trial/SHROOM_trial-v1.1/trial-v1.json`; `Dev/SHROOM_dev-v2/val.model-agnostic.json`; `codex/data/Labeled test/SHROOM_test-labeled/test.model-agnostic.json`; `codex/data/Unlabeled train/SHROOM_unlabeled-training-data-v2/train.model-agnostic.json`; `codex/data/6. Feature Extraction on Augmented Training Data/filtered_synthetic_data_balanced.csv`.

**Libraries / specifications:** pandas and stdlib; source imports recorded separately.

**Models:** No model required for the selected description; transitive initialization still needs review..

**Working-directory and path contract:** Resolve __file__/ROOT/OUT and injected sys.path exactly; changing CWD alone does not relocate fixed paths.

**Outputs:** `Canonical manifests, overlap/duplicate CSVs and folds under codex/`.

**Potential tracked/historical writes:** Writes canonical input locations; no permission to replace originals.

**Network, downloads and cloud:** No model/API stage in this script observed; library initialization still needs isolation.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `codex/data/Trial/SHROOM_trial-v1.1/trial-v1.json`: absent; `Dev/SHROOM_dev-v2/val.model-agnostic.json`: absent; `codex/data/Labeled test/SHROOM_test-labeled/test.model-agnostic.json`: absent; `codex/data/Unlabeled train/SHROOM_unlabeled-training-data-v2/train.model-agnostic.json`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `codex/canonical_evaluation_data_prep.py` SHA-256 `d98717c7b56c5f3298b8b99c89eac2687e70e83459f42100a017bacc56d5e8d5`.
  - Observed imports (selection): `from __future__ import annotations`; `import csv`; `import hashlib`; `import json`; `import unicodedata`; `from collections import Counter, defaultdict`; `from pathlib import Path`; `from typing import Any`.
  - IO/model/network markers (selection): `line 278: write_csv(DUPLICATE_AUDIT_PATH, duplicate_audit_rows, audit_fields)`; `line 324: write_csv(EXCLUDED_HUMAN_TEST_OVERLAPS_PATH, human_test_overlap_rows, ['exact_text_key', 'development_origin', 'development_row_index', 'test_id', 'test_row_index', 'task`; `line 373: write_csv(CANONICAL_HUMAN_MANIFEST_PATH, canonical_rows, canonical_fields)`; `line 468: write_csv(CANONICAL_SYNTHETIC_MANIFEST_PATH, synthetic_rows, synthetic_fields)`.

## canonical_features - Canonical NLI and similarity extraction

**Categories:** BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [codex/canonical_feature_extraction.py](<../../../codex/canonical_feature_extraction.py>)

**Required inputs:** `codex/canonical_human_development_manifest.csv`; `codex/canonical_fold_assignments.csv`; `codex/canonical_synthetic_diagnostic_manifest.csv`; `Original trial-feature compatibility input`.

**Libraries / specifications:** numpy,pandas,torch,transformers,scipy,sentence_transformers; recorded canonical runtime.

**Models:** `microsoft/deberta-large-mnli`; `sentence-transformers/all-mpnet-base-v2`.

**Working-directory and path contract:** Resolve __file__/ROOT/OUT and injected sys.path exactly; changing CWD alone does not relocate fixed paths.

**Outputs:** `Six matrices, checkpoints, metadata, audit CSVs and log under codex/canonical_feature_outputs/`.

**Potential tracked/historical writes:** Writes beside tracked metadata/quality/compatibility records.

**Network, downloads and cloud:** Local cache loading and offline defaults observed; setdefault is not a network enforcement boundary.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `codex/canonical_human_development_manifest.csv`: absent; `codex/canonical_fold_assignments.csv`: absent; `codex/canonical_synthetic_diagnostic_manifest.csv`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `codex/canonical_feature_extraction.py` SHA-256 `946dbdd11397056ff6d9257dca5bb0c9900fe3e73a9e6f28b5c093d08cedba24`.
  - Observed imports (selection): `from __future__ import annotations`; `import csv`; `import hashlib`; `import json`; `import logging`; `import math`; `import os`; `import platform`.
  - IO/model/network markers (selection): `line 29: os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')`; `line 30: os.environ.setdefault('HF_HUB_OFFLINE', '1')`; `line 99: OUTPUT_DIR.mkdir(exist_ok=True)`; `line 100: CHECKPOINT_DIR.mkdir(exist_ok=True)`.

## canonical_cv - Canonical E1-E4 CV

**Categories:** BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [codex/canonical_development_cv.py](<../../../codex/canonical_development_cv.py>)

**Required inputs:** `codex/canonical_human_development_manifest.csv`; `codex/canonical_fold_assignments.csv`; `codex/canonical_feature_outputs/canonical_human_14_features.csv`; `codex/canonical_feature_outputs/canonical_synthetic_14_features.csv`; `Feature metadata and original compatibility rows`.

**Libraries / specifications:** numpy,pandas,scipy,scikit-learn; recorded canonical runtime.

**Models:** No model required for the selected description; transitive initialization still needs review..

**Working-directory and path contract:** Resolve __file__/ROOT/OUT and injected sys.path exactly; changing CWD alone does not relocate fixed paths. CANONICAL_CV_OUTPUT_DIR exists but UNMATCHED_COMPATIBILITY_ROWS remains in FEATURE_DIR; output mkdir occurs at import.

**Outputs:** `CV output directory plus possible feature-directory compatibility CSV`.

**Potential tracked/historical writes:** Default output rewrites tracked aggregate/selection/audit files; override is incomplete for all writes.

**Network, downloads and cloud:** RF training/evaluation, even without pretrained model inference, is prohibited now.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `codex/canonical_human_development_manifest.csv`: absent; `codex/canonical_fold_assignments.csv`: absent; `codex/canonical_feature_outputs/canonical_human_14_features.csv`: absent; `codex/canonical_feature_outputs/canonical_synthetic_14_features.csv`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `codex/canonical_development_cv.py` SHA-256 `cde3f829ea68ee35ded568953b5d59ffabbd854a9da6e11d9436ed01403b49d2`.
  - Observed imports (selection): `from __future__ import annotations`; `import hashlib`; `import json`; `import logging`; `import os`; `import platform`; `import sys`; `import time`.
  - IO/model/network markers (selection): `line 44: OUTPUT_DIR.mkdir(exist_ok=True)`; `line 43: os.environ.get('CANONICAL_CV_OUTPUT_DIR', ROOT / 'canonical_cv_outputs')`; `line 187: out.to_csv(UNMATCHED_COMPATIBILITY_ROWS, index=False)`; `line 597: (OUTPUT_DIR / 'canonical_cv_results_summary.md').write_text('\n'.join(lines), encoding='utf-8')`.

## canonical_folds - Canonical fold-generation procedure

**Categories:** BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [codex/regenerate_canonical_folds_sklearn.py](<../../../codex/regenerate_canonical_folds_sklearn.py>)

**Required inputs:** `codex/canonical_human_development_manifest.csv`.

**Libraries / specifications:** pandas,scikit-learn and original versions.

**Models:** No model required for the selected description; transitive initialization still needs review..

**Working-directory and path contract:** Resolve __file__/ROOT/OUT and injected sys.path exactly; changing CWD alone does not relocate fixed paths.

**Outputs:** `codex/canonical_fold_assignments.csv`; `codex/canonical_fold_generation_metadata.json`; `codex/canonical_fold_balance_audit.csv`.

**Potential tracked/historical writes:** Write/truncate helpers can overwrite original folds and tracked metadata.

**Network, downloads and cloud:** No API/model observed; regeneration is not authorized and cannot substitute for original frozen folds.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `codex/canonical_human_development_manifest.csv`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `codex/regenerate_canonical_folds_sklearn.py` SHA-256 `97751673e5b1e00ba616b2105884584573076db4e3a2e4604effa0655ff592a7`.
  - Observed imports (selection): `from __future__ import annotations`; `import csv`; `import hashlib`; `import json`; `import platform`; `import sys`; `from collections import Counter`; `from datetime import datetime`.
  - IO/model/network markers (selection): `line 144: output.to_csv(OUTPUT_FOLDS, index=False)`; `line 145: balance.to_csv(BALANCE_AUDIT_CSV, index=False)`; `line 194: METADATA_JSON.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')`; `line 44: writer.writeheader()`.

## descriptive_eda - Descriptive development EDA

**Categories:** BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [codex/prompt6_development_eda.py](<../../../codex/prompt6_development_eda.py>)

**Required inputs:** `Original agnostic and aware development JSONs`.

**Libraries / specifications:** Observed pandas/numpy/plot/tokenizer imports; exact source evidence below, no inferred latest pins.

**Models:** No model required for the selected description; transitive initialization still needs review..

**Working-directory and path contract:** HERE.parent selects project root; output mkdir is at module scope.

**Outputs:** `EDA figures and CSVs in source-defined output root`.

**Potential tracked/historical writes:** Import and plotting/tokenizer initialization can write before helper calls.

**Network, downloads and cloud:** Tokenizer/model/cache behavior depends on selected helper; no blanket no-download claim.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Static evidence (selected observations, not a call-graph proof):**
- `codex/prompt6_development_eda.py` SHA-256 `4c05f2994717dd53bffe3154cf766e2c4c9d9a78880fe4b04f09c2484f457eeb`.
  - Observed imports (selection): `from __future__ import annotations`; `import json`; `from pathlib import Path`; `import matplotlib`; `import matplotlib.pyplot as plt`; `import numpy as np`; `import pandas as pd`; `from transformers import AutoTokenizer`.
  - IO/model/network markers (selection): `line 27: OUTPUT_DIR.mkdir(parents=True, exist_ok=True)`; `line 57: fig.savefig(OUTPUT_DIR / filename, dpi=300, bbox_inches='tight')`; `line 108: inspection_table(frames).to_csv(OUTPUT_DIR / 'development_inspection_summary.csv', index=False)`; `line 124: pd.DataFrame(schema_rows).to_csv(OUTPUT_DIR / 'development_schema_and_missing.csv', index=False)`.

## baseline_nb_1 - Historical baseline notebook variant: RAG/shroom_ensemble.ipynb

**Categories:** BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/shroom_ensemble.ipynb](<../../../RAG/shroom_ensemble.ipynb>)

**Required inputs:** `Historical development/features and prior in-memory cells; Colab variant needs supplied feature CSV`.

**Libraries / specifications:** Notebook imports/cells and available requirements, not a universal environment.

**Models:** `NLI/MPNet where feature stages are selected; generation settings vary by notebook cell`.

**Working-directory and path contract:** Kernel CWD differs from notebook storage; SHROOM_PROJECT_ROOT, shared frames/folds and Colab upload/install branches apply.

**Outputs:** `CWD figures, aggregate/OOF CSVs and variant-specific augmentation products`.

**Potential tracked/historical writes:** Can overwrite/recreate archived CSV names at old paths.

**Network, downloads and cloud:** Mixed model, pip/upload/API/generation branches; no Run All authorization.

**Frozen/provenance constraints:** RAG baseline is protected by Module2; codex/data baseline is read by E10 recovery. Keep all distinct variants.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/shroom_ensemble.ipynb` SHA-256 `fe57bcdfe1b3668bb37a6c1666ec244f8c2519072dab1e52e387393f061e2bd2`.
  - Observed imports (selection): `import json`; `from pathlib import Path`; `import pandas as pd`; `import numpy as np`; `import matplotlib.pyplot as plt`; `from sklearn.metrics import accuracy_score`; `from scipy.stats import spearmanr`; `from transformers import AutoTokenizer`.
  - IO/model/network markers (selection): `cell 6, line 70: __import__('os').environ.get('SHROOM_PROJECT_ROOT', '.')`; `cell 11, line 44: folder.mkdir(parents=True, exist_ok=True)`; `cell 11, line 59: plt.savefig(folder / f'{name}.png', dpi=300, bbox_inches='tight')`; `cell 19, line 19: save_plot(f'{safe_name(name)}_label_distribution', folder=LABEL_DIST_DIR)`.

## baseline_nb_2 - Historical baseline notebook variant: data/2. EDA/shroom_ensemble.ipynb

**Categories:** BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [data/2. EDA/shroom_ensemble.ipynb](<../../../data/2.%20EDA/shroom_ensemble.ipynb>)

**Required inputs:** `Historical development/features and prior in-memory cells; Colab variant needs supplied feature CSV`.

**Libraries / specifications:** Notebook imports/cells and available requirements, not a universal environment.

**Models:** `NLI/MPNet where feature stages are selected; generation settings vary by notebook cell`.

**Working-directory and path contract:** Kernel CWD differs from notebook storage; SHROOM_PROJECT_ROOT, shared frames/folds and Colab upload/install branches apply.

**Outputs:** `CWD figures, aggregate/OOF CSVs and variant-specific augmentation products`.

**Potential tracked/historical writes:** Can overwrite/recreate archived CSV names at old paths.

**Network, downloads and cloud:** Mixed model, pip/upload/API/generation branches; no Run All authorization.

**Frozen/provenance constraints:** RAG baseline is protected by Module2; codex/data baseline is read by E10 recovery. Keep all distinct variants.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Static evidence (selected observations, not a call-graph proof):**
- `data/2. EDA/shroom_ensemble.ipynb` SHA-256 `23eea79c2cafa1395b1d57e4e9818569ad64feddb61e0ef719bd2f4b36bda5a7`.
  - Observed imports (selection): `import json`; `from pathlib import Path`; `import pandas as pd`; `import numpy as np`; `import matplotlib.pyplot as plt`; `from sklearn.metrics import accuracy_score`; `from scipy.stats import spearmanr`; `from transformers import AutoTokenizer`.
  - IO/model/network markers (selection): `cell 7, line 70: __import__('os').environ.get('SHROOM_PROJECT_ROOT', '.')`; `cell 12, line 44: folder.mkdir(parents=True, exist_ok=True)`; `cell 12, line 59: plt.savefig(folder / f'{name}.png', dpi=300, bbox_inches='tight')`; `cell 20, line 19: save_plot(f'{safe_name(name)}_label_distribution', folder=LABEL_DIST_DIR)`.

## baseline_nb_3 - Historical baseline notebook variant: codex/data/2. EDA/shroom_final_implementation/shroom_ensemble.ipynb

**Categories:** BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [codex/data/2. EDA/shroom_final_implementation/shroom_ensemble.ipynb](<../../../codex/data/2.%20EDA/shroom_final_implementation/shroom_ensemble.ipynb>)

**Required inputs:** `Historical development/features and prior in-memory cells; Colab variant needs supplied feature CSV`.

**Libraries / specifications:** Notebook imports/cells and available requirements, not a universal environment.

**Models:** `NLI/MPNet where feature stages are selected; generation settings vary by notebook cell`.

**Working-directory and path contract:** Kernel CWD differs from notebook storage; SHROOM_PROJECT_ROOT, shared frames/folds and Colab upload/install branches apply.

**Outputs:** `CWD figures, aggregate/OOF CSVs and variant-specific augmentation products`.

**Potential tracked/historical writes:** Can overwrite/recreate archived CSV names at old paths.

**Network, downloads and cloud:** Mixed model, pip/upload/API/generation branches; no Run All authorization.

**Frozen/provenance constraints:** RAG baseline is protected by Module2; codex/data baseline is read by E10 recovery. Keep all distinct variants.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Static evidence (selected observations, not a call-graph proof):**
- `codex/data/2. EDA/shroom_final_implementation/shroom_ensemble.ipynb` SHA-256 `92001227fff7f13ce9ed2447c01a42f668b3fe5d25b6240e1f02ffe650909f3a`.
  - Observed imports (selection): `import json`; `from pathlib import Path`; `import pandas as pd`; `import numpy as np`; `import matplotlib.pyplot as plt`; `from sklearn.metrics import accuracy_score`; `from scipy.stats import spearmanr`; `from transformers import AutoTokenizer`.
  - IO/model/network markers (selection): `cell 7, line 70: __import__('os').environ.get('SHROOM_PROJECT_ROOT', '.')`; `cell 12, line 44: folder.mkdir(parents=True, exist_ok=True)`; `cell 12, line 59: plt.savefig(folder / f'{name}.png', dpi=300, bbox_inches='tight')`; `cell 20, line 19: save_plot(f'{safe_name(name)}_label_distribution', folder=LABEL_DIST_DIR)`.

## baseline_nb_4 - Historical baseline notebook variant: codex/data/2. EDA/shroom_final_implementation/shroom_ensemble_colab.ipynb

**Categories:** BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [codex/data/2. EDA/shroom_final_implementation/shroom_ensemble_colab.ipynb](<../../../codex/data/2.%20EDA/shroom_final_implementation/shroom_ensemble_colab.ipynb>)

**Required inputs:** `Historical development/features and prior in-memory cells; Colab variant needs supplied feature CSV`.

**Libraries / specifications:** Notebook imports/cells and available requirements, not a universal environment.

**Models:** `NLI/MPNet where feature stages are selected; generation settings vary by notebook cell`.

**Working-directory and path contract:** Kernel CWD differs from notebook storage; SHROOM_PROJECT_ROOT, shared frames/folds and Colab upload/install branches apply.

**Outputs:** `CWD figures, aggregate/OOF CSVs and variant-specific augmentation products`.

**Potential tracked/historical writes:** Can overwrite/recreate archived CSV names at old paths.

**Network, downloads and cloud:** Mixed model, pip/upload/API/generation branches; no Run All authorization.

**Frozen/provenance constraints:** RAG baseline is protected by Module2; codex/data baseline is read by E10 recovery. Keep all distinct variants.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Static evidence (selected observations, not a call-graph proof):**
- `codex/data/2. EDA/shroom_final_implementation/shroom_ensemble_colab.ipynb` SHA-256 `7f8dfe79a4c4effd025c3369f06aba90b04799f2266b608b7f2d362fe366b51c`.
  - Observed imports (selection): `from google.colab import files`.
  - IO/model/network markers (selection): `cell 21, line 2: OUTPUT_DIR.mkdir(parents=True, exist_ok=True)`; `cell 21, line 4: final_results_df.to_csv(OUTPUT_DIR / 'final_results_summary.csv', index=False)`; `cell 21, line 5: importance_df.to_csv(OUTPUT_DIR / 'e3_feature_importance.csv', index=False)`; `cell 21, line 8: cv_results[experiment_id].to_csv(OUTPUT_DIR / f'{experiment_id.lower()}_cv_results.csv', index=False)`.

## baseline_nb_5 - Historical baseline notebook variant: codex/data/shroom_ensemble.ipynb

**Categories:** BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [codex/data/shroom_ensemble.ipynb](<../../../codex/data/shroom_ensemble.ipynb>)

**Required inputs:** `Historical development/features and prior in-memory cells; Colab variant needs supplied feature CSV`.

**Libraries / specifications:** Notebook imports/cells and available requirements, not a universal environment.

**Models:** `NLI/MPNet where feature stages are selected; generation settings vary by notebook cell`.

**Working-directory and path contract:** Kernel CWD differs from notebook storage; SHROOM_PROJECT_ROOT, shared frames/folds and Colab upload/install branches apply.

**Outputs:** `CWD figures, aggregate/OOF CSVs and variant-specific augmentation products`.

**Potential tracked/historical writes:** Can overwrite/recreate archived CSV names at old paths.

**Network, downloads and cloud:** Mixed model, pip/upload/API/generation branches; no Run All authorization.

**Frozen/provenance constraints:** RAG baseline is protected by Module2; codex/data baseline is read by E10 recovery. Keep all distinct variants.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Static evidence (selected observations, not a call-graph proof):**
- `codex/data/shroom_ensemble.ipynb` SHA-256 `53e60b98c7eba15aa3fde27559885bdae70bf936513dfff60fda5c6a01486d03`.
  - Observed imports (selection): `import json`; `from pathlib import Path`; `import pandas as pd`; `import numpy as np`; `import matplotlib.pyplot as plt`; `from transformers import AutoTokenizer`; `from tqdm.auto import tqdm`; `from transformers import pipeline`.
  - IO/model/network markers (selection): `cell 2, line 3: __import__('os').environ.get('SHROOM_PROJECT_ROOT', '.')`; `cell 10, line 5: AutoTokenizer.from_pretrained('microsoft/deberta-v3-large')`; `cell 28, line 2: df.to_csv('nli_features_dataset.csv', index=False)`; `cell 34, line 3: nli_oof_df.to_csv('nli_baseline_oof_predictions.csv', index=False)`.

## augmentation_5 - Historical augmentation setting 5 samples per task

**Categories:** BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [codex/data/5. Augmentation/5 samples - augmentation_outputs_vertex/shroom_ensemble.ipynb](<../../../codex/data/5.%20Augmentation/5%20samples%20-%20augmentation_outputs_vertex/shroom_ensemble.ipynb>)

**Required inputs:** `Original data/features and prior notebook state`.

**Libraries / specifications:** Notebook generation/feature imports and recorded settings.

**Models:** `Notebook-declared Gemini/NLI/MPNet settings, not inferred from filename`.

**Working-directory and path contract:** CWD augmentation_outputs_vertex or project data/6 suffix; sample setting does not prove generated-row count.

**Outputs:** `Raw/filtered/balanced synthetic data and generation/feature checkpoints`.

**Potential tracked/historical writes:** Can write project data/output directories and old baselines.

**Network, downloads and cloud:** Generation, model downloads or package-install branches require separate approval.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Static evidence (selected observations, not a call-graph proof):**
- `codex/data/5. Augmentation/5 samples - augmentation_outputs_vertex/shroom_ensemble.ipynb` SHA-256 `ad234f1eecd3ae1a5ebd12116a762f154d3b1f0e44bb28e8c51b4f4eff79b4c3`.
  - Observed imports (selection): `import json`; `from pathlib import Path`; `import pandas as pd`; `import numpy as np`; `import matplotlib.pyplot as plt`; `from transformers import AutoTokenizer`; `from tqdm.auto import tqdm`; `from transformers import pipeline`.
  - IO/model/network markers (selection): `cell 2, line 3: __import__('os').environ.get('SHROOM_PROJECT_ROOT', '.')`; `cell 10, line 5: AutoTokenizer.from_pretrained('microsoft/deberta-v3-large')`; `cell 28, line 2: df.to_csv('nli_features_dataset.csv', index=False)`; `cell 34, line 3: nli_oof_df.to_csv('nli_baseline_oof_predictions.csv', index=False)`.

## augmentation_20 - Historical augmentation setting 20 samples per task

**Categories:** BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [codex/data/5. Augmentation/20 samples - augmentation_outputs_vertex/shroom_ensemble.ipynb](<../../../codex/data/5.%20Augmentation/20%20samples%20-%20augmentation_outputs_vertex/shroom_ensemble.ipynb>)

**Required inputs:** `Original data/features and prior notebook state`.

**Libraries / specifications:** Notebook generation/feature imports and recorded settings.

**Models:** `Notebook-declared Gemini/NLI/MPNet settings, not inferred from filename`.

**Working-directory and path contract:** CWD augmentation_outputs_vertex or project data/6 suffix; sample setting does not prove generated-row count.

**Outputs:** `Raw/filtered/balanced synthetic data and generation/feature checkpoints`.

**Potential tracked/historical writes:** Can write project data/output directories and old baselines.

**Network, downloads and cloud:** Generation, model downloads or package-install branches require separate approval.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Static evidence (selected observations, not a call-graph proof):**
- `codex/data/5. Augmentation/20 samples - augmentation_outputs_vertex/shroom_ensemble.ipynb` SHA-256 `a608743d08995ffe8572fb3e7d08c94f616c35ff8445834f30e2fe13b42fb321`.
  - Observed imports (selection): `import json`; `from pathlib import Path`; `import pandas as pd`; `import numpy as np`; `import matplotlib.pyplot as plt`; `from transformers import AutoTokenizer`; `from tqdm.auto import tqdm`; `from transformers import pipeline`.
  - IO/model/network markers (selection): `cell 2, line 3: __import__('os').environ.get('SHROOM_PROJECT_ROOT', '.')`; `cell 10, line 5: AutoTokenizer.from_pretrained('microsoft/deberta-v3-large')`; `cell 28, line 2: df.to_csv('nli_features_dataset.csv', index=False)`; `cell 34, line 3: nli_oof_df.to_csv('nli_baseline_oof_predictions.csv', index=False)`.

## augmentation_50 - Historical augmentation setting 50 samples per task

**Categories:** BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [codex/data/5. Augmentation/50 samples - augmentation_outputs_vertex/shroom_ensemble.ipynb](<../../../codex/data/5.%20Augmentation/50%20samples%20-%20augmentation_outputs_vertex/shroom_ensemble.ipynb>)

**Required inputs:** `Original data/features and prior notebook state`.

**Libraries / specifications:** Notebook generation/feature imports and recorded settings.

**Models:** `Notebook-declared Gemini/NLI/MPNet settings, not inferred from filename`.

**Working-directory and path contract:** CWD augmentation_outputs_vertex or project data/6 suffix; sample setting does not prove generated-row count.

**Outputs:** `Raw/filtered/balanced synthetic data and generation/feature checkpoints`.

**Potential tracked/historical writes:** Can write project data/output directories and old baselines.

**Network, downloads and cloud:** Generation, model downloads or package-install branches require separate approval.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Static evidence (selected observations, not a call-graph proof):**
- `codex/data/5. Augmentation/50 samples - augmentation_outputs_vertex/shroom_ensemble.ipynb` SHA-256 `2b660baa391c560984757f28f447d49671b9d256cbdb7f4d060457582a6d686a`.
  - Observed imports (selection): `import json`; `from pathlib import Path`; `import pandas as pd`; `import numpy as np`; `import matplotlib.pyplot as plt`; `from transformers import AutoTokenizer`; `from tqdm.auto import tqdm`; `from transformers import pipeline`.
  - IO/model/network markers (selection): `cell 2, line 3: __import__('os').environ.get('SHROOM_PROJECT_ROOT', '.')`; `cell 10, line 5: AutoTokenizer.from_pretrained('microsoft/deberta-v3-large')`; `cell 28, line 2: df.to_csv('nli_features_dataset.csv', index=False)`; `cell 34, line 3: nli_oof_df.to_csv('nli_baseline_oof_predictions.csv', index=False)`.

## augmentation_200 - Historical augmentation setting 200 samples per task

**Categories:** BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [codex/data/5. Augmentation/200 samples - augmentation_outputs_vertex/shroom_ensemble.ipynb](<../../../codex/data/5.%20Augmentation/200%20samples%20-%20augmentation_outputs_vertex/shroom_ensemble.ipynb>)

**Required inputs:** `Original data/features and prior notebook state`.

**Libraries / specifications:** Notebook generation/feature imports and recorded settings.

**Models:** `Notebook-declared Gemini/NLI/MPNet settings, not inferred from filename`.

**Working-directory and path contract:** CWD augmentation_outputs_vertex or project data/6 suffix; sample setting does not prove generated-row count.

**Outputs:** `Raw/filtered/balanced synthetic data and generation/feature checkpoints`.

**Potential tracked/historical writes:** Can write project data/output directories and old baselines.

**Network, downloads and cloud:** Generation, model downloads or package-install branches require separate approval.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Static evidence (selected observations, not a call-graph proof):**
- `codex/data/5. Augmentation/200 samples - augmentation_outputs_vertex/shroom_ensemble.ipynb` SHA-256 `2b437a13e2d4eb29bc7f4c56a9401902ed2514daa7139a308d743f65166cd137`.
  - Observed imports (selection): `import json`; `from pathlib import Path`; `import pandas as pd`; `import numpy as np`; `import matplotlib.pyplot as plt`; `from transformers import AutoTokenizer`; `from tqdm.auto import tqdm`; `from transformers import pipeline`.
  - IO/model/network markers (selection): `cell 2, line 3: __import__('os').environ.get('SHROOM_PROJECT_ROOT', '.')`; `cell 10, line 5: AutoTokenizer.from_pretrained('microsoft/deberta-v3-large')`; `cell 28, line 2: df.to_csv('nli_features_dataset.csv', index=False)`; `cell 34, line 3: nli_oof_df.to_csv('nli_baseline_oof_predictions.csv', index=False)`.

## historical_ablation - Older labeled-test synthetic ablation

**Categories:** BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [data/7. Ablation Synthetic Data/7.Ablation_Synthetic_Data.ipynb](<../../../data/7.%20Ablation%20Synthetic%20Data/7.Ablation_Synthetic_Data.ipynb>)

**Required inputs:** `data/7. Ablation Synthetic Data/4.nli_similarity_features_dataset.csv`; `data/7. Ablation Synthetic Data/6.nli_similarity_features_dataset.csv`.

**Libraries / specifications:** numpy,pandas,scipy,scikit-learn.

**Models:** No model required for the selected description; transitive initialization still needs review..

**Working-directory and path contract:** DATA_DIR=CWD if evaluation input exists, else SHROOM_PROJECT_ROOT/data/7. Ablation Synthetic Data.

**Outputs:** `Seven archived aggregates plus predictions and individual error rows`.

**Potential tracked/historical writes:** Can recreate old archive paths and overwrite originals.

**Network, downloads and cloud:** Observed ablation needs RF fits; no current permission even when API-free.

**Frozen/provenance constraints:** Historical labeled-test protocol, never canonical development-561 or development-499.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `data/7. Ablation Synthetic Data/4.nli_similarity_features_dataset.csv`: absent; `data/7. Ablation Synthetic Data/6.nli_similarity_features_dataset.csv`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `data/7. Ablation Synthetic Data/7.Ablation_Synthetic_Data.ipynb` SHA-256 `143214d822c933cc2bf249bd71503635e381556865876c383fcf809e827d18e4`.
  - Observed imports (selection): `import numpy as np`; `import pandas as pd`; `from pathlib import Path`; `from IPython.display import display`; `from sklearn.ensemble import RandomForestRegressor`; `from sklearn.metrics import accuracy_score, mean_absolute_error`; `from sklearn.model_selection import train_test_split`; `from scipy.stats import spearmanr`.
  - IO/model/network markers (selection): `cell 2, line 17: __import__('os').environ.get('SHROOM_PROJECT_ROOT', '.')`; `cell 12, line 7: summary_df.to_csv(DATA_DIR / 'ablation_summary_results.csv', index=False)`; `cell 14, line 7: per_task_df.to_csv(DATA_DIR / 'ablation_per_task_results.csv', index=False)`; `cell 16, line 7: importance_df.to_csv(DATA_DIR / 'ablation_feature_importance.csv', index=False)`.

## module1_main - E5 Module1 notebook

**Categories:** STATIC_ONLY; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/shroom_rag_e5_module1.ipynb](<../../../RAG/shroom_rag_e5_module1.ipynb>)

**Required inputs:** `Original unlabeled/prototype rows and cache`.

**Libraries / specifications:** RAG/requirements-rag-module1.txt.

**Models:** `Gemini model setting in actual notebook`.

**Working-directory and path contract:** SHROOM_RAG_OUTPUT_DIR or results/rag_module1 relative to kernel CWD.

**Outputs:** `Response cache and prototype report outputs`.

**Potential tracked/historical writes:** Cache appends/reports can go into repository.

**Network, downloads and cloud:** API client branches need new cloud/cost authorization; never import/run for discovery.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/shroom_rag_e5_module1.ipynb` SHA-256 `081dd955a3dc0bd42daface9a03f0dcc3522bd57fa987521b928c309fbeecfa2`.
  - Observed imports (selection): `import hashlib`; `import json`; `import os`; `import re`; `import time`; `import unicodedata`; `from pathlib import Path`; `import numpy as np`.
  - IO/model/network markers (selection): `cell 4, line 23: os.environ.get('SHROOM_RAG_MODEL', 'gemini-2.5-flash-lite')`; `cell 4, line 28: OUTPUT_DIR.mkdir(parents=True, exist_ok=True)`; `cell 4, line 26: os.environ.get('SHROOM_DATA_DIR', str(DEFAULT_DATA_DIR))`; `cell 4, line 27: os.environ.get('SHROOM_RAG_OUTPUT_DIR', 'results/rag_module1')`.

## module1_trial - E5 Module1 notebook

**Categories:** STATIC_ONLY; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/shroom_rag_e5_module1_gemini_trial.ipynb](<../../../RAG/shroom_rag_e5_module1_gemini_trial.ipynb>)

**Required inputs:** `Original unlabeled/prototype rows and cache`.

**Libraries / specifications:** RAG/requirements-rag-module1.txt.

**Models:** `Gemini model setting in actual notebook`.

**Working-directory and path contract:** SHROOM_RAG_OUTPUT_DIR or results/rag_module1 relative to kernel CWD.

**Outputs:** `Response cache and prototype report outputs`.

**Potential tracked/historical writes:** Cache appends/reports can go into repository.

**Network, downloads and cloud:** API client branches need new cloud/cost authorization; never import/run for discovery.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/shroom_rag_e5_module1_gemini_trial.ipynb` SHA-256 `8ee129ecca5c88d0bf1945b23c5e49703ec6df5c6c31a6efa957ff1750d19c14`.
  - Observed imports (selection): `import hashlib`; `import json`; `import os`; `import re`; `import time`; `import tempfile`; `import unicodedata`; `from pathlib import Path`.
  - IO/model/network markers (selection): `cell 4, line 24: os.environ.get('SHROOM_RAG_MODEL', 'gemini-2.5-flash-lite')`; `cell 4, line 29: OUTPUT_DIR.mkdir(parents=True, exist_ok=True)`; `cell 4, line 27: os.environ.get('SHROOM_DATA_DIR', str(DEFAULT_DATA_DIR))`; `cell 4, line 28: os.environ.get('SHROOM_RAG_OUTPUT_DIR', 'results/rag_module1')`.

## module2_retrieval - E5 Module2 retrieval

**Categories:** BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/shroom_rag_e5_module2_retrieval.ipynb](<../../../RAG/shroom_rag_e5_module2_retrieval.ipynb>)

**Required inputs:** `Original source pool, Module1 cache, frozen ranking/dense cache and stage-appropriate human annotations`.

**Libraries / specifications:** RAG/requirements-rag-module1.txt; RAG/requirements-rag-module2.txt.

**Models:** `Pinned MPNet for dense-retrieval stage`.

**Working-directory and path contract:** SHROOM_PROJECT_ROOT/RAG ROOT; fixed phase-A/annotation/evaluation/holdout paths.

**Outputs:** `Candidates, embeddings, row annotations/decisions and aggregate metrics`.

**Potential tracked/historical writes:** May write tracked Module2 metrics and reports.

**Network, downloads and cloud:** Some stages load model assets; evaluation imports cannot be assumed write-free.

**Frozen/provenance constraints:** Protected baseline/helper/cache hashes and original split/annotation provenance.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/shroom_rag_e5_module2_retrieval.ipynb` SHA-256 `ee2eaefadb52b3fa4abda0ed11166c53438e2fd8e1e9a8f39fe1962ed8b7c82e`.
  - Observed imports (selection): `import hashlib`; `import json`; `import os`; `import random`; `import re`; `import sys`; `import unicodedata`; `from importlib.metadata import version`.
  - IO/model/network markers (selection): `cell 5, line 7: OUTPUT_DIR.mkdir(parents=True, exist_ok=True)`; `cell 5, line 1: __import__('os').environ.get('SHROOM_PROJECT_ROOT', '.')`; `cell 15, line 3: json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')`; `cell 15, line 3: json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(',', ':'))`.

## module2_phase_b_evaluation - E5 Module2 phase_b_evaluation

**Categories:** BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/shroom_rag_e5_module2_phase_b_evaluation.ipynb](<../../../RAG/shroom_rag_e5_module2_phase_b_evaluation.ipynb>)

**Required inputs:** `Original source pool, Module1 cache, frozen ranking/dense cache and stage-appropriate human annotations`.

**Libraries / specifications:** RAG/requirements-rag-module1.txt; RAG/requirements-rag-module2.txt.

**Models:** `Pinned MPNet for dense-retrieval stage`.

**Working-directory and path contract:** SHROOM_PROJECT_ROOT/RAG ROOT; fixed phase-A/annotation/evaluation/holdout paths.

**Outputs:** `Candidates, embeddings, row annotations/decisions and aggregate metrics`.

**Potential tracked/historical writes:** May write tracked Module2 metrics and reports.

**Network, downloads and cloud:** Some stages load model assets; evaluation imports cannot be assumed write-free.

**Frozen/provenance constraints:** Protected baseline/helper/cache hashes and original split/annotation provenance.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/shroom_rag_e5_module2_phase_b_evaluation.ipynb` SHA-256 `c5abdb31f21934959875a594cc7004b7cdcbc82d91d9c577cac0b6f7834b2315`.
  - Observed imports (selection): `from __future__ import annotations`; `import csv, hashlib, json, math, os, pathlib, statistics, tempfile`; `from collections import Counter, defaultdict`; `import io`.
  - IO/model/network markers (selection): `cell 1, line 7: __import__('os').environ.get('SHROOM_PROJECT_ROOT', '.')`; `cell 13, line 20: atomic_write_text(OUTPUTS['metrics'], csv_text(metric_rows, metric_fields), 'utf-8')`; `cell 13, line 21: atomic_write_text(OUTPUTS['sensitivity'], csv_text(sensitivity_public, sensitivity_fields), 'utf-8')`; `cell 13, line 22: atomic_write_text(OUTPUTS['decisions'], ''.join((json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n' for r in decision_rows)), 'utf-8')`.

## module2_holdout_evaluation - E5 Module2 holdout_evaluation

**Categories:** BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/shroom_rag_e5_module2_holdout_evaluation.ipynb](<../../../RAG/shroom_rag_e5_module2_holdout_evaluation.ipynb>)

**Required inputs:** `Original source pool, Module1 cache, frozen ranking/dense cache and stage-appropriate human annotations`.

**Libraries / specifications:** RAG/requirements-rag-module1.txt; RAG/requirements-rag-module2.txt.

**Models:** `Pinned MPNet for dense-retrieval stage`.

**Working-directory and path contract:** SHROOM_PROJECT_ROOT/RAG ROOT; fixed phase-A/annotation/evaluation/holdout paths.

**Outputs:** `Candidates, embeddings, row annotations/decisions and aggregate metrics`.

**Potential tracked/historical writes:** May write tracked Module2 metrics and reports.

**Network, downloads and cloud:** Some stages load model assets; evaluation imports cannot be assumed write-free.

**Frozen/provenance constraints:** Protected baseline/helper/cache hashes and original split/annotation provenance.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/shroom_rag_e5_module2_holdout_evaluation.ipynb` SHA-256 `14105af14224f177be9e10a895c48fab17e48cc66e9fb53ededc942ea9ed2298`.
  - Observed imports (selection): `from __future__ import annotations`; `import csv, hashlib, io, json, os, pathlib, statistics, tempfile`; `from collections import Counter`.
  - IO/model/network markers (selection): `cell 1, line 6: __import__('os').environ.get('SHROOM_PROJECT_ROOT', '.')`; `cell 8, line 49: json.dumps(ungated, indent=2)`; `cell 8, line 50: json.dumps(gated, indent=2)`; `cell 12, line 38: writer.writeheader()`.

## module3 - Module3 diagnostic/preparation history

**Categories:** STATIC_ONLY. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- No final executable located for this diagnostic/history profile; no command is invented.

**Required inputs:** `Historical annotation/snapshot records described by plans`.

**Libraries / specifications:** No final executable environment is inferred.

**Models:** No model required for the selected description; transitive initialization still needs review..

**Working-directory and path contract:** No located standalone final gated-RAG evaluation entrypoint.

**Outputs:** `No executable output procedure proposed`.

**Potential tracked/historical writes:** Do not recreate planned CSVs under a claimed missing executable workflow.

**Network, downloads and cloud:** New annotation/acquisition requires an actual reviewed implementation and approval.

**Frozen/provenance constraints:** Diagnostic plans/results are history, not commands.

**Missing/public availability:** Row annotation/snapshot payloads absent; no final evaluator located.

**Static evidence (selected observations, not a call-graph proof):**

## module4_prepare-inputs - Module4 lexical builder mode prepare-inputs

**Categories:** BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/scripts/module4_build_external_lexicon.py](<../../../RAG/scripts/module4_build_external_lexicon.py>)

**Required inputs:** `codex/canonical_human_development_manifest.csv`; `codex/canonical_fold_assignments.csv`; `Original raw WordNet/Wiktionary assets for offline build`.

**Libraries / specifications:** beautifulsoup4==4.14.3; requirements-module4-parser.txt; stdlib.

**Models:** No model required for the selected description; transitive initialization still needs review..

**Working-directory and path contract:** Existing CLI declares --canonical-manifest, --output-dir, --mode. Review selected mode independently.

**Outputs:** `Lexical snapshot, term rows, raw responses and logs`.

**Potential tracked/historical writes:** Output-dir must not be a completed/static-protocol artifact tree.

**Network, downloads and cloud:** acquire performs external HTTP/downloads; offline-build uses supplied raw assets. No mode executed.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `codex/canonical_human_development_manifest.csv`: absent; `codex/canonical_fold_assignments.csv`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/scripts/module4_build_external_lexicon.py` SHA-256 `db6d3a8ffe595ca875d349b074041c7679328fc9f50df4499a943d129411021e`.
  - Observed imports (selection): `from __future__ import annotations`; `import argparse`; `import copy`; `import csv`; `import hashlib`; `import html`; `import json`; `import re`.
  - IO/model/network markers (selection): `line 83: path.parent.mkdir(parents=True, exist_ok=True)`; `line 277: raw_dir.mkdir(parents=True, exist_ok=True)`; `line 323: snapshot_path.parent.mkdir(parents=True, exist_ok=True)`; `line 324: snapshot_path.write_text(''.join((json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for r in deduped)), encoding='utf-8')`.

## module4_acquire - Module4 lexical builder mode acquire

**Categories:** STATIC_ONLY; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/scripts/module4_build_external_lexicon.py](<../../../RAG/scripts/module4_build_external_lexicon.py>)

**Required inputs:** `codex/canonical_human_development_manifest.csv`; `codex/canonical_fold_assignments.csv`; `Original raw WordNet/Wiktionary assets for offline build`.

**Libraries / specifications:** beautifulsoup4==4.14.3; requirements-module4-parser.txt; stdlib.

**Models:** No model required for the selected description; transitive initialization still needs review..

**Working-directory and path contract:** Existing CLI declares --canonical-manifest, --output-dir, --mode. Review selected mode independently.

**Outputs:** `Lexical snapshot, term rows, raw responses and logs`.

**Potential tracked/historical writes:** Output-dir must not be a completed/static-protocol artifact tree.

**Network, downloads and cloud:** acquire performs external HTTP/downloads; offline-build uses supplied raw assets. No mode executed.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `codex/canonical_human_development_manifest.csv`: absent; `codex/canonical_fold_assignments.csv`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/scripts/module4_build_external_lexicon.py` SHA-256 `db6d3a8ffe595ca875d349b074041c7679328fc9f50df4499a943d129411021e`.
  - Observed imports (selection): `from __future__ import annotations`; `import argparse`; `import copy`; `import csv`; `import hashlib`; `import html`; `import json`; `import re`.
  - IO/model/network markers (selection): `line 83: path.parent.mkdir(parents=True, exist_ok=True)`; `line 277: raw_dir.mkdir(parents=True, exist_ok=True)`; `line 323: snapshot_path.parent.mkdir(parents=True, exist_ok=True)`; `line 324: snapshot_path.write_text(''.join((json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for r in deduped)), encoding='utf-8')`.

## module4_offline-build - Module4 lexical builder mode offline-build

**Categories:** BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/scripts/module4_build_external_lexicon.py](<../../../RAG/scripts/module4_build_external_lexicon.py>)

**Required inputs:** `codex/canonical_human_development_manifest.csv`; `codex/canonical_fold_assignments.csv`; `Original raw WordNet/Wiktionary assets for offline build`.

**Libraries / specifications:** beautifulsoup4==4.14.3; requirements-module4-parser.txt; stdlib.

**Models:** No model required for the selected description; transitive initialization still needs review..

**Working-directory and path contract:** Existing CLI declares --canonical-manifest, --output-dir, --mode. Review selected mode independently.

**Outputs:** `Lexical snapshot, term rows, raw responses and logs`.

**Potential tracked/historical writes:** Output-dir must not be a completed/static-protocol artifact tree.

**Network, downloads and cloud:** acquire performs external HTTP/downloads; offline-build uses supplied raw assets. No mode executed.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `codex/canonical_human_development_manifest.csv`: absent; `codex/canonical_fold_assignments.csv`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/scripts/module4_build_external_lexicon.py` SHA-256 `db6d3a8ffe595ca875d349b074041c7679328fc9f50df4499a943d129411021e`.
  - Observed imports (selection): `from __future__ import annotations`; `import argparse`; `import copy`; `import csv`; `import hashlib`; `import html`; `import json`; `import re`.
  - IO/model/network markers (selection): `line 83: path.parent.mkdir(parents=True, exist_ok=True)`; `line 277: raw_dir.mkdir(parents=True, exist_ok=True)`; `line 323: snapshot_path.parent.mkdir(parents=True, exist_ok=True)`; `line 324: snapshot_path.write_text(''.join((json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for r in deduped)), encoding='utf-8')`.

## module4_schannel - Module4 Schannel transport acquisition/build

**Categories:** STATIC_ONLY; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/rag_module4/continuation_v1/schannel_run_v1/scripts/module4_schannel_acquire.py](<../../../RAG/results/rag_module4/continuation_v1/schannel_run_v1/scripts/module4_schannel_acquire.py>)

**Required inputs:** `Locked term manifest/raw inputs`.

**Libraries / specifications:** Windows transport and parser source dependencies.

**Models:** No model required for the selected description; transitive initialization still needs review..

**Working-directory and path contract:** Resolve __file__/ROOT/OUT and injected sys.path exactly; changing CWD alone does not relocate fixed paths.

**Outputs:** `raw_sources, snapshot/term manifest and network log`.

**Potential tracked/historical writes:** Even preflight writes a log/output path.

**Network, downloads and cloud:** External transport calls require separate approval.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `Locked term manifest/raw inputs`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/rag_module4/continuation_v1/schannel_run_v1/scripts/module4_schannel_acquire.py` SHA-256 `f44171f65ce18528ce51eef13bbc6285fb273fe139f75e9ede4ab112224fbe89`.
  - Observed imports (selection): `from __future__ import annotations`; `import argparse, hashlib, json, os, subprocess, sys, tempfile, time`; `from datetime import datetime, timezone`; `from email.utils import parsedate_to_datetime`; `from pathlib import Path`; `from typing import Any`; `import module4_build_wiktionary_lexicon as frozen_wiki`.
  - IO/model/network markers (selection): `line 50: self.log_path.parent.mkdir(parents=True, exist_ok=True)`; `line 52: self.log_path.parent.mkdir(parents=True, exist_ok=True)`; `line 53: f.write(json.dumps(event, sort_keys=True) + '\n')`; `line 88: json.dumps(preflight(args.output_dir / 'raw_sources'), sort_keys=True)`.

## module4_fusion - Module4 pinned features and fusion evaluation

**Categories:** BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/rag_module4/continuation_v1/mpnet_provenance_v2/scripts/module4_build_rag_features_pinned.py](<../../../RAG/results/rag_module4/continuation_v1/mpnet_provenance_v2/scripts/module4_build_rag_features_pinned.py>)
- [RAG/results/rag_module4/continuation_v1/schannel_run_v1/scripts/module4_evaluate_fusion.py](<../../../RAG/results/rag_module4/continuation_v1/schannel_run_v1/scripts/module4_evaluate_fusion.py>)

**Required inputs:** `codex/canonical_human_development_manifest.csv`; `codex/canonical_fold_assignments.csv`; `codex/canonical_feature_outputs/canonical_human_14_features.csv`; `codex/canonical_feature_outputs/canonical_synthetic_14_features.csv`; `Original lexical snapshot/ranking/pinned inputs`.

**Libraries / specifications:** Historical numpy/pandas/torch/transformers/sentence-transformers/sklearn context.

**Models:** `Pinned MPNet/NLI assets`.

**Working-directory and path contract:** Resolve __file__/ROOT/OUT and injected sys.path exactly; changing CWD alone does not relocate fixed paths.

**Outputs:** `RAG/fused21 matrices, OOF rows and aggregate outputs`.

**Potential tracked/historical writes:** Fixed completed-run directories include public records.

**Network, downloads and cloud:** Model inference and RF fitting are not approved.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `codex/canonical_human_development_manifest.csv`: absent; `codex/canonical_fold_assignments.csv`: absent; `codex/canonical_feature_outputs/canonical_human_14_features.csv`: absent; `codex/canonical_feature_outputs/canonical_synthetic_14_features.csv`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/rag_module4/continuation_v1/mpnet_provenance_v2/scripts/module4_build_rag_features_pinned.py` SHA-256 `56ff9521c96cfc4d6a8793c86dc60194f4afac16e57aa922e0c9218c72eaf0de`.
  - Observed imports (selection): `from __future__ import annotations`; `import argparse, csv, hashlib, json, math, os, random, re, unicodedata`; `from collections import defaultdict`; `from pathlib import Path`; `from typing import Any, Callable`; `import numpy as np`; `import numpy as np, torch`; `from sentence_transformers import SentenceTransformer`.
  - IO/model/network markers (selection): `line 73: path.parent.mkdir(parents=True, exist_ok=True)`; `line 84: AutoTokenizer.from_pretrained(NLI_ID, revision=NLI_REVISION, local_files_only=True)`; `line 85: AutoModelForSequenceClassification.from_pretrained(NLI_ID, revision=NLI_REVISION, local_files_only=True).to(device).eval()`; `line 100: write_csv(args.output, build(rows, records, embed, nli))`.
- `RAG/results/rag_module4/continuation_v1/schannel_run_v1/scripts/module4_evaluate_fusion.py` SHA-256 `ef127e98c8a71b64abec6986cb6baf852b9521ff480142517ef0bc00e40b919e`.
  - Observed imports (selection): `from __future__ import annotations`; `import argparse, hashlib, json`; `from pathlib import Path`; `import numpy as np`; `import pandas as pd`; `from scipy.stats import spearmanr`; `from sklearn.ensemble import RandomForestRegressor`; `from sklearn.metrics import accuracy_score`.
  - IO/model/network markers (selection): `line 56: args.output_dir.mkdir(parents=True, exist_ok=True)`; `line 57: fused.parent.mkdir(parents=True, exist_ok=True)`; `line 58: frame[['canonical_id'] + E3 + RAG].to_csv(fused, index=False, encoding='utf-8-sig', lineterminator='\n')`; `line 60: e3_pred.to_csv(e3_out, index=False, encoding='utf-8-sig', lineterminator='\n')`.

## module4_source_verify - Source-only Module4 verifier candidate

**Categories:** CANDIDATE_FOR_FUTURE_TEST; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/module4_release_v1/verify_module4.py](<../../../RAG/module4_release_v1/verify_module4.py>)

**Required inputs:** `RELEASE_MANIFEST.json and selected public sources`.

**Libraries / specifications:** stdlib.

**Models:** No model required for the selected description; transitive initialization still needs review..

**Working-directory and path contract:** Verifier declares explicit --repo-root/--manifest/--mode; source versus local-artifacts is significant.

**Outputs:** `stdout/JSON captured outside repository`.

**Potential tracked/historical writes:** Only reviewed source mode is a future candidate; no write-free assumption from filename.

**Network, downloads and cloud:** No network/model in reviewed source-only mode; no runtime test now.

**Frozen/provenance constraints:** Historical SHA validation may return FAIL; never edit expected values to force PASS.

**Missing/public availability:** Local-artifacts mode needs omitted assets; source-mode runtime result unknown.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/module4_release_v1/verify_module4.py` SHA-256 `74676563cace86438c4487f2135bb65fb234307e2ff894341d50e38e7b26d638`.
  - Observed imports (selection): `from __future__ import annotations`; `import argparse`; `import hashlib`; `import json`; `import os`; `import re`; `import sys`; `from pathlib import Path, PurePosixPath, PureWindowsPath`.
  - IO/model/network markers (selection): `line 286: json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)`; `line 279: json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)`.

## e6_v1 - E6-v1 preparation/features/evaluation/report stages

**Categories:** BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/rag_e6_v1/scripts/preflight.py](<../../../RAG/results/rag_e6_v1/scripts/preflight.py>)
- [RAG/results/rag_e6_v1/scripts/prepare_run.py](<../../../RAG/results/rag_e6_v1/scripts/prepare_run.py>)
- [RAG/results/rag_e6_v1/scripts/build_features.py](<../../../RAG/results/rag_e6_v1/scripts/build_features.py>)
- [RAG/results/rag_e6_v1/scripts/evaluate_e6.py](<../../../RAG/results/rag_e6_v1/scripts/evaluate_e6.py>)
- [RAG/results/rag_e6_v1/scripts/report_e6.py](<../../../RAG/results/rag_e6_v1/scripts/report_e6.py>)

**Required inputs:** `codex/canonical_human_development_manifest.csv`; `codex/canonical_fold_assignments.csv`; `codex/canonical_feature_outputs/canonical_human_14_features.csv`; `codex/canonical_feature_outputs/canonical_synthetic_14_features.csv`; `Module4 artifacts and preceding-version matrices/OOF as applicable`.

**Libraries / specifications:** Per-version config/run_config.json runtime and observed imports.

**Models:** `Module4 MPNet/NLI`.

**Working-directory and path contract:** Resolve __file__/ROOT/OUT and injected sys.path exactly; changing CWD alone does not relocate fixed paths. e6_common imports pinned Module4 sources at module scope.

**Outputs:** `Feature/ranking/OOF files, config logs/markers and result reports`.

**Potential tracked/historical writes:** Even preflight/report stages can write tracked records; inspect the chosen stage separately.

**Network, downloads and cloud:** Local assets required for inference; acquisition is a different prohibited workflow; no RF fits approved.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `codex/canonical_human_development_manifest.csv`: absent; `codex/canonical_fold_assignments.csv`: absent; `codex/canonical_feature_outputs/canonical_human_14_features.csv`: absent; `codex/canonical_feature_outputs/canonical_synthetic_14_features.csv`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/rag_e6_v1/scripts/preflight.py` SHA-256 `9a3479d8ba599bcced56a405fa1eb9155f4bcd9e64eaee5fd971a7d6a6f00466`.
  - Observed imports (selection): `from pathlib import Path`; `import hashlib`; `import importlib.util`; `import json`; `from datetime import datetime, timezone`; `import pandas as pd`.
  - IO/model/network markers (selection): `line 18: importlib.util.spec_from_file_location('release_verifier', ROOT / 'RAG/module4_release_v1/verify_module4.py')`; `line 73: dest.parent.mkdir(parents=True, exist_ok=True)`; `line 76: dest.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')`; `line 77: json.dumps({k: result[k] for k in ['status', 'rows', 'fold_sizes', 'evidence_rows', 'saved_baseline_metrics']})`.
- `RAG/results/rag_e6_v1/scripts/prepare_run.py` SHA-256 `d0e41c979b59927e13cbd223c9d19f041f63dd6f9f2ecb5afdf7cd58be0a5410`.
  - Observed imports (selection): `import importlib.metadata`; `import sys`; `from e6_common import *`; `from sklearn.ensemble import RandomForestRegressor`.
  - IO/model/network markers (selection): `line 46: write_json(OUT / 'config/run_config.json', result)`; `line 47: json.dumps({'status': 'CONFIG_LOCKED', 'protected_files': len(protected), 'packages': packages})`.
- `RAG/results/rag_e6_v1/scripts/build_features.py` SHA-256 `fc0dd1677c81d7ed5a4b810cb45056720dd52e53d7f0c712f8a37465ca4fcde5`.
  - Observed imports (selection): `import json`; `import time`; `import unicodedata`; `from collections import defaultdict`; `import numpy as np`; `import pandas as pd`; `from e6_common import *`.
  - IO/model/network markers (selection): `line 76: ranking_path.parent.mkdir(parents=True, exist_ok=True)`; `line 80: csv_write(OUT / 'ranking/reconstructed_aggregates.csv', derived)`; `line 92: write_json(OUT / 'config/ranking_consistency.json', ranking_check)`; `line 124: csv_write(OUT / 'features/e6_added_4_features.csv', extra)`.
- `RAG/results/rag_e6_v1/scripts/evaluate_e6.py` SHA-256 `fe55448b3917b0a68f02e8a62b7f5ad93ffd72b752215f8d82275f2309a23387`.
  - Observed imports (selection): `import numpy as np`; `import pandas as pd`; `from scipy.stats import binomtest`; `from sklearn.ensemble import RandomForestRegressor`; `from e6_common import *`.
  - IO/model/network markers (selection): `line 86: write_json(OUT / 'evaluation/baseline_compatibility.json', {'status': 'PASS', 'checked_utc': now(), 'metrics': baseline_metrics, 'ids_and_folds': '561 one-to-one matches `; `line 92: write_json(OUT / 'evaluation/evaluation_started.json', {'started_utc': now(), 'config_sha256': sha(OUT / 'config/run_config.json'), 'feature_freeze_sha256': sha(OUT / 'co`; `line 101: csv_write(OUT / 'evaluation/e6_oof_predictions.csv', pred)`; `line 119: csv_write(OUT / 'evaluation/paired_row_diagnostics.csv', frame[['canonical_id', 'fold_id', 'task', 'rag_evidence_available', 'label_bin', 'p_hallucination', 'E3', 'E5', '`.
- `RAG/results/rag_e6_v1/scripts/report_e6.py` SHA-256 `5dae61cb4cf823e45be00d9ef7eccf13a3291061833771eaaaa3eb90c8943dcd`.
  - Observed imports (selection): `from e6_common import *`.
  - IO/model/network markers (selection): `line 127: (OUT / 'E6_RESULTS.md').write_text('\n'.join(lines), encoding='utf-8')`; `line 128: write_json(OUT / 'config/completion_manifest.json', {'status': 'COMPLETED', 'verified_utc': now(), 'protected_files_unchanged': len(lock['protected_sha256']), 'network_at`; `line 134: json.dumps({'report': str(OUT / 'E6_RESULTS.md'), 'status': 'COMPLETED'})`.

## e6_v2 - E6-v2 preparation/features/evaluation/report stages

**Categories:** BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/rag_e6_v2/scripts/prepare_inputs.py](<../../../RAG/results/rag_e6_v2/scripts/prepare_inputs.py>)
- [RAG/results/rag_e6_v2/scripts/extract_features.py](<../../../RAG/results/rag_e6_v2/scripts/extract_features.py>)
- [RAG/results/rag_e6_v2/scripts/evaluate_v2.py](<../../../RAG/results/rag_e6_v2/scripts/evaluate_v2.py>)
- [RAG/results/rag_e6_v2/scripts/report_v2.py](<../../../RAG/results/rag_e6_v2/scripts/report_v2.py>)

**Required inputs:** `codex/canonical_human_development_manifest.csv`; `codex/canonical_fold_assignments.csv`; `codex/canonical_feature_outputs/canonical_human_14_features.csv`; `codex/canonical_feature_outputs/canonical_synthetic_14_features.csv`; `Module4 artifacts and preceding-version matrices/OOF as applicable`.

**Libraries / specifications:** Per-version config/run_config.json runtime and observed imports.

**Models:** `MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli@b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7`.

**Working-directory and path contract:** Resolve __file__/ROOT/OUT and injected sys.path exactly; changing CWD alone does not relocate fixed paths. e6_common imports pinned Module4 sources at module scope.

**Outputs:** `Feature/ranking/OOF files, config logs/markers and result reports`.

**Potential tracked/historical writes:** Even preflight/report stages can write tracked records; inspect the chosen stage separately.

**Network, downloads and cloud:** Local assets required for inference; acquisition is a different prohibited workflow; no RF fits approved.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `codex/canonical_human_development_manifest.csv`: absent; `codex/canonical_fold_assignments.csv`: absent; `codex/canonical_feature_outputs/canonical_human_14_features.csv`: absent; `codex/canonical_feature_outputs/canonical_synthetic_14_features.csv`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/rag_e6_v2/scripts/prepare_inputs.py` SHA-256 `84dc730aba9fef8946c78064080c2ddcf75622744504f1aa4338783069cf4b4a`.
  - Observed imports (selection): `import json`; `import numpy as np`; `import pandas as pd`; `import v2_common as c`.
  - IO/model/network markers (selection): `line 57: c.write_json(c.OUT / 'config/input_manifest.json', {'created_utc': c.now(), 'protected_sha256': protected, 'mode': 'hash verification only; no evaluation labels projected`; `line 79: saved.set_index('canonical_id').loc[ids].reset_index()`; `line 85: c.write_json(c.OUT / 'inputs/nli_pairs_label_free.json', pairs)`; `line 86: c.write_json(c.OUT / 'inputs/definition_reference_mapping.json', mapping)`.
- `RAG/results/rag_e6_v2/scripts/extract_features.py` SHA-256 `ccd7fa76546566be41f83cfa668a1c13a1572c6a6ac251161757753c3aeed093`.
  - Observed imports (selection): `import time`; `import numpy as np`; `import pandas as pd`; `import v2_common as c`; `from nli_backend import load_backend, infer_batch`; `import torch`.
  - IO/model/network markers (selection): `line 49: chunk_dir.mkdir(parents=True, exist_ok=True)`; `line 67: c.csv_write(c.OUT / 'features/nli2_pair_scores.csv', pd.DataFrame(all_scores))`; `line 68: c.csv_write(c.OUT / 'features/truncation_audit.csv', pd.DataFrame(all_audits))`; `line 69: c.csv_write(c.OUT / 'features/e6_v2_added_9_features.csv', new)`.
- `RAG/results/rag_e6_v2/scripts/evaluate_v2.py` SHA-256 `d9215c5b88c918a84b5f73381ead9b781558023e58603f6f3bd71595c4ffa237`.
  - Observed imports (selection): `import numpy as np`; `import pandas as pd`; `from scipy.stats import spearmanr, binomtest`; `from sklearn.ensemble import RandomForestRegressor`; `import v2_common as c`.
  - IO/model/network markers (selection): `line 61: saved.set_index('canonical_id').loc[ids].reset_index()`; `line 63: saved.prediction.to_numpy()`; `line 82: c.write_json(c.OUT / 'evaluation/baseline_verification.json', check)`; `line 83: c.write_json(c.OUT / 'evaluation/evaluation_started.json', {'started_utc': c.now(), 'expected_rf_fits': 5, 'baseline_fits': 0, 'configuration_count': 1, 'run_config_sha25`.
- `RAG/results/rag_e6_v2/scripts/report_v2.py` SHA-256 `4fb76da98a5e7e1210738ab8f481b38e7395faad62ed2ee525ec4b424541af6f`.
  - Observed imports (selection): `import json`; `import numpy as np`; `import pandas as pd`; `import v2_common as c`; `from evaluate_v2 import load_evaluation, metric, paired`; `from extract_features import assemble`.
  - IO/model/network markers (selection): `line 64: c.write_json(c.OUT / 'config/final_integrity.json', audit)`; `line 67: c.write_json(c.OUT / 'config/completion_manifest.json', {'status': 'COMPLETED', 'completed_utc': c.now(), 'evaluations': 1, 'rf_fits': 5, 'files': {p.relative_to(c.OUT).a`; `line 66: out.write(render(result, freeze, lock, audit, baseline))`.

## e6_v3 - E6-v3 preparation/features/evaluation/report stages

**Categories:** BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/rag_e6_v3/scripts/prepare_inputs.py](<../../../RAG/results/rag_e6_v3/scripts/prepare_inputs.py>)
- [RAG/results/rag_e6_v3/scripts/extract_features.py](<../../../RAG/results/rag_e6_v3/scripts/extract_features.py>)
- [RAG/results/rag_e6_v3/scripts/evaluate_v3.py](<../../../RAG/results/rag_e6_v3/scripts/evaluate_v3.py>)
- [RAG/results/rag_e6_v3/scripts/report_v3.py](<../../../RAG/results/rag_e6_v3/scripts/report_v3.py>)

**Required inputs:** `codex/canonical_human_development_manifest.csv`; `codex/canonical_fold_assignments.csv`; `codex/canonical_feature_outputs/canonical_human_14_features.csv`; `codex/canonical_feature_outputs/canonical_synthetic_14_features.csv`; `Module4 artifacts and preceding-version matrices/OOF as applicable`.

**Libraries / specifications:** Per-version config/run_config.json runtime and observed imports.

**Models:** `vectara/hallucination_evaluation_model@58383384656cbaec2949a75a41f20e891e90a73b`.

**Working-directory and path contract:** Resolve __file__/ROOT/OUT and injected sys.path exactly; changing CWD alone does not relocate fixed paths. e6_common imports pinned Module4 sources at module scope.

**Outputs:** `Feature/ranking/OOF files, config logs/markers and result reports`.

**Potential tracked/historical writes:** Even preflight/report stages can write tracked records; inspect the chosen stage separately.

**Network, downloads and cloud:** Local assets required for inference; acquisition is a different prohibited workflow; no RF fits approved.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `codex/canonical_human_development_manifest.csv`: absent; `codex/canonical_fold_assignments.csv`: absent; `codex/canonical_feature_outputs/canonical_human_14_features.csv`: absent; `codex/canonical_feature_outputs/canonical_synthetic_14_features.csv`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/rag_e6_v3/scripts/prepare_inputs.py` SHA-256 `88cebd8e3f14d33f1a111e2fc3c954a3d162dd11541f5d6bbc90012ceb29e0b7`.
  - Observed imports (selection): `import shutil`; `import numpy as np`; `import pandas as pd`; `import v3_common as c`.
  - IO/model/network markers (selection): `line 29: c.write_json(c.OUT / 'config/input_manifest.json', {'created_utc': c.now(), 'protected_sha256': protected, 'baseline': 'E6-v2', 'mode': 'hash only; no label projection'})`; `line 61: c.write_json(c.OUT / 'inputs/hhem_pairs_label_free.json', pairs)`; `line 62: c.write_json(c.OUT / 'config/input_checks.json', {'status': 'PASS', 'rows': 561, 'original_features': columns, 'new_features': c.NEW, 'total_features': 36, 'pairs': {'A':`.
- `RAG/results/rag_e6_v3/scripts/extract_features.py` SHA-256 `d8dc674a9314a15ecfe4219d47caa00177bf3bf73d9e6960d889090e2d4f27d4`.
  - Observed imports (selection): `import json, time, os, uuid`; `import numpy as np`; `import pandas as pd`; `from scipy.special import expit`; `import v3_common as c`; `from hhem_backend import load_backend, infer_batch`; `import torch`.
  - IO/model/network markers (selection): `line 9: c.hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()`; `line 78: c.write_json(c.OUT / f'config/extraction_sessions/{session}_started.json', {'utc': start, 'pid': os.getpid()})`; `line 81: chunks.mkdir(parents=True, exist_ok=True)`; `line 108: c.write_json(c.OUT / f'config/extraction_sessions/{session}_completed.json', {'started_utc': start, 'completed_utc': c.now(), 'duration_seconds': seconds, 'inferred': inf`.
- `RAG/results/rag_e6_v3/scripts/evaluate_v3.py` SHA-256 `fd6a041ac07201f702a0927628d01e58060ed4e5ed3d1ab5cc0b9d468a251893`.
  - Observed imports (selection): `import numpy as np`; `import pandas as pd`; `from scipy.stats import spearmanr, binomtest`; `from sklearn.ensemble import RandomForestRegressor`; `import v3_common as c`.
  - IO/model/network markers (selection): `line 61: saved.set_index('canonical_id').loc[ids].reset_index()`; `line 63: saved.prediction.to_numpy()`; `line 81: c.write_json(c.OUT / 'evaluation/baseline_verification.json', check)`; `line 82: c.write_json(c.OUT / 'evaluation/evaluation_started.json', {'started_utc': c.now(), 'expected_rf_fits': 5, 'baseline_fits': 0, 'configuration_count': 1, 'run_config_sha25`.
- `RAG/results/rag_e6_v3/scripts/report_v3.py` SHA-256 `efb1e0498e92250049b55c3cb1c1eb2f2030e623742c1b7bb167e12fe9fc5756`.
  - Observed imports (selection): `import json`; `import numpy as np`; `import pandas as pd`; `import v3_common as c`; `from evaluate_v3 import load_evaluation, metric, paired`; `from extract_features import assemble, validate_cache`.
  - IO/model/network markers (selection): `line 79: c.write_json(c.OUT / 'config/final_integrity.json', audit)`; `line 81: c.write_json(c.OUT / 'config/completion_manifest.json', {'status': 'COMPLETED', 'completed_utc': c.now(), 'evaluations': 1, 'rf_fits': 5, 'files': {p.relative_to(c.OUT).a`; `line 80: out.write(render(result, freeze, lock, audit))`; `line 157: json.dumps(lock['random_forest'], indent=2, sort_keys=True)`.

## e6_acquisition - E6 acquisition/bootstrap utilities

**Categories:** STATIC_ONLY; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/rag_e6_v2/scripts/acquire_model.py](<../../../RAG/results/rag_e6_v2/scripts/acquire_model.py>)
- [RAG/results/rag_e6_v3/scripts/bootstrap_sources.py](<../../../RAG/results/rag_e6_v3/scripts/bootstrap_sources.py>)
- [RAG/results/rag_e6_v3/scripts/record_acquisition.py](<../../../RAG/results/rag_e6_v3/scripts/record_acquisition.py>)

**Required inputs:** `Pinned upstream identities/acquisition prerequisites`.

**Libraries / specifications:** Source-specific hub/package imports.

**Models:** `Pinned NLI2/HHEM`.

**Working-directory and path contract:** Resolve __file__/ROOT/OUT and injected sys.path exactly; changing CWD alone does not relocate fixed paths.

**Outputs:** `Model/source trees and acquisition records`.

**Potential tracked/historical writes:** Writes model/provenance paths, including tracked metadata.

**Network, downloads and cloud:** Downloading/bootstrap/install behavior is not approved.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `Pinned upstream identities/acquisition prerequisites`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/rag_e6_v2/scripts/acquire_model.py` SHA-256 `59decab039965c7b75ccb381547a45cf0258eb16dbfeb198e61d433108df0ac3`.
  - Observed imports (selection): `from pathlib import Path`; `from datetime import datetime, timezone`; `import hashlib, json, subprocess, time`.
  - IO/model/network markers (selection): `line 42: json.dump(result, f, indent=2)`; `line 42: f.write('\n')`; `line 36: json.dumps({'file': name, 'bytes': dest.stat().st_size, 'sha256': results[name]['sha256']})`.
- `RAG/results/rag_e6_v3/scripts/bootstrap_sources.py` SHA-256 `e7f095b03706b050cf138e592468ac630e85d21f020d41a3314613151cc741f5`.
  - Observed imports (selection): `from pathlib import Path`.
  - IO/model/network markers (selection): `line 17: save('v3_common.py', common)`; `line 20: save('smoke_hhem.py', smoke)`; `line 44: save('hhem_backend.py', backend)`; `line 60: save('evaluate_v3.py', evaluation)`.
- `RAG/results/rag_e6_v3/scripts/record_acquisition.py` SHA-256 `958e2c61e04d6983d9fcfacb74e8fbcaf81d1e5ed54fa799359c49bc1554f7e1`.
  - Observed imports (selection): `import v3_common as c`; `import re`.
  - IO/model/network markers (selection): `line 20: c.write_json(c.OUT / 'provenance/acquisition.json', {'created_utc': c.now(), 'model_id': c.MODEL_ID, 'revision': c.REVISION, 'historical_name': 'hhem-1.0-open', 'files': `.

## e6_v4_initial - Initial E6-v4 compatibility diagnostic

**Categories:** STATIC_ONLY; BLOCKED_PROVENANCE; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/rag_e6_v4/compatibility_analysis/reproduce_minimal.py](<../../../RAG/results/rag_e6_v4/compatibility_analysis/reproduce_minimal.py>)
- [RAG/results/rag_e6_v4/scripts/check_compatibility.py](<../../../RAG/results/rag_e6_v4/scripts/check_compatibility.py>)

**Required inputs:** `Historical compatibility assets and original diagnostics`.

**Libraries / specifications:** Compatibility records, not current/latest packages.

**Models:** `Pinned DeBERTa MNLI from v4 source`.

**Working-directory and path contract:** Resolve __file__/ROOT/OUT and injected sys.path exactly; changing CWD alone does not relocate fixed paths.

**Outputs:** `Diagnostic source/JSON artifacts`.

**Potential tracked/historical writes:** May recreate diagnostic public-safe derivatives/source dumps.

**Network, downloads and cloud:** Model/package execution possible; do not install a fix or rerun original blocker implicitly.

**Frozen/provenance constraints:** Initial blocked stage and amended completed run remain distinct.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/rag_e6_v4/compatibility_analysis/reproduce_minimal.py` SHA-256 `f298eaeb2f075fcd4cb0b091b4ec3d2a10afd2f51d87b6882387586becec0020`.
  - Observed imports (selection): `import os, sys, json, traceback, inspect, hashlib, socket, importlib.metadata`; `from pathlib import Path`; `import transformers, tokenizers, torch, bert_score`; `from bert_score.utils import get_tokenizer, sent_encode`.
  - IO/model/network markers (selection): `line 57: json.dump(result, f, indent=2, ensure_ascii=False)`; `line 58: json.dumps({k: v for k, v in result.items() if k not in ['sources', 'traceback']}, indent=2)`.
- `RAG/results/rag_e6_v4/scripts/check_compatibility.py` SHA-256 `723732b636a5631ad2382b026d9486b4b1fb92e8a654d5cd401a90aa0343f489`.
  - Observed imports (selection): `from pathlib import Path`; `import sys, os, json, hashlib, traceback, time, socket, base64, csv, importlib.metadata`; `import bert_score, torch, transformers`; `from bert_score.utils import model2layers, get_hash, greedy_cos_idf, sent_encode`.
  - IO/model/network markers (selection): `line 85: write('provenance/compatibility.json', result)`; `line 16: json.dump(v, f, indent=2, ensure_ascii=False, allow_nan=False)`; `line 86: json.dumps({k: v for k, v in result.items() if k not in ['model_files', 'smoke']}, ensure_ascii=False, indent=2)`.

## e6_v4_amended - Amended E6-v4 encoding/evaluation

**Categories:** BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/rag_e6_v4/execution/extract.py](<../../../RAG/results/rag_e6_v4/execution/extract.py>)
- [RAG/results/rag_e6_v4/execution/evaluate.py](<../../../RAG/results/rag_e6_v4/execution/evaluate.py>)
- [RAG/results/rag_e6_v4/execution/freeze.py](<../../../RAG/results/rag_e6_v4/execution/freeze.py>)
- [RAG/results/rag_e6_v4/execution/report.py](<../../../RAG/results/rag_e6_v4/execution/report.py>)

**Required inputs:** `codex/canonical_human_development_manifest.csv`; `codex/canonical_fold_assignments.csv`; `E6-v3 matrix/OOF, original compatibility/model/freeze inputs`.

**Libraries / specifications:** Encoding pins: transformers4.30.2,tokenizers 0.13.3,huggingface-hub 0.25.2,bert-score0.3.13; RF uses its separately recorded runtime.

**Models:** `microsoft/deberta-large-mnli@7296194b9009373def4f7c5dad292651e4b5cf4e`.

**Working-directory and path contract:** Resolve __file__/ROOT/OUT and injected sys.path exactly; changing CWD alone does not relocate fixed paths. offline() replaces TEMP/TMP/HF_MODULES_CACHE/JOBLIB/MPL paths with execution/tmp; initial env redirection can be undone.

**Outputs:** `Encoding chunks/matrix, markers/network logs and result records`.

**Potential tracked/historical writes:** Both execution and experiment-root outputs include tracked files.

**Network, downloads and cloud:** Offline helper writes first; BERTScore construction still executes model code. No current encoding/RF execution.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `codex/canonical_human_development_manifest.csv`: absent; `codex/canonical_fold_assignments.csv`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/rag_e6_v4/execution/extract.py` SHA-256 `9e48874a05e4d76725b5396b31db5a3e688ab73788cb8a24032e6ebdc37245d3`.
  - Observed imports (selection): `import common as c`; `import time, traceback`; `import numpy as np, pandas as pd, torch`; `import structure`; `from bert_score.utils import sent_encode`.
  - IO/model/network markers (selection): `line 18: c.write(c.HERE / 'extraction_started.json', {'started_utc': c.now(), 'planned_rows': 561, 'freeze_sha256': c.sha(c.HERE / 'run_config.json')})`; `line 49: c.csvwrite(c.V4 / 'features/e6_v4_new_7_features.csv', features)`; `line 50: c.csvwrite(c.V4 / 'features/e6_v4_43_features.csv', combined)`; `line 51: c.csvwrite(c.V4 / 'features/truncation_audit.csv', pd.DataFrame(trunc))`.
- `RAG/results/rag_e6_v4/execution/evaluate.py` SHA-256 `bffae5ea5824ec781847ff35ead19f015a871b9f5664f619c0d39d5022ead303`.
  - Observed imports (selection): `import common as c`; `import time, traceback`; `import numpy as np, pandas as pd`; `from scipy.stats import spearmanr, binomtest`; `from sklearn.ensemble import RandomForestRegressor`.
  - IO/model/network markers (selection): `line 54: c.write(c.HERE / 'baseline_verification_final.json', {'status': 'PASS', 'metrics': expected, 'IDs_folds_labels_predictions_exact': True, 'baseline_fits': 0})`; `line 55: c.write(c.HERE / 'evaluation_started.json', {'started_utc': c.now(), 'planned_fits': 5, 'configuration_count': 1, 'feature_freeze_sha256': c.sha(c.HERE / 'feature_freeze.`; `line 75: c.csvwrite(c.V4 / 'evaluation/e6_v4_oof_predictions.csv', pd.DataFrame({'canonical_id': ids, 'fold_id': frame.fold_id, 'prediction': pred}))`; `line 76: c.csvwrite(c.V4 / 'evaluation/paired_row_diagnostics.csv', frame)`.
- `RAG/results/rag_e6_v4/execution/freeze.py` SHA-256 `fea85a2adda13f284fed9fc3996a7cfc3d71d636ae2c4ff3ab21ddf51a9e29b3`.
  - Observed imports (selection): `import common as c`; `import ast`; `import structure`.
  - IO/model/network markers (selection): `line 31: c.write(c.HERE / 'canonical_ids.json', ids)`; `line 47: c.write(c.HERE / 'run_config.json', config)`.
- `RAG/results/rag_e6_v4/execution/report.py` SHA-256 `e2e0a561094fea3102ddfb9f1708a234475a821ea679d9a711cca2336fd9a5af`.
  - Observed imports (selection): `import common as c`; `import subprocess`; `import numpy as np, pandas as pd`; `from evaluate import metric, paired`.
  - IO/model/network markers (selection): `line 37: c.write(c.HERE / 'final_integrity.json', audit)`; `line 134: (c.V4 / 'E6_V4_RESULTS.md').write_text(text, encoding='utf-8')`; `line 142: c.write(c.HERE / 'completion_manifest.json', {'status': 'COMPLETED', 'created_utc': c.now(), 'files': files, 'excluded': ['execution/tmp', 'self manifest'], 'RF_fits': 5,`.

## e7 - E7 preparation/evaluation/report chain

**Categories:** BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/rag_e7_agentic_v1/scripts/preflight.py](<../../../RAG/results/rag_e7_agentic_v1/scripts/preflight.py>)
- [RAG/results/rag_e7_agentic_v1/scripts/prepare_evaluation.py](<../../../RAG/results/rag_e7_agentic_v1/scripts/prepare_evaluation.py>)
- [RAG/results/rag_e7_agentic_v1/scripts/evaluate_e7.py](<../../../RAG/results/rag_e7_agentic_v1/scripts/evaluate_e7.py>)
- [RAG/results/rag_e7_agentic_v1/scripts/report_e7.py](<../../../RAG/results/rag_e7_agentic_v1/scripts/report_e7.py>)

**Required inputs:** `codex/canonical_human_development_manifest.csv`; `codex/canonical_fold_assignments.csv`; `codex/canonical_feature_outputs/canonical_human_14_features.csv`; `codex/canonical_feature_outputs/canonical_synthetic_14_features.csv`; `E6-v1 matrix/ranking and Module4 artifacts`.

**Libraries / specifications:** Original per-run Python/package pins.

**Models:** No model required for the selected description; transitive initialization still needs review..

**Working-directory and path contract:** Resolve __file__/ROOT/OUT and injected sys.path exactly; changing CWD alone does not relocate fixed paths. AccessGuard permits fixed OUT and original read allowlists; changing constants changes frozen source.

**Outputs:** `Routing/nested-CV/OOF/fit markers, diagnostics and reports in fixed OUT`.

**Potential tracked/historical writes:** Guard construction/preparation can write repository diagnostics.

**Network, downloads and cloud:** RF fitting remains training, even with no new feature inference or network.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `codex/canonical_human_development_manifest.csv`: absent; `codex/canonical_fold_assignments.csv`: absent; `codex/canonical_feature_outputs/canonical_human_14_features.csv`: absent; `codex/canonical_feature_outputs/canonical_synthetic_14_features.csv`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/rag_e7_agentic_v1/scripts/preflight.py` SHA-256 `915cd943284c7d2eb4ba4391e6dc605917a7535f5659bdee6de5ac69382cc525`.
  - Observed imports (selection): `from e7_common import *`.
  - IO/model/network markers (selection): `line 9: write_json(OUT / 'config/preflight.json', result)`; `line 12: guard.save()`.
- `RAG/results/rag_e7_agentic_v1/scripts/prepare_evaluation.py` SHA-256 `f15fbbc7e7721be337d981fe2748f05e145abdd1ad8097d3e3b0c34a16df2c0c`.
  - Observed imports (selection): `from e7_common import *`; `import numpy as np`; `from router import plan_routes, USE, FALLBACK, OBSERVATIONS`; `import e7_common`.
  - IO/model/network markers (selection): `line 27: csv_write(OUT / 'routing/router_inputs.csv', signals)`; `line 28: csv_write(OUT / 'routing/routes.csv', routes)`; `line 29: write_json(OUT / 'config/fold_thresholds.json', thresholds)`; `line 31: write_json(OUT / 'config/routes_freeze.json', {'frozen_utc': now(), 'rows': 561, 'router_inputs': list(OBSERVATIONS), 'labels_loaded': False, 'saved_predictions_loaded': `.
- `RAG/results/rag_e7_agentic_v1/scripts/evaluate_e7.py` SHA-256 `d3eef103e38d2d30a1fda18eb751d76e52d0fdb032cb95479b392524968619a0`.
  - Observed imports (selection): `from e7_common import *`; `import numpy as np`; `import pandas as pd`; `from scipy.stats import rankdata`; `from sklearn.ensemble import RandomForestRegressor`; `from router import USE, FALLBACK, choose_route, finish_prediction, OBSERVATIONS`; `from evaluation_common import verify_evaluation_freeze, audited_cv, metric, paired`; `import e7_common`.
  - IO/model/network markers (selection): `line 60: write_json(OUT / 'evaluation/baseline_verification.json', {'checked_utc': now(), 'status': 'PASS', 'metrics': baseline_metrics, 'routes_frozen_before_label_projection': T`; `line 66: write_json(started, {'started_utc': now(), 'expected_evaluation_count': 1, 'expected_outer_folds': 5, 'expected_rf_fits': 10, 'evaluation_freeze_sha256': sha(OUT / 'confi`; `line 95: csv_write(OUT / 'evaluation/e7_oof_predictions.csv', frame[['canonical_id', 'fold_id', 'route', 'E7']].rename(columns={'E7': 'prediction'}))`; `line 96: write_json(OUT / 'evaluation/agent_trajectories.json', trajectories)`.
- `RAG/results/rag_e7_agentic_v1/scripts/report_e7.py` SHA-256 `cb24d46a4f746d932aeac6b6f617728abfa9f527f85142db166c79a32f5aa8da`.
  - Observed imports (selection): `from e7_common import *`; `import numpy as np`; `import pandas as pd`; `from router import USE, FALLBACK, OBSERVATIONS, plan_routes, finish_prediction`; `from evaluation_common import verify_evaluation_freeze, metric, paired`; `import e7_common`; `from evaluation_common import verify_evaluation_freeze`.
  - IO/model/network markers (selection): `line 90: write_json(OUT / 'evaluation/routing_ceiling_analysis.json', ceiling)`; `line 103: write_json(OUT / 'config/final_integrity_audit.json', audit)`; `line 177: target.write_text('\n\n'.join(report) + '\n', encoding='utf-8', newline='\n')`; `line 193: write_json(OUT / 'config/completion_manifest.json', {'status': 'COMPLETED', 'verified_utc': now(), 'files': files, 'self_excluded': True, 'e7_evaluations': 1, 'rf_fits': `.

## e8 - E8 preparation/evaluation/report chain

**Categories:** BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/rag_e8_rf_tuning_v1/scripts/prepare_e8.py](<../../../RAG/results/rag_e8_rf_tuning_v1/scripts/prepare_e8.py>)
- [RAG/results/rag_e8_rf_tuning_v1/scripts/evaluate_e8.py](<../../../RAG/results/rag_e8_rf_tuning_v1/scripts/evaluate_e8.py>)
- [RAG/results/rag_e8_rf_tuning_v1/scripts/nested_rf.py](<../../../RAG/results/rag_e8_rf_tuning_v1/scripts/nested_rf.py>)
- [RAG/results/rag_e8_rf_tuning_v1/scripts/report_e8_render_fixed.py](<../../../RAG/results/rag_e8_rf_tuning_v1/scripts/report_e8_render_fixed.py>)

**Required inputs:** `codex/canonical_human_development_manifest.csv`; `codex/canonical_fold_assignments.csv`; `codex/canonical_feature_outputs/canonical_human_14_features.csv`; `codex/canonical_feature_outputs/canonical_synthetic_14_features.csv`; `E6-v1 matrix/ranking and Module4 artifacts`.

**Libraries / specifications:** Original per-run Python/package pins.

**Models:** No model required for the selected description; transitive initialization still needs review..

**Working-directory and path contract:** Resolve __file__/ROOT/OUT and injected sys.path exactly; changing CWD alone does not relocate fixed paths. AccessGuard permits fixed OUT and original read allowlists; changing constants changes frozen source.

**Outputs:** `Routing/nested-CV/OOF/fit markers, diagnostics and reports in fixed OUT`.

**Potential tracked/historical writes:** Guard construction/preparation can write repository diagnostics.

**Network, downloads and cloud:** RF fitting remains training, even with no new feature inference or network.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `codex/canonical_human_development_manifest.csv`: absent; `codex/canonical_fold_assignments.csv`: absent; `codex/canonical_feature_outputs/canonical_human_14_features.csv`: absent; `codex/canonical_feature_outputs/canonical_synthetic_14_features.csv`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/rag_e8_rf_tuning_v1/scripts/prepare_e8.py` SHA-256 `0b99a30c9243d2a2f64e54e0741dff2438c7284010a92c66a84a1701b74400c2`.
  - Observed imports (selection): `import sys`; `import unittest`; `import io`; `import e8_common as c`; `from e8_data import runtime, load_data, baseline`; `from nested_rf import configurations, generate_splits, validate_splits`; `from joblib import Parallel, delayed`; `import numpy as np`.
  - IO/model/network markers (selection): `line 34: (c.OUT / 'config/contracts_output.txt').write_text(output.getvalue(), encoding='utf-8')`; `line 37: c.write_json(c.OUT / 'config/contracts.json', {'status': 'PASS', 'tests_run': result.testsRun, 'real_estimator_fits': 0, 'runtime_thread_smoke': 'PASS', 'completed_utc': `; `line 40: c.write_json(c.OUT / 'config/configurations.json', {'runtime': rt, 'features': columns, 'candidate_order': [x['id'] for x in configurations()], 'configurations': configur`; `line 43: c.write_json(c.OUT / 'splits/nested_splits.json', {'canonical_ids': frame.canonical_id.tolist(), 'outer_folds': splits, 'inner_generator': {'n_splits': 3, 'shuffle': True`.
- `RAG/results/rag_e8_rf_tuning_v1/scripts/evaluate_e8.py` SHA-256 `d5bfb9941e93a77bd8f608593a3c7ebabb5d84d52e6742726d9a1f715c6a2d4e`.
  - Observed imports (selection): `import json`; `import hashlib`; `import e8_common as c`; `import numpy as np`; `import pandas as pd`; `from sklearn.ensemble import RandomForestRegressor`; `from e8_data import load_data, runtime, baseline`; `from nested_rf import tune_training_only, metrics, paired, validate_splits`.
  - IO/model/network markers (selection): `line 36: c.write_json(c.OUT / 'evaluation/evaluation_started.json', {'started_utc': c.now(), 'execution_freeze_sha256': c.sha(c.OUT / 'config/execution_freeze.json'), 'expected_e8`; `line 109: c.csv_write(c.OUT / 'evaluation/e8_oof_predictions.csv', oof)`; `line 110: c.csv_write(c.OUT / 'evaluation/inner_scores.csv', pd.DataFrame(all_scores))`; `line 111: c.write_json(c.OUT / 'evaluation/selected_configurations.json', selections)`.
- `RAG/results/rag_e8_rf_tuning_v1/scripts/nested_rf.py` SHA-256 `8c6b8ecde3bb44717e7a63cb4e7d93a09ec4fb7928b19a758198b67ffb4ec7ec`.
  - Observed imports (selection): `import numpy as np`; `import pandas as pd`; `from scipy.stats import spearmanr, binomtest`; `from sklearn.ensemble import RandomForestRegressor`; `from sklearn.model_selection import StratifiedKFold`.
- `RAG/results/rag_e8_rf_tuning_v1/scripts/report_e8_render_fixed.py` SHA-256 `8aa83b8ffd63bbfd1f5c231bb8fc2ae84594f7f9ed80f24937fb79a1c11199a5`.
  - Observed imports (selection): `import json`; `import hashlib`; `import e8_common as c`; `from evaluate_e8 import verify_execution`; `import numpy as np`; `import pandas as pd`; `from nested_rf import metrics, paired, select, validate_splits`; `from e8_data import load_data, baseline, runtime`.
  - IO/model/network markers (selection): `line 95: c.write_json(c.OUT / 'config/completion_manifest.json', {'status': 'COMPLETED', 'completed_utc': c.now(), 'nested_evaluations': 1, 'files': {p.relative_to(c.OUT).as_posix`; `line 90: c.write_json(c.OUT / 'config/final_integrity.json', audit)`; `line 94: guard.save()`; `line 99: json.dumps({'status': 'COMPLETED', 'audit': audit, 'report': str(c.OUT / 'E8_RESULTS.md')})`.

## e8_original_report - Historical E8 report syntax failure

**Categories:** STATIC_ONLY; BLOCKED_PROVENANCE. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/rag_e8_rf_tuning_v1/scripts/report_e8.py](<../../../RAG/results/rag_e8_rf_tuning_v1/scripts/report_e8.py>)

**Required inputs:** `Original report inputs`.

**Libraries / specifications:** Not importable as-is.

**Models:** No model required for the selected description; transitive initialization still needs review..

**Working-directory and path contract:** Resolve __file__/ROOT/OUT and injected sys.path exactly; changing CWD alone does not relocate fixed paths.

**Outputs:** `Original report target`.

**Potential tracked/historical writes:** Do not repair or overwrite original source.

**Network, downloads and cloud:** No execution performed.

**Frozen/provenance constraints:** Known syntax error line138; existing render_fixed source is separate, not permission to replace the original.

**Missing/public availability:** Historical parse failure remains.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/rag_e8_rf_tuning_v1/scripts/report_e8.py` SHA-256 `7699f5dbc0d383994028ae7ebbc5ba38bf828ca1befb2341f4049e5eba13675a`.

## e9_prepare - E9 baseline/preparation stages

**Categories:** BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/phase3_e9_claim_verification/scripts/verify_baseline.py](<../../../RAG/results/phase3_e9_claim_verification/scripts/verify_baseline.py>)
- [RAG/results/phase3_e9_claim_verification/scripts/prepare.py](<../../../RAG/results/phase3_e9_claim_verification/scripts/prepare.py>)

**Required inputs:** `codex/canonical_human_development_manifest.csv`; `codex/canonical_fold_assignments.csv`; `E6-v2/v3 matrices, OOF/baseline provenance`.

**Libraries / specifications:** numpy,pandas,scipy,sklearn and helper imports.

**Models:** No model required for the selected description; transitive initialization still needs review..

**Working-directory and path contract:** Resolve __file__/ROOT/OUT and injected sys.path exactly; changing CWD alone does not relocate fixed paths.

**Outputs:** `Preparation/claims/provenance/verification files`.

**Potential tracked/historical writes:** verify/preflight names do not prove write-free behavior.

**Network, downloads and cloud:** Some prep is model-free but still not authorized to run.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `codex/canonical_human_development_manifest.csv`: absent; `codex/canonical_fold_assignments.csv`: absent; `E6-v2/v3 matrices, OOF/baseline provenance`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/phase3_e9_claim_verification/scripts/verify_baseline.py` SHA-256 `60fe2f00845ebfaeeaa62590628d9e7433758021189fbce2d94eb2c43b3fbb51`.
  - Observed imports (selection): `import json`; `import importlib.metadata`; `import sys`; `import pandas as pd`; `import numpy as np`; `import e9_common as c`.
  - IO/model/network markers (selection): `line 69: json.dumps(verify()[-1], indent=2)`.
- `RAG/results/phase3_e9_claim_verification/scripts/prepare.py` SHA-256 `da37fd3c84e6094da119cba3dbce978e2e634730a5dbe275c4f7886607f6e165`.
  - Observed imports (selection): `import os`; `import subprocess`; `from datetime import datetime, timezone`; `import e9_common as c`; `from verify_baseline import verify`; `from decomposer import MODEL, VERSION, PROMPT, SCHEMA`.
  - IO/model/network markers (selection): `line 14: c.write_json(c.OUT / 'provenance/baseline_verification.json', audit)`; `line 15: c.write_json(c.OUT / 'evaluation/baseline_metrics.json', audit['metrics'])`; `line 27: c.write_json(c.OUT / 'config/run_config.json', config)`; `line 28: c.write_json(c.OUT / 'config/decomposition_prompt.json', {'version': VERSION, 'system': PROMPT, 'schema': SCHEMA})`.

## e9_api - E9 full decomposition API

**Categories:** STATIC_ONLY; BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/phase3_e9_claim_verification/scripts/run_decomposition.py](<../../../RAG/results/phase3_e9_claim_verification/scripts/run_decomposition.py>)
- [RAG/results/phase3_e9_claim_verification/scripts/decomposer.py](<../../../RAG/results/phase3_e9_claim_verification/scripts/decomposer.py>)

**Required inputs:** `codex/canonical_human_development_manifest.csv`; `codex/canonical_fold_assignments.csv`; `Frozen hyp-only prompt/input selection`.

**Libraries / specifications:** numpy,pandas,urllib and source API contract.

**Models:** `gpt-4o-2024-08-06`.

**Working-directory and path contract:** Fixed claims/cache/full_run; asserts historical branch phase3-e9-claim-verification, different from current branch.

**Outputs:** `Claim cache and run/request markers`.

**Potential tracked/historical writes:** Writes completed experiment tree.

**Network, downloads and cloud:** Explicit API flag/key needed; no cloud or cost approval.

**Frozen/provenance constraints:** Do not spoof old branch or disable frozen prompt/hash assertions.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `codex/canonical_human_development_manifest.csv`: absent; `codex/canonical_fold_assignments.csv`: absent; `Frozen hyp-only prompt/input selection`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/phase3_e9_claim_verification/scripts/run_decomposition.py` SHA-256 `dcc6f45f87820f52e551af0509c769798597c282fc23b4985749ba0db7f4c791`.
  - Observed imports (selection): `import argparse`; `from concurrent.futures import ThreadPoolExecutor, as_completed`; `from datetime import datetime, timezone`; `import hashlib`; `import json`; `import os`; `from pathlib import Path`; `import subprocess`.
  - IO/model/network markers (selection): `line 35: path.parent.mkdir(parents=True, exist_ok=True)`; `line 67: os.environ.get('OPENAI_API_KEY', '').strip()`; `line 79: CACHE.mkdir(parents=True, exist_ok=True)`; `line 104: save(LOCAL / f'resume_{uuid4().hex}.json', {'utc': datetime.now(timezone.utc).isoformat(), 'workers': 1, 'transport_spacing_seconds': 1, 'frozen_sha256': frozen, 'reason'`.
- `RAG/results/phase3_e9_claim_verification/scripts/decomposer.py` SHA-256 `a78bde2644eff93db90230e671b90d97a93b476ded589f920bbd69b469846dc9`.
  - Observed imports (selection): `import hashlib`; `import json`; `import os`; `import time`; `import urllib.request`; `import urllib.error`; `from pathlib import Path`.
  - IO/model/network markers (selection): `line 69: json.dumps({'version': VERSION, 'request': payload(value)}, sort_keys=True, ensure_ascii=False)`; `line 107: os.environ.get('OPENAI_API_KEY')`; `line 110: urllib.request.Request('https://api.openai.com/v1/chat/completions', data=json.dumps(request).encode(), headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'applic`; `line 170: path.parent.mkdir(parents=True, exist_ok=True)`.

## e9_evaluate - E9 claim NLI/evaluation/reporting

**Categories:** BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/phase3_e9_claim_verification/scripts/nli_features.py](<../../../RAG/results/phase3_e9_claim_verification/scripts/nli_features.py>)
- [RAG/results/phase3_e9_claim_verification/scripts/evaluate.py](<../../../RAG/results/phase3_e9_claim_verification/scripts/evaluate.py>)
- [RAG/results/phase3_e9_claim_verification/scripts/report_completed.py](<../../../RAG/results/phase3_e9_claim_verification/scripts/report_completed.py>)

**Required inputs:** `codex/canonical_human_development_manifest.csv`; `codex/canonical_fold_assignments.csv`; `Original claims/scores and E6 baselines`.

**Libraries / specifications:** Transformer dependencies where NLI selected; numpy,pandas,scipy,sklearn.

**Models:** `Original NLI assets from provenance`.

**Working-directory and path contract:** Resolve __file__/ROOT/OUT and injected sys.path exactly; changing CWD alone does not relocate fixed paths.

**Outputs:** `Claim matrices, OOF, metrics/report/fit records`.

**Potential tracked/historical writes:** Can write tracked reports and completed state.

**Network, downloads and cloud:** Some stages infer or fit models; no execution now.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `codex/canonical_human_development_manifest.csv`: absent; `codex/canonical_fold_assignments.csv`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/phase3_e9_claim_verification/scripts/nli_features.py` SHA-256 `95c431086e6ac33948101b82b3dbc2efa8c5af9cde42a7ea7b03e8be0573f647`.
  - Observed imports (selection): `import json`; `import os`; `import sys`; `import pandas as pd`; `import e9_common as c`; `from aggregates import nli, append_features`; `from verify_baseline import verify`; `from decomposer import MODEL, VERSION, cache_key, validate`.
  - IO/model/network markers (selection): `line 43: c.write_json(c.OUT / 'features/nli_started.json', {'model_id': v2_common.MODEL_ID, 'revision': v2_common.REVISION, 'claim_count': len(frame)})`; `line 77: c.write_json(c.OUT / 'features/E9-A_freeze.json', {'status': 'PASS', 'samples': 561, 'feature_count': 44, 'claims_scored': len(frame), 'features_sha256': c.sha(c.OUT / 'f`; `line 75: matrix.to_csv(handle, index=False)`; `line 58: handle.write(json.dumps({'pair_id': pair['pair_id'], 'canonical_id': row.canonical_id, 'reference_column': 'src' if row.task == 'PG' else 'tgt', 'premise_sha256': c.hashl`.
- `RAG/results/phase3_e9_claim_verification/scripts/evaluate.py` SHA-256 `f70209db783c39ca18716ef838f95cbfc6d016a4c7af2caef444f06653ddded3`.
  - Observed imports (selection): `import importlib.metadata`; `import numpy as np`; `from sklearn.ensemble import RandomForestRegressor`; `import e9_common as c`; `from verify_baseline import verify`; `from run_decomposition import frozen_check`; `import argparse`; `import pandas as pd`.
  - IO/model/network markers (selection): `line 33: c.write_json(c.OUT / f'evaluation/{variant}_started.json', {'expected_rf_fits': 5, 'feature_count': len(names)})`; `line 62: c.write_json(c.OUT / f'evaluation/{variant}_metrics.json', report)`; `line 41: c.write_json(c.OUT / f'evaluation/fit_{variant}_{fold}_started.json', {'fold': fold, 'train_ids': metadata.loc[train, 'canonical_id'].tolist(), 'validation_ids': metadata`; `line 50: c.write_json(c.OUT / f'evaluation/fit_{variant}_{fold}.json', {'fold': fold, 'completed': True})`.
- `RAG/results/phase3_e9_claim_verification/scripts/report_completed.py` SHA-256 `53812fa6652647dd9b93789f4d92ebe27a54972b1d30d79bf02e5aa2a3334da3`.
  - Observed imports (selection): `import json`; `from pathlib import Path`; `import e9_common as c`.
  - IO/model/network markers (selection): `line 93: (c.OUT / 'E9_RESULTS.md').write_text(text, encoding='utf-8')`; `line 98: c.write_json(c.OUT / 'reports/final_summary.json', final)`; `line 99: json.dumps({'status': status, 'E9-A': a['metrics']['overall'], 'paired': paired}, indent=2)`; `line 73: json.dumps(b['paired_vs_e6_v3'], indent=2)`.

## minicheck - MiniCheck GPU scoring and return

**Categories:** STATIC_ONLY; BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/phase3_e9_claim_verification/minicheck_gpu/run_minicheck_gpu.py](<../../../RAG/results/phase3_e9_claim_verification/minicheck_gpu/run_minicheck_gpu.py>)
- [RAG/results/phase3_e9_claim_verification/minicheck_gpu/prepare_gpu_inputs.py](<../../../RAG/results/phase3_e9_claim_verification/minicheck_gpu/prepare_gpu_inputs.py>)
- [RAG/results/phase3_e9_claim_verification/minicheck_gpu/return_to_local.py](<../../../RAG/results/phase3_e9_claim_verification/minicheck_gpu/return_to_local.py>)

**Required inputs:** `Original claim/reference bundle, model and returned-score manifests`.

**Libraries / specifications:** RAG/results/phase3_e9_claim_verification/minicheck_gpu/requirements_gpu.lock.txt.

**Models:** `bespokelabs/Bespoke-MiniCheck-7B@1ed7786bcda3fa1dc35f7c4ed9e3f36b785d33b8`.

**Working-directory and path contract:** Output/cache args exist; default cache is under user home; local return contracts remain fixed.

**Outputs:** `GPU scores/report/cache and returned feature artifacts`.

**Potential tracked/historical writes:** Return adapters can write fixed local features/minicheck_return.

**Network, downloads and cloud:** --run in source authorizes downloads/scoring, not authorized by Phase15.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/phase3_e9_claim_verification/minicheck_gpu/run_minicheck_gpu.py` SHA-256 `cb140483019a2c9885a3d858ebbfaf8981f52d354f2c108542251d5847bed0ef`.
  - Observed imports (selection): `import argparse`; `import importlib.metadata as metadata`; `import os`; `import platform`; `import subprocess`; `import sys`; `import time`; `from pathlib import Path`.
  - IO/model/network markers (selection): `line 109: destination.mkdir(parents=True, exist_ok=False)`; `line 121: cache_dir.mkdir(parents=True, exist_ok=True)`; `line 160: write(destination / 'MINICHECK_GPU_REPORT.json', report)`; `line 167: (destination / 'environment_freeze.txt').write_text(freeze.stdout, encoding='utf-8')`.
- `RAG/results/phase3_e9_claim_verification/minicheck_gpu/prepare_gpu_inputs.py` SHA-256 `d7654cf98e6a44e6898ba6559fa70f51ee8237918fa97d133b68af45e94d06f7`.
  - Observed imports (selection): `import csv`; `import hashlib`; `import io`; `import json`; `import urllib.request`; `import zipfile`; `from gpu_common import HERE, MODEL, REVISION, COMMIT, SETTINGS, POLICY, require, sha, read, jsonl, digest, write`; `from gpu_common import validate_inputs`.
  - IO/model/network markers (selection): `line 51: urllib.request.urlopen(data_url).read()`; `line 90: write(HERE / 'GPU_RUN_MANIFEST.json', m)`; `line 48: hashlib.sha256(urllib.request.urlopen(url).read()).hexdigest()`; `line 93: json.dumps({'samples': 561, 'claims': 575, 'input_sha256': sha(HERE / 'minicheck_inputs.jsonl'), 'manifest_sha256': sha(HERE / 'GPU_RUN_MANIFEST.json')}, indent=2)`.
- `RAG/results/phase3_e9_claim_verification/minicheck_gpu/return_to_local.py` SHA-256 `57827345469154a1d58a45caab0f2bfccd9b567867b8afed9cf3a25ce2c7dbc0`.
  - Observed imports (selection): `import argparse`; `import csv`; `import io`; `from pathlib import Path`; `from gpu_common import HERE, FEATURES, POLICY, require, sha, read, jsonl, validate_inputs, validate_outputs, aggregate, write`.
  - IO/model/network markers (selection): `line 44: destination.mkdir(parents=True, exist_ok=False)`; `line 48: write(destination / 'E9-B_freeze.json', dict(status='PASS', samples=561, feature_count=49, claims=575, features_sha256=sha(path), gpu_output_sha256=sha(output), e9_a_sha2`; `line 47: csv.writer(f).writerows(augmented)`; `line 47: csv.writer(f)`.

## factcg_development - FactCG development scoring/return/evaluation

**Categories:** STATIC_ONLY; BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/phase3_e9_claim_verification/factcg_gpu/run_factcg_gpu.py](<../../../RAG/results/phase3_e9_claim_verification/factcg_gpu/run_factcg_gpu.py>)
- [RAG/results/phase3_e9_claim_verification/factcg_gpu/return_to_local.py](<../../../RAG/results/phase3_e9_claim_verification/factcg_gpu/return_to_local.py>)
- [RAG/results/phase3_e9_claim_verification/factcg_gpu/evaluate_e10.py](<../../../RAG/results/phase3_e9_claim_verification/factcg_gpu/evaluate_e10.py>)

**Required inputs:** `codex/canonical_human_development_manifest.csv`; `codex/canonical_fold_assignments.csv`; `Whole-hypothesis/reference rows, frozen36 baseline, original FactCG returns`.

**Libraries / specifications:** RAG/results/phase3_e9_claim_verification/factcg_gpu/requirements_gpu.lock.txt.

**Models:** `yaxili96/FactCG-DeBERTa-v3-Large@0430e3509dbd28d2dff7a117c0eae25359ff3e80`.

**Working-directory and path contract:** Resolve __file__/ROOT/OUT and injected sys.path exactly; changing CWD alone does not relocate fixed paths. E10 spans E9/factcg_gpu, features/e10_return and evaluation/E10.

**Outputs:** `37-feature matrix, scores, five-fold OOF and aggregate results`.

**Potential tracked/historical writes:** evaluate_e10 uses exist_ok=False for completed E10 folder; do not clear it.

**Network, downloads and cloud:** GPU/model download and RF fitting are not approved.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `codex/canonical_human_development_manifest.csv`: absent; `codex/canonical_fold_assignments.csv`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/phase3_e9_claim_verification/factcg_gpu/run_factcg_gpu.py` SHA-256 `8a6acc461202746be9aa4b68655c9d882d1a9ac391427ef93043914184ac2c9b`.
  - Observed imports (selection): `import argparse`; `import importlib.metadata as metadata`; `import json`; `import os`; `import platform`; `import subprocess`; `import sys`; `import time`.
  - IO/model/network markers (selection): `line 63: destination.mkdir(parents=True, exist_ok=False)`; `line 76: cache_dir.mkdir(parents=True, exist_ok=True)`; `line 113: write(destination / 'FACTCG_GPU_REPORT.json', report)`; `line 117: (destination / 'environment_freeze.txt').write_text(frozen.stdout, encoding='utf-8')`.
- `RAG/results/phase3_e9_claim_verification/factcg_gpu/return_to_local.py` SHA-256 `5c8531efb5a15be54c7fe421acf6aaa38cf641fad6d3badc6159ae565f11d4f5`.
  - Observed imports (selection): `import argparse`; `import csv`; `from pathlib import Path`; `from factcg_common import HERE, ROOT, FEATURE, POLICY, require, sha, write, validate_inputs, validate_outputs`.
  - IO/model/network markers (selection): `line 33: destination.mkdir(parents=True, exist_ok=False)`; `line 37: write(destination / 'E10_freeze.json', dict(status='PASS', samples=561, feature_count=37, features_sha256=sha(path), baseline_sha256=sha(baseline), gpu_output_sha256=sha(`; `line 36: csv.writer(f).writerows(result)`; `line 43: f.write(source.read_bytes())`.
- `RAG/results/phase3_e9_claim_verification/factcg_gpu/evaluate_e10.py` SHA-256 `43537eb2e0fc3038832250b572e1dd869585a58306c21eb7a007a0a43d9c9e36`.
  - Observed imports (selection): `import argparse`; `import sys`; `from factcg_common import HERE, FEATURE, require, read, sha, write, validate_inputs, validate_outputs`; `from return_to_local import verify_local`; `from verify_baseline import verify`; `import e9_common as c`; `import numpy as np`; `import pandas as pd`.
  - IO/model/network markers (selection): `line 37: out.mkdir(exist_ok=False)`; `line 38: write(out / 'E10_started.json', dict(expected_rf_fits=5, samples=561, feature_count=37, features_sha256=sha(folder / 'E10.csv'), parameters=lock['random_forest']))`; `line 69: write(out / 'E10_metrics.json', report)`; `line 47: write(out / f'fit_{fold}_started.json', dict(fold=fold, train_ids=metadata.loc[train, 'canonical_id'].tolist(), validation_ids=metadata.loc[valid, 'canonical_id'].tolist(`.

## e10_test - Retrospective test reconstruction/extraction/scoring

**Categories:** STATIC_ONLY; BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/e10_official_test_v1/reconstructed_v1/reconstruct.py](<../../../RAG/results/e10_official_test_v1/reconstructed_v1/reconstruct.py>)
- [RAG/results/e10_official_test_v1/reconstructed_v1/extract_cpu.py](<../../../RAG/results/e10_official_test_v1/reconstructed_v1/extract_cpu.py>)
- [RAG/results/e10_official_test_v1/reconstructed_v1/predict_and_score.py](<../../../RAG/results/e10_official_test_v1/reconstructed_v1/predict_and_score.py>)

**Required inputs:** `Original official test rows, canonical/E6-v3 training artifacts, original/reconstructed lexical payloads and staged returns`.

**Libraries / specifications:** Pinned canonical/E6 CPU context; requirements_parser.public.txt; model-specific GPU lock.

**Models:** `Model identities in E10_OFFICIAL_TEST_FEATURE_MANIFEST.json`.

**Working-directory and path contract:** Resolve __file__/ROOT/OUT and injected sys.path exactly; changing CWD alone does not relocate fixed paths. Injects codex/E6/Module4 sources; writes fixed reconstructed_v1/cpu_features.

**Outputs:** `Lexical reconstruction, features, RF serialization, test predictions and tracked locks/metrics`.

**Potential tracked/historical writes:** Tracked manifests/metrics plus raw payloads can be written.

**Network, downloads and cloud:** reconstruct acquires external evidence; other stages infer/fit/score.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile. Retrospective status, prior test exposure and MT-overlap limitations stay explicit.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/e10_official_test_v1/reconstructed_v1/reconstruct.py` SHA-256 `cf863497f2765fe281e2779de77fbfb10f1c5e00fb034bf32129100d29f36306`.
  - Observed imports (selection): `import collections, csv, hashlib, json, sys`; `from pathlib import Path`; `import audit_data as audit`; `import module4_schannel_acquire as transport`.
  - IO/model/network markers (selection): `line 12: p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')`; `line 20: save(HERE / 'test_inputs_label_free.json', rows)`; `line 27: raw.mkdir(exist_ok=True)`; `line 28: processed.mkdir(exist_ok=True)`.
- `RAG/results/e10_official_test_v1/reconstructed_v1/extract_cpu.py` SHA-256 `cd2960a8680a80489a1d5c0d2dc0a62f06d4a35c3c812115daa8e6f9539925ad`.
  - Observed imports (selection): `import argparse, collections, hashlib, importlib.util, json, os, sys, time`; `from pathlib import Path`; `import numpy as np, pandas as pd, torch`; `import v3_common`; `import canonical_feature_extraction as base`; `from transformers import AutoTokenizer, AutoModelForSequenceClassification`; `from sentence_transformers import SentenceTransformer`; `import build_features as e6`.
  - IO/model/network markers (selection): `line 17: hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True).encode()).hexdigest()`; `line 30: dest.mkdir(exist_ok=True)`; `line 33: write(dest / (stage + '_input_lock.json'), {'input_sha256': sha(HERE / 'test_inputs_label_free.json'), 'contract_sha256': sha(HERE.parent / 'E10_OFFICIAL_TEST_FEATURE_MAN`; `line 124: write(done, {'stage': stage, 'input_sha256': sha(HERE / 'test_inputs_label_free.json'), 'device': 'cpu', 'dtype': 'float32', 'threads': 4, 'seconds': time.time() - starte`.
- `RAG/results/e10_official_test_v1/reconstructed_v1/predict_and_score.py` SHA-256 `b8d3fe3bbbc2b9790107249e2226a1c36e8070e5f00b294c690719ac3c662cb0`.
  - Observed imports (selection): `import argparse, collections, hashlib, json, sys, time`; `from pathlib import Path`; `import numpy as np, pandas as pd, joblib, sklearn`; `from sklearn.ensemble import RandomForestRegressor`; `import numpy as np`; `import e9_common as evaluator`.
  - IO/model/network markers (selection): `line 65: write(HERE / 'E10_OFFICIAL_TEST_FEATURES_MANIFEST.json', {'status': 'PASS_FROZEN_BEFORE_TEST_GOLD', 'rows': 1500, 'ordered_features': names, 'task_counts': counts, 'test_`; `line 73: write(HERE / 'PRESCORING_CODE_LOCK.json', {'files': {p.name: sha(p) for p in sorted(HERE.glob('*.py'))}, 'locked_unix': time.time()})`; `line 74: write(HERE / 'E10_OFFICIAL_TEST_TRAIN_MANIFEST.json', {'training_examples': 561, 'source_counts': dict(collections.Counter(metadata.source_split)), 'task_counts': dict(co`; `line 75: write(HERE / 'RF_FIT_STARTED.json', {'started_unix': time.time(), 'fits_authorized': 1})`.

## e11a_prepare - E11-A preparation/validation

**Categories:** BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/phase3_e11_task_adaptation/e11a_prepare_data.py](<../../../RAG/results/phase3_e11_task_adaptation/e11a_prepare_data.py>)
- [RAG/results/phase3_e11_task_adaptation/validate_e11a_protocol.py](<../../../RAG/results/phase3_e11_task_adaptation/validate_e11a_protocol.py>)

**Required inputs:** `codex/canonical_human_development_manifest.csv`; `codex/canonical_fold_assignments.csv`; `E11A_TRAINING_PROTOCOL.json`.

**Libraries / specifications:** stdlib and observed contract helpers.

**Models:** No model required for the selected description; transitive initialization still needs review..

**Working-directory and path contract:** Root sentinel requires exact E11 protocol and E9 paths; fixed e11a_prepared/manifest defaults.

**Outputs:** `Prepared per-fold rows and preparation manifest`.

**Potential tracked/historical writes:** write_once may create fixed files including tracked manifest.

**Network, downloads and cloud:** Model-free prep is not automatically write-free or approved.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `codex/canonical_human_development_manifest.csv`: absent; `codex/canonical_fold_assignments.csv`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/phase3_e11_task_adaptation/e11a_prepare_data.py` SHA-256 `aee42fd2143ec13c3559ebd25689eb9b983f73ca373fe9201e884d2d9e5a7ca5`.
  - Observed imports (selection): `from __future__ import annotations`; `import csv`; `import hashlib`; `import json`; `from collections import Counter`; `from pathlib import Path`; `from scoring_common import HERE, ROOT, require, sha_file`.
  - IO/model/network markers (selection): `line 21: json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')`; `line 39: path.parent.mkdir(parents=True, exist_ok=True)`; `line 113: write_once(MANIFEST, output)`; `line 101: write_once(train_path, jsonl_bytes(train))`.
- `RAG/results/phase3_e11_task_adaptation/validate_e11a_protocol.py` SHA-256 `b7bdb0def785fd29f93e85f77122a1dbc8f7aa6c1c13edbec7b17fcb140f58c4`.
  - Observed imports (selection): `from __future__ import annotations`; `import csv`; `import json`; `import math`; `from collections import Counter`; `from pathlib import Path`; `from scoring_common import HERE, ROOT, require, sha_file`; `from e11a_prepare_data import load_protocol, text_row`.
  - IO/model/network markers (selection): `line 182: json.dumps(validate_local(), indent=2)`.

## e11a_train - E11-A fold worker

**Categories:** BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/phase3_e11_task_adaptation/e11a_train_fold.py](<../../../RAG/results/phase3_e11_task_adaptation/e11a_train_fold.py>)

**Required inputs:** `Original prepared bundle, local pinned encoder and protocol`.

**Libraries / specifications:** RAG/results/phase3_e11_task_adaptation/E11A_REQUIREMENTS.lock.txt.

**Models:** `MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli@b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7`.

**Working-directory and path contract:** execute accepts bundle/model/output paths; full import/initialization closure still needs review.

**Outputs:** `final_checkpoint, heldout rows, FOLD_PASS`.

**Potential tracked/historical writes:** Output parameter is not proof that every library/dependency write is isolated.

**Network, downloads and cloud:** Local training/model loading, not merely data verification; remote wrappers separate.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/phase3_e11_task_adaptation/e11a_train_fold.py` SHA-256 `d1676e37e3d42dd41ed053d20e44065db416488e6037458111f8a041b47ea893`.
  - Observed imports (selection): `from __future__ import annotations`; `import argparse`; `import json`; `import math`; `import os`; `import random`; `import re`; `import sys`.
  - IO/model/network markers (selection): `line 73: target.mkdir(parents=True, exist_ok=False)`; `line 100: AutoTokenizer.from_pretrained(str(model_dir), local_files_only=True, trust_remote_code=False, use_fast=True)`; `line 105: AutoModelForSequenceClassification.from_pretrained(str(model_dir), local_files_only=True, trust_remote_code=False, use_safetensors=True, num_labels=2, ignore_mismatched_s`; `line 206: model.save_pretrained(str(checkpoint), safe_serialization=True)`.

## e11b - E11-B scoring and teacher feasibility

**Categories:** BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/phase3_e11_task_adaptation/validate_teacher_protocol.py](<../../../RAG/results/phase3_e11_task_adaptation/validate_teacher_protocol.py>)
- [RAG/results/phase3_e11_task_adaptation/prepare_scoring_inputs.py](<../../../RAG/results/phase3_e11_task_adaptation/prepare_scoring_inputs.py>)
- [RAG/results/phase3_e11_task_adaptation/run_detector.py](<../../../RAG/results/phase3_e11_task_adaptation/run_detector.py>)
- [RAG/results/phase3_e11_task_adaptation/run_teacher_stage.py](<../../../RAG/results/phase3_e11_task_adaptation/run_teacher_stage.py>)

**Required inputs:** `codex/canonical_human_development_manifest.csv`; `codex/canonical_fold_assignments.csv`; `Unlabeled rows, original detector assets and scoring returns`.

**Libraries / specifications:** Detector-specific torch/transformers and scoring contracts.

**Models:** `FactCG/MiniCheck/HHEM/NLI identities in teacher/scoring manifest`.

**Working-directory and path contract:** Local root sentinel, remote /opt/e11,/results and canonical source::function reference.

**Outputs:** `Scores, teacher/preparation/protocol records`.

**Potential tracked/historical writes:** Scoring/preparation can write fixed E11 paths.

**Network, downloads and cloud:** Detector scoring is inference even without a trained student.

**Frozen/provenance constraints:** Exact detector/protocol/normalization hashes; E11-B is feasibility, not a completed student/Accuracy-Spearman result.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `codex/canonical_human_development_manifest.csv`: absent; `codex/canonical_fold_assignments.csv`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/phase3_e11_task_adaptation/validate_teacher_protocol.py` SHA-256 `f1dc79d87d1b4b1cbf52e8a1aca422666e318d15d631e892b82be9b6fbbff513`.
  - Observed imports (selection): `from __future__ import annotations`; `import csv`; `import hashlib`; `import json`; `import unicodedata`; `from collections import Counter`; `from pathlib import Path`; `from scoring_common import find_local_repo_root`.
  - IO/model/network markers (selection): `line 69: json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')`; `line 176: json.dumps({'status': 'PASS', 'protocol_sha256': p['protocol_sha256'], 'raw_unlabeled': len(unlabeled), 'deduplicated_unlabeled': len(unique), 'folds': summary, 'inferenc`; `line 32: json.dumps(value, ensure_ascii=False, sort_keys=True)`; `line 69: json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)`.
- `RAG/results/phase3_e11_task_adaptation/prepare_scoring_inputs.py` SHA-256 `8c0f2728c71cbbcfa4e487912c6493e7eb456061f318612dd3655a9508b093fb`.
  - Observed imports (selection): `from __future__ import annotations`; `import csv`; `import io`; `import json`; `import math`; `from collections import Counter`; `from pathlib import Path`; `from scoring_common import HERE, ROOT, FORBIDDEN_FIELDS, POLICY, hash_parts, protocol, read_jsonl, reference, require, scoring_row, sha_bytes, sha_file, strict_json, text_keys`.
  - IO/model/network markers (selection): `line 27: path.parent.mkdir(parents=True, exist_ok=True)`; `line 43: writer.writeheader()`; `line 44: writer.writerows(rows)`; `line 32: handle.write(data)`.
- `RAG/results/phase3_e11_task_adaptation/run_detector.py` SHA-256 `f02cad6c6152c1eb6ae7f616fb74eb7f14afc08a658911cb22e8031dde7d555d`.
  - Observed imports (selection): `from __future__ import annotations`; `import argparse`; `import importlib.metadata as metadata`; `import json`; `import os`; `import platform`; `import sys`; `import time`.
  - IO/model/network markers (selection): `line 83: cache_root.mkdir(parents=True, exist_ok=True)`; `line 134: json.dumps(run(args.detector, args.scope, args.prepared_dir, args.output_root, args.package_root, args.cache_root, args.models_root, args.batch_size, args.full_run), inde`; `line 100: json.dumps({'detector': detector, 'scope': scope, 'completed_in_store': len(store.rows), 'requested': len(requested)})`.
- `RAG/results/phase3_e11_task_adaptation/run_teacher_stage.py` SHA-256 `fb40d4ba1797059d1513553e9ee8bdc05664fc1d05d1c0c2ab009d0db98d2ec1`.
  - Observed imports (selection): `from __future__ import annotations`; `import argparse`; `import csv`; `import hashlib`; `import json`; `import math`; `import platform`; `import warnings`.
  - IO/model/network markers (selection): `line 62: (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')`; `line 71: path.parent.mkdir(parents=True, exist_ok=True)`; `line 105: validate_download(raw_dir, 'full')`; `line 456: write_once(manifest_path, json_bytes(manifest))`.

## e11c_labels - E11-C API/batch labels and alternate rescue

**Categories:** STATIC_ONLY; BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/phase3_e11_task_adaptation/e11c/e11c_production.py](<../../../RAG/results/phase3_e11_task_adaptation/e11c/e11c_production.py>)
- [RAG/results/phase3_e11_task_adaptation/e11c/e11c_batch.py](<../../../RAG/results/phase3_e11_task_adaptation/e11c/e11c_batch.py>)
- [RAG/results/phase3_e11_task_adaptation/e11c/run_azure_alternate_rescue.py](<../../../RAG/results/phase3_e11_task_adaptation/e11c/run_azure_alternate_rescue.py>)

**Required inputs:** `Original master rows, protocol, request/batch ledgers and separately approved credentials`.

**Libraries / specifications:** Source-specific provider/batch imports; e11c_common contracts.

**Models:** `Original provider/model identity in protocol, not a substituted current model`.

**Working-directory and path contract:** Fixed private/request/result ledgers and original run identities.

**Outputs:** `Batch requests/results, labels and retry/rescue records`.

**Potential tracked/historical writes:** Never truncate ledgers or resubmit a completed provider batch.

**Network, downloads and cloud:** Cloud costs/retries/rescue require separate approval.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/phase3_e11_task_adaptation/e11c/e11c_production.py` SHA-256 `674fdb250712e2d5bdd658236a9df877ecc305c6978ee6af9e10ae2bf4f115c6`.
  - Observed imports (selection): `import argparse`; `from collections import Counter`; `from contextlib import contextmanager`; `import subprocess`; `import sys`; `import e11c_common as c`; `import e11c_pilot as pilot`.
  - IO/model/network markers (selection): `line 44: c.save(BASELINE, {'files_sha256': {str(p.relative_to(c.HERE)): c.sha(p) for p in sorted(paths)}})`; `line 101: c.write_once(PRIVATE / 'candidates.jsonl', c.rows_bytes(rows))`; `line 128: c.save(c.HERE / f'E11C_PRODUCTION_{stage}_TEST_REPORT.json', {'status': 'PASS', 'suites': reports})`; `line 138: c.save(c.HERE / 'E11C_PRODUCTION_PREFLIGHT.json', {'status': 'PASS', 'protocol_sha256': pilot.EXPECTED, 'pilot_count': 300, 'production_count': 11700, 'total_count': 1200`.
- `RAG/results/phase3_e11_task_adaptation/e11c/e11c_batch.py` SHA-256 `5bb42de422ef04d762818e3ddc68a054425781b2121fe976b45beb8503102c04`.
  - Observed imports (selection): `import argparse`; `import datetime as dt`; `import os`; `import urllib.error`; `import urllib.request`; `import uuid`; `from e11c_common import *`; `from parse_e11c_results import parse_round`.
  - IO/model/network markers (selection): `line 19: os.environ.get('OPENAI_API_KEY')`; `line 80: save(state / 'model_metadata.json', metadata)`; `line 83: save(state / 'submission_intent.json', intent)`; `line 126: save(state / 'download_receipt.json', {'batch': batch, 'files': files, 'request_sha256': sha(path), 'protocol_sha256': spec['protocol_sha256'], 'terminal_observed_utc': n`.
- `RAG/results/phase3_e11_task_adaptation/e11c/run_azure_alternate_rescue.py` SHA-256 `dc2942134f89308cfc467da5b89b509f9cfeaf6f736f57557f23d5365bfc77e0`.
  - Observed imports (selection): `import argparse`; `import copy`; `import os`; `import re`; `import subprocess`; `import time`; `from pathlib import Path`; `import e11c_common as c`.
  - IO/model/network markers (selection): `line 53: environment()`; `line 91: c.save(folder / 'request.json', body)`; `line 165: c.write_once(OUT / 'rescue_judgments.jsonl', c.rows_bytes(results))`; `line 166: c.save(c.HERE / f'{PREFIX}_AUDIT.json', report)`.

## e11c_training - E11-C preparation/training/evaluation

**Categories:** BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/phase3_e11_task_adaptation/e11c_training/prepare_training.py](<../../../RAG/results/phase3_e11_task_adaptation/e11c_training/prepare_training.py>)
- [RAG/results/phase3_e11_task_adaptation/e11c_training/train_stages.py](<../../../RAG/results/phase3_e11_task_adaptation/e11c_training/train_stages.py>)
- [RAG/results/phase3_e11_task_adaptation/e11c_training/evaluate_training.py](<../../../RAG/results/phase3_e11_task_adaptation/e11c_training/evaluate_training.py>)

**Required inputs:** `codex/canonical_human_development_manifest.csv`; `codex/canonical_fold_assignments.csv`; `Original private bundles, authoritative labels/stage subsets, model and returned prediction/checkpoint data`.

**Libraries / specifications:** RAG/results/phase3_e11_task_adaptation/E11A_REQUIREMENTS.lock.txt; RAG/results/phase3_e11_task_adaptation/e11c_training/README.md.

**Models:** `Inherited pinned MoritzLaurer DeBERTa; C/E stage2 requires its own fold stage1 checkpoint`.

**Working-directory and path contract:** Resolve __file__/ROOT/OUT and injected sys.path exactly; changing CWD alone does not relocate fixed paths. Worker output args coexist with fixed prepare/evaluate private paths.

**Outputs:** `Prepared/runtime manifests, checkpoints, heldout rows and final results`.

**Potential tracked/historical writes:** May write tracked audits/results and private returns.

**Network, downloads and cloud:** Local workers train; Modal wrappers separately blocked.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile. Preserve C two-stage, D human-only contrastive and E two-stage contrastive initialization/data/loss semantics.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `codex/canonical_human_development_manifest.csv`: absent; `codex/canonical_fold_assignments.csv`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/phase3_e11_task_adaptation/e11c_training/prepare_training.py` SHA-256 `75db84281923eb6245ca54d8388dff26fac6e3f06f514126190c5b8153e8b0bf`.
  - Observed imports (selection): `import csv`; `import sys`; `from collections import Counter, defaultdict`; `from pathlib import Path`; `import e11c_common as c`; `import e11c_production as production`; `import e11a_prepare_data as a`; `import validate_e11a_protocol as av`.
  - IO/model/network markers (selection): `line 56: c.save(HERE / 'PRESERVATION_BASELINE.json', {str(p.relative_to(E11)): c.sha(p) for p in paths})`; `line 90: c.write_once(PRIVATE / 'duplicate_exclusions.jsonl', c.rows_bytes(duplicate_removed))`; `line 134: c.save(HERE / 'E11C_TRAINING_PROTOCOL.json', protocol)`; `line 144: c.save(HERE / 'PRETRAINING_AUDIT_INITIAL.json', audit)`.
- `RAG/results/phase3_e11_task_adaptation/e11c_training/train_stages.py` SHA-256 `a56ccc2a4a794d9b332d97facf9b3ee0402a609e798b84e8033003c45dfd9be2`.
  - Observed imports (selection): `import json`; `import math`; `import os`; `import random`; `import sys`; `import time`; `import importlib.metadata`; `from collections import Counter`.
  - IO/model/network markers (selection): `line 64: target.mkdir(parents=True)`; `line 91: AutoTokenizer.from_pretrained(str(model_dir), local_files_only=True, trust_remote_code=False, use_fast=True)`; `line 96: AutoModelForSequenceClassification.from_pretrained(str(model_dir), local_files_only=True, trust_remote_code=False, use_safetensors=True, num_labels=2, ignore_mismatched_s`; `line 193: model.save_pretrained(str(checkpoint), safe_serialization=True)`.
- `RAG/results/phase3_e11_task_adaptation/e11c_training/evaluate_training.py` SHA-256 `84d43f3844f6ff66787fc8aec7bdfba2203554af951aa1ded2911e448ddaf99f`.
  - Observed imports (selection): `import json`; `import math`; `import subprocess`; `from collections import Counter`; `import prepare_training as p`.
  - IO/model/network markers (selection): `line 52: c.write_once(p.PRIVATE / 'E11C_OOF_PREDICTIONS.jsonl', c.rows_bytes(rows))`; `line 66: c.save(p.HERE / 'E11C_RESULTS.json', results)`; `line 74: c.write_once(p.HERE / 'E11C_RESULTS.md', '\n'.join(report).encode())`; `line 85: c.save(p.HERE / 'E11C_TRAINING_AUDIT.json', training_audit)`.

## e11d_training - E11-D preparation/training/evaluation

**Categories:** BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/phase3_e11_task_adaptation/e11d_training/prepare.py](<../../../RAG/results/phase3_e11_task_adaptation/e11d_training/prepare.py>)
- [RAG/results/phase3_e11_task_adaptation/e11d_training/train_fold.py](<../../../RAG/results/phase3_e11_task_adaptation/e11d_training/train_fold.py>)
- [RAG/results/phase3_e11_task_adaptation/e11d_training/evaluate.py](<../../../RAG/results/phase3_e11_task_adaptation/e11d_training/evaluate.py>)

**Required inputs:** `codex/canonical_human_development_manifest.csv`; `codex/canonical_fold_assignments.csv`; `Original private bundles, authoritative labels/stage subsets, model and returned prediction/checkpoint data`.

**Libraries / specifications:** RAG/results/phase3_e11_task_adaptation/E11A_REQUIREMENTS.lock.txt; RAG/results/phase3_e11_task_adaptation/e11d_training/README.md.

**Models:** `Inherited pinned MoritzLaurer DeBERTa; C/E stage2 requires its own fold stage1 checkpoint`.

**Working-directory and path contract:** Resolve __file__/ROOT/OUT and injected sys.path exactly; changing CWD alone does not relocate fixed paths. Worker output args coexist with fixed prepare/evaluate private paths.

**Outputs:** `Prepared/runtime manifests, checkpoints, heldout rows and final results`.

**Potential tracked/historical writes:** May write tracked audits/results and private returns.

**Network, downloads and cloud:** Local workers train; Modal wrappers separately blocked.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile. Preserve C two-stage, D human-only contrastive and E two-stage contrastive initialization/data/loss semantics.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `codex/canonical_human_development_manifest.csv`: absent; `codex/canonical_fold_assignments.csv`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/phase3_e11_task_adaptation/e11d_training/prepare.py` SHA-256 `ba66c36feffd8df74aaead70419b08dfafbd9b4f19dc302d730b0af780c22405`.
  - Observed imports (selection): `import hashlib`; `import json`; `import sys`; `from datetime import datetime, timezone`; `from pathlib import Path`; `from scoring_common import ROOT, sha_file, require`; `from e11a_prepare_data import load_protocol`; `from validate_e11a_protocol import validate_local, read_jsonl`.
  - IO/model/network markers (selection): `line 82: save(HERE / 'E11D_LOSS_PROTOCOL.json', design)`; `line 85: AutoTokenizer.from_pretrained(str(ROOT / spec['model']['local_mirror_dir']), local_files_only=True, use_fast=True)`; `line 93: save(HERE / 'private/PRESERVED_SHA256.json', protected)`; `line 103: save(HERE / 'E11D_PRETRAINING_AUDIT.json', audit)`.
- `RAG/results/phase3_e11_task_adaptation/e11d_training/train_fold.py` SHA-256 `e9a70577d9ca425e8488603456bf963ccdaca19620c43958f5fd9a8606be43cb`.
  - Observed imports (selection): `from __future__ import annotations`; `import argparse`; `import json`; `import math`; `import os`; `import random`; `import re`; `import sys`.
  - IO/model/network markers (selection): `line 78: target.mkdir(parents=True, exist_ok=False)`; `line 105: AutoTokenizer.from_pretrained(str(model_dir), local_files_only=True, trust_remote_code=False, use_fast=True)`; `line 110: AutoModelForSequenceClassification.from_pretrained(str(model_dir), local_files_only=True, trust_remote_code=False, use_safetensors=True, num_labels=2, ignore_mismatched_s`; `line 224: model.save_pretrained(str(checkpoint), safe_serialization=True)`.
- `RAG/results/phase3_e11_task_adaptation/e11d_training/evaluate.py` SHA-256 `cd5fcb11428a62e1e1dce3e52e17ca8bdd81eee667ca06ff1df8ddff79872a97`.
  - Observed imports (selection): `import hashlib`; `import json`; `import math`; `from collections import Counter`; `from prepare import HERE, E11, ROOT, save, sha_file, require, baselines, metric, protected_files`.
  - IO/model/network markers (selection): `line 68: save(HERE / 'E11D_RESULTS.json', result)`; `line 71: save(HERE / 'E11D_TRAINING_AUDIT.json', audit)`; `line 83: (HERE / 'E11D_RESULTS.md').write_text('\n'.join(md), encoding='utf-8')`; `line 84: (HERE / 'E11D_TRAINING_AUDIT.md').write_text('# E11-D training audit: PASS\n\n' + '\n\n'.join(md[2:]) + '\n\nAll five persisted checkpoints independently rehashed on the `.

## e11e_training - E11-E preparation/training/evaluation

**Categories:** BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/phase3_e11_task_adaptation/e11e_training/prepare.py](<../../../RAG/results/phase3_e11_task_adaptation/e11e_training/prepare.py>)
- [RAG/results/phase3_e11_task_adaptation/e11e_training/train_stages.py](<../../../RAG/results/phase3_e11_task_adaptation/e11e_training/train_stages.py>)
- [RAG/results/phase3_e11_task_adaptation/e11e_training/evaluate.py](<../../../RAG/results/phase3_e11_task_adaptation/e11e_training/evaluate.py>)

**Required inputs:** `codex/canonical_human_development_manifest.csv`; `codex/canonical_fold_assignments.csv`; `Original private bundles, authoritative labels/stage subsets, model and returned prediction/checkpoint data`.

**Libraries / specifications:** RAG/results/phase3_e11_task_adaptation/E11A_REQUIREMENTS.lock.txt; RAG/results/phase3_e11_task_adaptation/e11e_training/README.md.

**Models:** `Inherited pinned MoritzLaurer DeBERTa; C/E stage2 requires its own fold stage1 checkpoint`.

**Working-directory and path contract:** Resolve __file__/ROOT/OUT and injected sys.path exactly; changing CWD alone does not relocate fixed paths. Worker output args coexist with fixed prepare/evaluate private paths.

**Outputs:** `Prepared/runtime manifests, checkpoints, heldout rows and final results`.

**Potential tracked/historical writes:** May write tracked audits/results and private returns.

**Network, downloads and cloud:** Local workers train; Modal wrappers separately blocked.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile. Preserve C two-stage, D human-only contrastive and E two-stage contrastive initialization/data/loss semantics.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Literal input-path checks in this checkout:** `codex/canonical_human_development_manifest.csv`: absent; `codex/canonical_fold_assignments.csv`: absent.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/phase3_e11_task_adaptation/e11e_training/prepare.py` SHA-256 `a8f02c3dbc0bd0ae794d3b654fa2dd0972efa364b0017c92b5b0b26cccb53817`.
  - Observed imports (selection): `import argparse`; `from collections import Counter, defaultdict`; `from datetime import datetime, timezone`; `from e11e_common import *`; `from transformers import AutoTokenizer`.
  - IO/model/network markers (selection): `line 69: AutoTokenizer.from_pretrained(str(ROOT / a['model']['local_mirror_dir']), local_files_only=True, use_fast=True)`; `line 81: save(HERE / 'E11E_TRAINING_PROTOCOL.json', protocol)`; `line 82: save(HERE / 'private/PRESERVED_SHA256.json', protected_files())`; `line 93: save(HERE / 'PRETRAINING_CHECKS.json', checks)`.
- `RAG/results/phase3_e11_task_adaptation/e11e_training/train_stages.py` SHA-256 `9555ee0c40b1a0378b63e483e2bdcb4b6c178c8a7c46c7794bff1b74b883d41e`.
  - Observed imports (selection): `import json`; `import math`; `import os`; `import random`; `import sys`; `import time`; `import importlib.metadata`; `from collections import Counter`.
  - IO/model/network markers (selection): `line 67: target.mkdir(parents=True)`; `line 94: AutoTokenizer.from_pretrained(str(model_dir), local_files_only=True, trust_remote_code=False, use_fast=True)`; `line 99: AutoModelForSequenceClassification.from_pretrained(str(model_dir), local_files_only=True, trust_remote_code=False, use_safetensors=True, num_labels=2, ignore_mismatched_s`; `line 209: model.save_pretrained(str(checkpoint), safe_serialization=True)`.
- `RAG/results/phase3_e11_task_adaptation/e11e_training/evaluate.py` SHA-256 `1aa787c8593098999aa65af5a39dc1070927ef99f591fa81239fb766377d03f6`.
  - Observed imports (selection): `import math`; `from collections import Counter`; `from e11e_common import *`.
  - IO/model/network markers (selection): `line 91: write_once(oof, ''.join((json.dumps(r, ensure_ascii=False, allow_nan=False) + '\n' for r in rows)).encode())`; `line 92: save(HERE / 'E11E_RESULTS.json', result)`; `line 106: save(HERE / 'E11E_TRAINING_AUDIT.json', audit)`; `line 133: write_once(HERE / 'E11E_RESULTS.md', '\n'.join(md).encode())`.

## remote_jobs_downloads - E11 Modal launch, remote CPU verification and downloads

**Categories:** STATIC_ONLY; BLOCKED_PROVENANCE; BLOCKED_MISSING_INPUTS. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/results/phase3_e11_task_adaptation/download_scoring_outputs.py](<../../../RAG/results/phase3_e11_task_adaptation/download_scoring_outputs.py>)
- [RAG/results/phase3_e11_task_adaptation/e11a_modal.py](<../../../RAG/results/phase3_e11_task_adaptation/e11a_modal.py>)
- [RAG/results/phase3_e11_task_adaptation/e11_modal.py](<../../../RAG/results/phase3_e11_task_adaptation/e11_modal.py>)
- [RAG/results/phase3_e11_task_adaptation/e11a_results/download_checkpoint_blocks.py](<../../../RAG/results/phase3_e11_task_adaptation/e11a_results/download_checkpoint_blocks.py>)
- [RAG/results/phase3_e11_task_adaptation/e11c_training/modal_training.py](<../../../RAG/results/phase3_e11_task_adaptation/e11c_training/modal_training.py>)
- [RAG/results/phase3_e11_task_adaptation/e11c_training/verify_saved_checkpoints.py](<../../../RAG/results/phase3_e11_task_adaptation/e11c_training/verify_saved_checkpoints.py>)
- [RAG/results/phase3_e11_task_adaptation/e11d_training/modal_training.py](<../../../RAG/results/phase3_e11_task_adaptation/e11d_training/modal_training.py>)
- [RAG/results/phase3_e11_task_adaptation/e11d_training/verify_saved_checkpoints.py](<../../../RAG/results/phase3_e11_task_adaptation/e11d_training/verify_saved_checkpoints.py>)
- [RAG/results/phase3_e11_task_adaptation/e11e_training/modal_training.py](<../../../RAG/results/phase3_e11_task_adaptation/e11e_training/modal_training.py>)
- [RAG/results/phase3_e11_task_adaptation/e11e_training/verify_saved_checkpoints.py](<../../../RAG/results/phase3_e11_task_adaptation/e11e_training/verify_saved_checkpoints.py>)

**Required inputs:** `Original remote state/runtime bundles/returns; not queried`.

**Libraries / specifications:** modal SDK and worker specs.

**Models:** `Original remote models/checkpoints`.

**Working-directory and path contract:** Worker /results is a mount point, not volume-native path; local wrappers also have fixed output paths.

**Outputs:** `Remote jobs/checkpoints/hash results or downloaded local blocks`.

**Potential tracked/historical writes:** Checkpoint verifier writes tracked CHECKPOINT_VERIFICATION after verify.remote().

**Network, downloads and cloud:** CPU-only/read-only hashing launches paid-capable Modal CPU functions; do not call it a safe local verifier.

**Frozen/provenance constraints:** Preserve the applicable original input, schema, source and fold expectations. Public-safe projections are not original runtime artifacts. The root .gitignore mismatch is specifically a documented E7/E8 frozen-check issue; it is not asserted to be checked by every script in this profile.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/results/phase3_e11_task_adaptation/download_scoring_outputs.py` SHA-256 `1e951aaee9814e35f414d6efd81a3b8080365e8388196fb56a967e624776314a`.
  - Observed imports (selection): `from __future__ import annotations`; `import argparse`; `import json`; `import re`; `import subprocess`; `import sys`; `from pathlib import Path`.
  - IO/model/network markers (selection): `line 33: local.parent.mkdir(parents=True, exist_ok=True)`.
- `RAG/results/phase3_e11_task_adaptation/e11a_modal.py` SHA-256 `73d7f04ea70c7f79e5ded0f59f7369d18f225a0a66b299640f8f945abe12a8b1`.
  - Observed imports (selection): `from __future__ import annotations`; `import json`; `import re`; `import sys`; `from pathlib import Path`; `import modal`; `from scoring_common import HERE, ROOT, require, sha_file`; `from e11a_prepare_data import load_protocol`.
  - IO/model/network markers (selection): `line 119: json.dumps(checked)`; `line 121: json.dumps(train_locked_fold.remote(fold_id, run_id), indent=2)`; `line 125: json.dumps(smoke.remote(run_id), indent=2)`; `line 130: json.dumps(validate_local_config(), indent=2)`.
- `RAG/results/phase3_e11_task_adaptation/e11_modal.py` SHA-256 `93c7c9efd8253eac80f81ff484bc34483670946965dbdeccb9c73960200c6c5c`.
  - Observed imports (selection): `from __future__ import annotations`; `import json`; `import os`; `import re`; `import subprocess`; `import sys`; `import time`; `from collections import Counter`.
  - IO/model/network markers (selection): `line 223: folder.mkdir(parents=True, exist_ok=True)`; `line 261: verify_remote_layout()`; `line 293: run_dir.mkdir(parents=True, exist_ok=resume)`; `line 325: json.dumps(checked)`.
- `RAG/results/phase3_e11_task_adaptation/e11a_results/download_checkpoint_blocks.py` SHA-256 `3bf3d9f5845544f40139f9206e9b5669a392b50e392e9ab58b65b6c146289c4d`.
  - Observed imports (selection): `from __future__ import annotations`; `import argparse`; `import asyncio`; `import hashlib`; `import json`; `import os`; `from pathlib import Path`; `import aiohttp`.
  - IO/model/network markers (selection): `line 47: partial.parent.mkdir(parents=True, exist_ok=True)`; `line 98: download(args.fold)`; `line 66: handle.write(data)`.
- `RAG/results/phase3_e11_task_adaptation/e11c_training/modal_training.py` SHA-256 `b4ae59dfad64657581d6c071106f71bde2971f30045101105367701689132c99`.
  - Observed imports (selection): `import json`; `import sys`; `from pathlib import Path`; `import modal`; `from train_stages import execute, require, sha_file`.
  - IO/model/network markers (selection): `line 56: target.mkdir(parents=True)`; `line 60: (target / f'fold_{fold}.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')`; `line 60: json.dumps(result, indent=2)`.
- `RAG/results/phase3_e11_task_adaptation/e11c_training/verify_saved_checkpoints.py` SHA-256 `f9a5f0f7ca95b16a6255e731d3cf43007810eab2596415e05d2b1844df0d1181`.
  - Observed imports (selection): `import hashlib`; `import json`; `from pathlib import Path`; `import modal`.
  - IO/model/network markers (selection): `line 35: verify.remote()`; `line 43: json.dump({'status': 'PASS', 'training_reruns': 0, 'original_five_jobs_completed': True, 'stage1_fits': 5, 'stage2_fits': 5, 'evidence': evidence}, f, indent=2)`; `line 45: f.write('\n')`.
- `RAG/results/phase3_e11_task_adaptation/e11d_training/modal_training.py` SHA-256 `6789f03eac08abfbe900e7e8e8285eccfc2040407a925d43f8ef6a8f65f291fd`.
  - Observed imports (selection): `import json`; `import sys`; `from pathlib import Path`; `import modal`; `from scoring_common import require, sha_file`; `from train_fold import execute`.
  - IO/model/network markers (selection): `line 52: target.mkdir(parents=True)`; `line 54: (target / f"fold_{result['fold_id']}.json").write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')`; `line 54: json.dumps(result, indent=2)`.
- `RAG/results/phase3_e11_task_adaptation/e11d_training/verify_saved_checkpoints.py` SHA-256 `8194a4d9e382ef207b9b27c5b748f1f911d5113f69c5385f9d5eb5a72027e9d7`.
  - Observed imports (selection): `import hashlib`; `import json`; `from pathlib import Path`; `import modal`.
  - IO/model/network markers (selection): `line 27: verify.remote()`; `line 33: json.dump(result, out, indent=2)`; `line 33: out.write('\n')`.
- `RAG/results/phase3_e11_task_adaptation/e11e_training/modal_training.py` SHA-256 `ff682b45ade46f73b61cf57522fbdcdf289b9e87d984a8639f31fcb3aa8e8f8e`.
  - Observed imports (selection): `import json`; `import sys`; `from pathlib import Path`; `import modal`; `from train_stages import execute, require, sha_file`; `import shutil`.
  - IO/model/network markers (selection): `line 21: bundle.mkdir(parents=True)`; `line 65: target.mkdir(parents=True)`; `line 30: (bundle / relative).parent.mkdir(parents=True, exist_ok=True)`; `line 68: json.dump(result, out, indent=2)`.
- `RAG/results/phase3_e11_task_adaptation/e11e_training/verify_saved_checkpoints.py` SHA-256 `8a899f4bc2588347971b2e5c056ae9afb6a99c6d06a536b10b845fa5324e1ac8`.
  - Observed imports (selection): `import hashlib`; `import json`; `from pathlib import Path`; `import modal`.
  - IO/model/network markers (selection): `line 43: verify.remote()`; `line 49: json.dump(result, handle, indent=2)`; `line 49: handle.write('\n')`.

## prototype_help_config - Prototype help/config-only future isolation scope

**Categories:** REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [research/prototypes/entailment_prototype/src/main.py](<../../../research/prototypes/entailment_prototype/src/main.py>)
- [research/prototypes/entailment_prototype/src/training/train.py](<../../../research/prototypes/entailment_prototype/src/training/train.py>)

**Required inputs:** `Existing base.yaml; synthetic configuration/string fixtures only for a separately approved test`.

**Libraries / specifications:** Prototype requirements.txt and prior Phase4 environment evidence; current environment not measured.

**Models:** No model required for the selected description; transitive initialization still needs review..

**Working-directory and path contract:** Package src resolution needs prototype root as CWD or a reviewed equivalent; initialize write policy before site/imports.

**Outputs:** `Captured help/config diagnostics in fresh external run folder`.

**Potential tracked/historical writes:** Third-party import startup may create temp/cache files even for help; no training function invocation.

**Network, downloads and cloud:** No network/model loading intended for that narrow future selection, but new contract enforcement remains untested.

**Frozen/provenance constraints:** Prior controlled Phase4 help/config/import evidence is historical, not new execution approval. learning_rate may load as string; do not silently repair it.

**Missing/public availability:** Runtime import/environment/write-boundary verification is not rerun in Phase15.

**Static evidence (selected observations, not a call-graph proof):**
- `research/prototypes/entailment_prototype/src/main.py` SHA-256 `1e8caad6f9e18acc721cec6f4b83011b026454e129d5b9b78e1d028cc8eacfd7`.
  - Observed imports (selection): `import argparse`; `import sys`; `import torch`; `from typing import Optional`; `from src.training.evaluate import evaluate`; `from src.training.pseudo_label import generate_pseudo_labels`; `from src.training.train import train`; `from src.training.ensemble_meta_train import train_meta_classifier`.
  - IO/model/network markers (selection): `line 176: AutoTokenizer.from_pretrained(args.model_name)`; `line 214: trainer.save_model(args.output_dir)`; `line 218: metadata_path.write_text(json.dumps({'model_name': args.model_name, 'max_length': args.max_length, 'pretrained_on': 'NLI'}, indent=2), encoding='utf-8')`; `line 219: json.dumps({'model_name': args.model_name, 'max_length': args.max_length, 'pretrained_on': 'NLI'}, indent=2)`.
- `research/prototypes/entailment_prototype/src/training/train.py` SHA-256 `9b15f12d07d16163d0e6c644fae58223c5b68e413264a4eb2ec9ff04bf958a91`.
  - Observed imports (selection): `import argparse`; `import json`; `from pathlib import Path`; `from typing import Dict, Optional`; `from importlib.util import find_spec`; `import numpy as np`; `import torch`; `import yaml`.
  - IO/model/network markers (selection): `line 155: AutoTokenizer.from_pretrained(model_name)`; `line 160: create_dataset(train_data, tokenizer, max_length, task_type)`; `line 205: trainer.save_model(output_dir)`; `line 208: metadata_path.write_text(json.dumps({'model_name': model_name, 'max_length': max_length, 'task_type': task_type}, indent=2), encoding='utf-8')`.

## future_helpers - Future pure/synthetic helper candidates, not whole-suite permission

**Categories:** CANDIDATE_FOR_FUTURE_TEST; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [RAG/scripts/module4_build_external_lexicon.py](<../../../RAG/scripts/module4_build_external_lexicon.py>)
- [RAG/results/phase3_e11_task_adaptation/scoring_common.py](<../../../RAG/results/phase3_e11_task_adaptation/scoring_common.py>)
- [RAG/results/phase3_e11_task_adaptation/e11d_training/contrastive.py](<../../../RAG/results/phase3_e11_task_adaptation/e11d_training/contrastive.py>)

**Required inputs:** `Fresh synthetic strings/schema/tensors only after separate approval`.

**Libraries / specifications:** Parser bs4, stdlib contracts or torch helper as applicable.

**Models:** No model required for the selected description; transitive initialization still needs review..

**Working-directory and path contract:** Review exact selected pure functions and import closure; do not run module CLI or test suite wholesale.

**Outputs:** `Scratch-only captured diagnostics`.

**Potential tracked/historical writes:** Native/library initialization writes need enforcement before imports.

**Network, downloads and cloud:** No network/model client intended in proposed narrow helper test; not yet proven.

**Frozen/provenance constraints:** Synthetic behavior does not satisfy original artifact/source replay.

**Missing/public availability:** Environment/import safety not measured in Phase15.

**Static evidence (selected observations, not a call-graph proof):**
- `RAG/scripts/module4_build_external_lexicon.py` SHA-256 `db6d3a8ffe595ca875d349b074041c7679328fc9f50df4499a943d129411021e`.
  - Observed imports (selection): `from __future__ import annotations`; `import argparse`; `import copy`; `import csv`; `import hashlib`; `import html`; `import json`; `import re`.
  - IO/model/network markers (selection): `line 83: path.parent.mkdir(parents=True, exist_ok=True)`; `line 277: raw_dir.mkdir(parents=True, exist_ok=True)`; `line 323: snapshot_path.parent.mkdir(parents=True, exist_ok=True)`; `line 324: snapshot_path.write_text(''.join((json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for r in deduped)), encoding='utf-8')`.
- `RAG/results/phase3_e11_task_adaptation/scoring_common.py` SHA-256 `250a9d7a2ed5fd9cb9a0e13d69d883cb4c0031941581fbc7c1afd5db989c0c6f`.
  - Observed imports (selection): `from __future__ import annotations`; `import hashlib`; `import json`; `import math`; `import os`; `import unicodedata`; `from pathlib import Path`.
  - IO/model/network markers (selection): `line 60: json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')`; `line 142: path.parent.mkdir(parents=True, exist_ok=True)`; `line 143: json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)`; `line 146: handle.write(data)`.
- `RAG/results/phase3_e11_task_adaptation/e11d_training/contrastive.py` SHA-256 `62f8f95a535ab6667a75f49e28986cb3fc9457fa72ede7cd09496bae117d1b67`.
  - Observed imports (selection): `import torch`; `import torch.nn.functional as F`.

## archival_probes - Archived probes and historical tools

**Categories:** STATIC_ONLY; REQUIRES_ISOLATION. **Runtime: NOT VERIFIED in Phase 15.**

**Actual entry points / selected modes:**
- [project_records/runtime_probes/modal_gpu_check.py](<../../runtime_probes/modal_gpu_check.py>)
- [project_records/runtime_probes/llm_reasoning.py](<../../runtime_probes/llm_reasoning.py>)

**Required inputs:** `Original historical context`.

**Libraries / specifications:** Modal/Vertex dependencies in original probe source.

**Models:** No model required for the selected description; transitive initialization still needs review..

**Working-directory and path contract:** Archived source is not an approved current workflow.

**Outputs:** `Potential remote GPU/provider result`.

**Potential tracked/historical writes:** Old release tools can rewrite manifests; never rerun for current-layout regeneration.

**Network, downloads and cloud:** Modal/Vertex top-level or invoked calls remain forbidden; no import.

**Frozen/provenance constraints:** Snapshots are not standalone runnable environments.

**Missing/public availability:** The original-data/artifact requirements listed above are not established as available by the presence of this source. Original canonical row manifests/folds, raw data, feature matrices, OOF rows and model/cache payloads required by the selected stage are not supplied together as a runnable public bundle. Review each selected input; this is not a claim that every listed artifact type is read by every entry point.

**Static evidence (selected observations, not a call-graph proof):**
- `project_records/runtime_probes/modal_gpu_check.py` SHA-256 `1ebb5d5dabf4b0ac8636dd0b8ff227d4e7e6133ee4820420dc25f8cab0f187a1`.
  - Observed imports (selection): `import modal`; `import torch`.
  - IO/model/network markers (selection): `line 25: check_gpu.remote()`.
- `project_records/runtime_probes/llm_reasoning.py` SHA-256 `2d0dcb88d8405e6a0113073bca7f0e7680335eb45671b416484a56d2979a57b9`.
  - Observed imports (selection): `import os`; `import vertexai`; `from vertexai.generative_models import GenerativeModel`.

## Mode-specific qualifications

- Module4 `prepare-inputs` derives term/input manifests from canonical rows; it does not require pre-existing raw WordNet/Wiktionary responses in that stage. `acquire` fetches raw sources; `offline-build` consumes those previously acquired assets. The shared family input list above describes this chain, not simultaneous requirements of all three modes. Each mode must use a separately reviewed `--output-dir`.
- E6-v3 HHEM source uses `local_files_only=True` and `trust_remote_code=False`; this does not remove model/cache or environment prerequisites. E6-v4 BERTScore uses a separate encoding environment from its inherited evaluation environment.
- E9 decomposition includes an assertion for the historical branch name. Renaming or spoofing a branch, disabling the assertion or executing different source under an archived hash would not establish provenance.
- E8 original `report_e8.py` retains its known syntax error. The separately named render-fixed script is a distinct historical source; no repair or substitution was performed.
- E11 C/D/E checkpoint verification invokes Modal CPU functions through `verify.remote()`. “Read-only” and “CPU-only” do not mean local execution or no cost. No remote availability or current cost was checked.
- Prototype help/config behavior has prior Phase4 evidence; it was not rerun here. The YAML `learning_rate: 2e-5` string behavior is pre-existing and must not be silently corrected in a parity test.

## Recorded dependency specifications

These files were read as text only. Their presence does not establish an installed, compatible environment.

### RAG/requirements-module4-parser.txt

[RAG/requirements-module4-parser.txt](<../../../RAG/requirements-module4-parser.txt>)

SHA-256: `8ea52aa64e76c5e431833b80cb25b8fcd11e6bac3eda9ad36d31e737ca8fd799`.

```text
beautifulsoup4==4.14.3
```

### RAG/requirements-rag-module1.txt

[RAG/requirements-rag-module1.txt](<../../../RAG/requirements-rag-module1.txt>)

SHA-256: `33c7977e6f877d1add74ca8f515de7e99e4e19ac248f74e848d79fed30f37624`.

```text
pandas
numpy
scipy
scikit-learn
google-genai
google-auth
jupyter
ipykernel
nbformat
```

### RAG/requirements-rag-module2.txt

[RAG/requirements-rag-module2.txt](<../../../RAG/requirements-rag-module2.txt>)

SHA-256: `48cebb1f4722c48a681fc49927e45dfb9ddf66737a617531d0b10f6c7e2f0de2`.

```text
rank-bm25==0.2.2
```

### RAG/results/e10_official_test_v1/reconstructed_v1/requirements_parser.public.txt

[RAG/results/e10_official_test_v1/reconstructed_v1/requirements_parser.public.txt](<../../../RAG/results/e10_official_test_v1/reconstructed_v1/requirements_parser.public.txt>)

SHA-256: `fecd94cac4f6c265e133201bb2c0d8aebc02d169c12ae3a1aa5087df59d32b8b`.

```text
beautifulsoup4==4.14.3
soupsieve==2.8.1
```

### RAG/results/phase3_e11_task_adaptation/E11A_REQUIREMENTS.lock.txt

[RAG/results/phase3_e11_task_adaptation/E11A_REQUIREMENTS.lock.txt](<../../../RAG/results/phase3_e11_task_adaptation/E11A_REQUIREMENTS.lock.txt>)

SHA-256: `28d6e3c646b425f1c8c1795b04337e1bb94f22a5fb9e49ae3aaf64d116fb40a5`.

```text
certifi==2024.8.30
charset-normalizer==3.4.0
click==8.1.7
filelock==3.16.1
fsspec==2024.10.0
huggingface-hub==0.26.2
idna==3.10
jinja2==3.1.4
joblib==1.4.2
markupsafe==3.0.2
mpmath==1.3.0
networkx==3.4.2
nltk==3.9.1
numpy==1.26.4
nvidia-cublas-cu12==12.1.3.1
nvidia-cuda-cupti-cu12==12.1.105
nvidia-cuda-nvrtc-cu12==12.1.105
nvidia-cuda-runtime-cu12==12.1.105
nvidia-cudnn-cu12==8.9.2.26
nvidia-cufft-cu12==11.0.2.54
nvidia-curand-cu12==10.3.2.106
nvidia-cusolver-cu12==11.4.5.107
nvidia-cusparse-cu12==12.1.0.106
nvidia-nccl-cu12==2.19.3
nvidia-nvjitlink-cu12==12.6.85
nvidia-nvtx-cu12==12.1.105
packaging==24.2
protobuf==4.25.5
psutil==6.1.0
pyyaml==6.0.2
regex==2024.11.6
requests==2.32.3
safetensors==0.4.5
sentencepiece==0.2.0
sympy==1.13.3
tokenizers==0.15.2
torch @ https://download.pytorch.org/whl/cu121/torch-2.2.1%2Bcu121-cp311-cp311-linux_x86_64.whl
tqdm==4.67.1
transformers==4.38.1
triton==2.2.0
typing-extensions==4.12.2
urllib3==2.2.3
```

### RAG/results/phase3_e9_claim_verification/factcg_gpu/requirements_gpu.lock.txt

[RAG/results/phase3_e9_claim_verification/factcg_gpu/requirements_gpu.lock.txt](<../../../RAG/results/phase3_e9_claim_verification/factcg_gpu/requirements_gpu.lock.txt>)

SHA-256: `28d6e3c646b425f1c8c1795b04337e1bb94f22a5fb9e49ae3aaf64d116fb40a5`.

```text
certifi==2024.8.30
charset-normalizer==3.4.0
click==8.1.7
filelock==3.16.1
fsspec==2024.10.0
huggingface-hub==0.26.2
idna==3.10
jinja2==3.1.4
joblib==1.4.2
markupsafe==3.0.2
mpmath==1.3.0
networkx==3.4.2
nltk==3.9.1
numpy==1.26.4
nvidia-cublas-cu12==12.1.3.1
nvidia-cuda-cupti-cu12==12.1.105
nvidia-cuda-nvrtc-cu12==12.1.105
nvidia-cuda-runtime-cu12==12.1.105
nvidia-cudnn-cu12==8.9.2.26
nvidia-cufft-cu12==11.0.2.54
nvidia-curand-cu12==10.3.2.106
nvidia-cusolver-cu12==11.4.5.107
nvidia-cusparse-cu12==12.1.0.106
nvidia-nccl-cu12==2.19.3
nvidia-nvjitlink-cu12==12.6.85
nvidia-nvtx-cu12==12.1.105
packaging==24.2
protobuf==4.25.5
psutil==6.1.0
pyyaml==6.0.2
regex==2024.11.6
requests==2.32.3
safetensors==0.4.5
sentencepiece==0.2.0
sympy==1.13.3
tokenizers==0.15.2
torch @ https://download.pytorch.org/whl/cu121/torch-2.2.1%2Bcu121-cp311-cp311-linux_x86_64.whl
tqdm==4.67.1
transformers==4.38.1
triton==2.2.0
typing-extensions==4.12.2
urllib3==2.2.3
```

### RAG/results/phase3_e9_claim_verification/factcg_gpu/requirements_gpu.txt

[RAG/results/phase3_e9_claim_verification/factcg_gpu/requirements_gpu.txt](<../../../RAG/results/phase3_e9_claim_verification/factcg_gpu/requirements_gpu.txt>)

SHA-256: `44fbc99f5f007541734ab2ee375a1cb26cafcb396076e1034c18e4903fdb7b2f`.

```text
# Separate environment from MiniCheck. Official FactCG Torch version, HF safetensors only.
torch @ https://download.pytorch.org/whl/cu121/torch-2.2.1%2Bcu121-cp311-cp311-linux_x86_64.whl
transformers==4.38.1
tokenizers==0.15.2
numpy==1.26.4
nltk==3.9.1
huggingface-hub==0.26.2
safetensors==0.4.5
sentencepiece==0.2.0
protobuf==4.25.5
psutil==6.1.0
```

### RAG/results/phase3_e9_claim_verification/factcg_local_smoke/requirements_local.txt

[RAG/results/phase3_e9_claim_verification/factcg_local_smoke/requirements_local.txt](<../../../RAG/results/phase3_e9_claim_verification/factcg_local_smoke/requirements_local.txt>)

SHA-256: `32fd11b97ea7f2ea9e7c35058e94c6367b395f4c84d48573cf57c09b0e10c268`.

```text
torch @ https://download.pytorch.org/whl/cpu/torch-2.2.1%2Bcpu-cp311-cp311-win_amd64.whl
transformers==4.38.1
tokenizers==0.15.2
numpy==1.26.4
nltk==3.9.1
huggingface-hub==0.26.2
safetensors==0.4.5
sentencepiece==0.2.0
protobuf==4.25.5
psutil==6.1.0
accelerate==0.28.0
```

### RAG/results/phase3_e9_claim_verification/minicheck_gpu/requirements_gpu.lock.txt

[RAG/results/phase3_e9_claim_verification/minicheck_gpu/requirements_gpu.lock.txt](<../../../RAG/results/phase3_e9_claim_verification/minicheck_gpu/requirements_gpu.lock.txt>)

SHA-256: `d73d4b68822ac24ba380dc640ea753dcd97e12ad8695e0a03861fd3dcb130501`.

```text
aiohappyeyeballs==2.4.3
aiohttp==3.11.8
aiosignal==1.3.1
annotated-types==0.7.0
anyio==4.6.2.post1
attrs==24.2.0
certifi==2024.8.30
charset-normalizer==3.4.0
click==8.1.7
cloudpickle==3.1.0
compressed-tensors==0.6.0
datasets==3.1.0
dill==0.3.8
diskcache==5.6.3
distro==1.9.0
einops==0.8.0
fastapi==0.115.5
filelock==3.16.1
frozenlist==1.5.0
fsspec==2024.9.0
gguf==0.10.0
h11==0.14.0
httpcore==1.0.7
httptools==0.6.4
httpx==0.28.0
huggingface-hub==0.26.2
idna==3.10
importlib-metadata==8.5.0
interegular==0.3.3
jinja2==3.1.4
jiter==0.8.0
joblib==1.4.2
jsonschema==4.23.0
jsonschema-specifications==2024.10.1
lark==1.2.2
llvmlite==0.43.0
lm-format-enforcer==0.10.6
markupsafe==3.0.2
minicheck @ git+https://github.com/Liyan06/MiniCheck.git@00a1ed40715ba11b9718ef251a3b0c493992944e
mistral-common==1.5.1
mpmath==1.3.0
msgpack==1.1.0
msgspec==0.18.6
multidict==6.1.0
multiprocess==0.70.16
nest-asyncio==1.6.0
networkx==3.4.2
nltk==3.9.1
numba==0.60.0
numpy==1.26.4
nvidia-cublas-cu12==12.1.3.1
nvidia-cuda-cupti-cu12==12.1.105
nvidia-cuda-nvrtc-cu12==12.1.105
nvidia-cuda-runtime-cu12==12.1.105
nvidia-cudnn-cu12==9.1.0.70
nvidia-cufft-cu12==11.0.2.54
nvidia-curand-cu12==10.3.2.106
nvidia-cusolver-cu12==11.4.5.107
nvidia-cusparse-cu12==12.1.0.106
nvidia-ml-py==12.560.30
nvidia-nccl-cu12==2.20.5
nvidia-nvjitlink-cu12==12.6.85
nvidia-nvtx-cu12==12.1.105
openai==1.54.4
opencv-python-headless==4.10.0.84
outlines==0.0.46
packaging==24.2
pandas==2.2.3
partial-json-parser==0.2.1.1.post4
pillow==10.4.0
prometheus-client==0.21.0
prometheus-fastapi-instrumentator==7.0.0
propcache==0.2.0
protobuf==5.28.3
psutil==6.1.0
py-cpuinfo==9.0.0
pyairports @ git+https://github.com/NICTA/pyairports.git@9699eae8c6b03c97239018dea92e01daa8594936
pyarrow==18.1.0
pycountry==24.6.1
pydantic==2.10.2
pydantic-core==2.27.1
python-dateutil==2.9.0.post0
python-dotenv==1.0.1
pytz==2024.2
pyyaml==6.0.2
pyzmq==26.2.0
ray==2.39.0
referencing==0.35.1
regex==2024.11.6
requests==2.32.3
rpds-py==0.21.0
safetensors==0.4.5
sentencepiece==0.2.0
six==1.16.0
sniffio==1.3.1
starlette==0.41.3
sympy==1.13.3
tiktoken==0.7.0
tokenizers==0.20.1
torch @ https://download.pytorch.org/whl/cu121/torch-2.4.0%2Bcu121-cp311-cp311-linux_x86_64.whl
torchvision @ https://download.pytorch.org/whl/cu121/torchvision-0.19.0%2Bcu121-cp311-cp311-linux_x86_64.whl
tqdm==4.67.1
transformers==4.45.2
triton==3.0.0
typing-extensions==4.12.2
tzdata==2024.2
urllib3==2.2.3
uvicorn==0.32.1
uvloop==0.21.0
vllm==0.6.3.post1
watchfiles==1.0.0
websockets==14.1
xformers==0.0.27.post2
xxhash==3.5.0
yarl==1.18.0
zipp==3.21.0
```

### RAG/results/phase3_e9_claim_verification/minicheck_gpu/requirements_gpu.txt

[RAG/results/phase3_e9_claim_verification/minicheck_gpu/requirements_gpu.txt](<../../../RAG/results/phase3_e9_claim_verification/minicheck_gpu/requirements_gpu.txt>)

SHA-256: `4212a2d7633d0f1c3d6394fcf06aec9afb6998866d04dcb4cbc20dc4b732def8`.

```text
# Linux x86_64, Python 3.11, clean virtualenv. No CPU wheel fallback.
torch @ https://download.pytorch.org/whl/cu121/torch-2.4.0%2Bcu121-cp311-cp311-linux_x86_64.whl
torchvision @ https://download.pytorch.org/whl/cu121/torchvision-0.19.0%2Bcu121-cp311-cp311-linux_x86_64.whl
vllm==0.6.3.post1
xformers==0.0.27.post2
transformers==4.45.2
tokenizers==0.20.1
numpy==1.26.4
nltk==3.9.1
huggingface-hub==0.26.2
safetensors==0.4.5
sentencepiece==0.2.0
pandas==2.2.3
datasets==3.1.0
openai==1.54.4
psutil==6.1.0
# Historical Outlines dependency is no longer available in its original PyPI release.
pyairports @ git+https://github.com/NICTA/pyairports.git@9699eae8c6b03c97239018dea92e01daa8594936
minicheck[llm] @ git+https://github.com/Liyan06/MiniCheck.git@00a1ed40715ba11b9718ef251a3b0c493992944e
```

### research/prototypes/entailment_prototype/requirements.txt

[research/prototypes/entailment_prototype/requirements.txt](<../../../research/prototypes/entailment_prototype/requirements.txt>)

SHA-256: `d68de281766516bfd1a60b6db29dce19ba3ba03a3d72fd81287450e6e675fe22`.

```text
torch>=2.0.0
transformers>=4.30.0
datasets>=2.10.0
scikit-learn>=1.3.0
pandas>=1.5.0
numpy>=1.23.0
scipy>=1.10.0
tqdm>=4.65.0
pyyaml>=6.0
```

## Review gates

Use the [public safe-execution contract](../../../docs/SAFE_EXECUTION.md) and the [output-path risks](OUTPUT_PATH_RISKS.md). Complete scratch-only path enforcement, exact input/hash/schema checks and an approved mode-specific import closure before proposing runtime. This matrix provides no executable launch recipe and authorizes no experiment.

## Important path and dependency evidence

These examples qualify the generic source-root descriptions above. They are not launch instructions.

| Family | Verified source behavior | Reproducibility implication |
|---|---|---|
| Canonical pipeline | Canonical scripts resolve their codex source root with `__file__`; data preparation also reads the original development JSON outside that subtree. | CWD alone does not supply the full legacy layout. Original row manifests and features are required, not only the public fold projection. |
| Historical notebooks | Notebook storage path does not set kernel CWD. Shared cell state, `SHROOM_PROJECT_ROOT`, literal basenames and Colab setup branches coexist. | Inputs, output selection and cell order must be reviewed for the selected variant. No Run All or universal environment is claimed. |
| RAG Module1/2 | Module1 uses `SHROOM_RAG_OUTPUT_DIR` or CWD-derived results; Module2 uses the expected RAG root and protected baseline/cache locations. | A Module1 override is not a general override for later modules. |
| E6/E7/E8 | Experiment-local OUT and repository ROOT derive from source ancestry; E7/E8 common modules use OUT = source parents[1], ROOT = OUT.parents[2]. | Moving a common module changes root discovery; editing it changes frozen source bytes. AccessGuard can write diagnostics before evaluation. |
| E9/E10 | Helpers inject canonical/E6/RAG source paths dynamically. E9 decomposition asserts the historical branch. E10 retrospective feature extraction checks original source SHA-256. | Current-path or public-safe source differences cannot be waived as cosmetic. |
| E11 | `scoring_common.find_local_repo_root` searches for an exact E11 teacher-protocol and E9 layout; workers also support the explicit `/opt/e11` and `/results` topology. | A scratch CWD alone is not an equivalent repository. Worker mount paths do not identify native Modal volume paths. |

Model revisions confirmed in the inspected source/records include:

- Canonical NLI: `microsoft/deberta-large-mnli`; similarity: `sentence-transformers/all-mpnet-base-v2`. No revision is fabricated where the stage does not supply one.
- E6-v2 and the inherited E11 encoder family: `MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli` at `b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7`.
- E6-v3 HHEM: `vectara/hallucination_evaluation_model` at `58383384656cbaec2949a75a41f20e891e90a73b`.
- E6-v4 BERTScore NLI encoder: `microsoft/deberta-large-mnli` at `7296194b9009373def4f7c5dad292651e4b5cf4e`.
- E9 decomposition API model: `gpt-4o-2024-08-06`; this is an external API stage, not a local model artifact.
- MiniCheck: `bespokelabs/Bespoke-MiniCheck-7B` at `1ed7786bcda3fa1dc35f7c4ed9e3f36b785d33b8`, with a vLLM scoring backend.
- FactCG: `yaxili96/FactCG-DeBERTa-v3-Large` at `0430e3509dbd28d2dff7a117c0eae25359ff3e80`.

The E6-v4 encoding record pins Transformers 4.30.2, tokenizers 0.13.3, huggingface-hub 0.25.2 and BERTScore 0.3.13; evaluation inherits a separate environment. An E6-v3 record reports Python 3.11.9, NumPy 2.4.4, pandas 3.0.2, SciPy 1.17.1, scikit-learn 1.8.0, torch 2.11.0, Transformers 5.5.4 and tokenizers 0.22.2. These are recorded historical values, not measurements of a current interpreter, universal requirements or an installation recommendation.

E11-C/E preserve stage2 initialization from their own stage1 checkpoints. E11-D is human-only contrastive; E11-E is two-stage contrastive. E11-B is a feasibility stage without a completed student-model Accuracy/Spearman result. Preserve these distinctions when selecting inputs or interpreting saved records.
