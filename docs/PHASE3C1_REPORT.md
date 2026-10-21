# PHASE 3C.1 completion report

> Historical preservation report. Counts and decisions below describe that earlier phase. See the [current release review](PUBLIC_RELEASE_REVIEW.md) for this candidate; this report is not current publication approval.

Verdict: **PUBLIC CANDIDATE READY WITH WARNINGS**. This is a publication candidate, not a claim of complete runnable reproduction. No GitHub integration or publication was performed.

## Source coverage

36 source files were added relative to the previous staging: eight notebooks, four research/runtime scripts, 23 historical source snapshots, and one recovered functional MPNet provenance test. Within the targeted PHASE 3C missing-code list, **zero significant thesis implementation source files remain unresolved**. This is a scoped recovery conclusion; it does not assert that every privately preserved documentation-production utility belongs in the implementation repository.

| Research area | Preserved implementation |
|---|---|
| E1 | NLI notebook variants and canonical cross-validation code |
| E2 | Similarity feature pipelines and evaluation |
| E3 | NLI/similarity ensemble variants |
| E4 | Synthetic-data augmentation 5/20/50/200 samples, Colab, EDA and ablation variants |
| E5 | RAG Modules 1-4, acquisition, scoring, tests and MPNet provenance |
| E6 | NLI/retrieval variants, BERTScore, configs and compatibility evidence |
| E7 | Agentic variants, evaluation helpers and historical tests |
| E8 | RF tuning source, configurations and selected configurations; original report syntax defect retained |
| E9 | Claim decomposition, NLI/MiniCheck/FactCG, frozen configs, CPU/GPU source variants |
| E10 | Official-test reconstruction and frozen evaluation artifacts/configuration; external rows withheld |
| E11 | Task adaptation A-E, teacher/scoring/training/evaluation/provenance source and historical variants |
| Independent solution | Current independent implementation retained; older main entrypoint evaluated separately |

The source provenance manifest maps every selected implementation artifact to its source and hash. Original layout remains unchanged for active sources. Historical snapshots retain their original relative subpaths below the Git blob directory; they are not standalone runnable checkouts.

## Notebooks

All 38 original notebook occurrences are accounted for. 35 occurrences map to 15 distinct thesis notebook versions (seven previously selected, eight recovered). Three occurrences of one organizer baseline remain private because redistribution permission was not established. All 16 distinct original byte versions are preserved privately. Public notebooks have no outputs, execution counts or attachments. Cell order, definition names and numeric constants were checked; exact per-cell original/public hashes and edits are recorded. This does not claim byte identity or full runtime equivalence for sanitized notebooks.

## Historical source decisions

27 RAG versions plus one independent solution version were compared by source diff and AST definitions/module statements. All 28 original blobs are preserved with SHA-256. RAG: 23 documentary snapshots, one functional test and three private superseded versions. Solution: one private superseded entrypoint.

| Git blob | Original path | Decision | Functional comparison |
|---|---|---|---|
| `adbd78c365bf75fdf843534d87745d15107c9557` | `RAG/results/phase3_e11_task_adaptation/e11c_training/evaluate_training.py` | PUBLIC_HISTORICAL_SOURCE_SNAPSHOT | E11-C evaluation before checkpoint verification/collapse checks and resumed-run provenance. |
| `5629dae9079e1f185da40f82e99e054e113e279f` | `RAG/results/phase3_e9_claim_verification/scripts/evaluate.py` | PUBLIC_HISTORICAL_SOURCE_SNAPSHOT | E9 evaluation before feature-freeze validation and per-fit array provenance. |
| `584d72a776a4a6691a5b5a49084828872721349b` | `RAG/results/phase3_e9_claim_verification/scripts/nli_features.py` | PUBLIC_HISTORICAL_SOURCE_SNAPSHOT | Initial E9 NLI extraction before decomposition freeze and input hashing. |
| `4c41eba009de5ca6b36970128b1a287b4aa48536` | `RAG/results/phase3_e9_claim_verification/tests/test_e9.py` | PUBLIC_HISTORICAL_SOURCE_SNAPSHOT | Earlier decomposition test schema, selection semantics and regression fixtures. |
| `9cc676467a61566ed5ac0b6a86918be0d207f1b8` | `RAG/results/phase3_e9_claim_verification/modal_gpu/modal_phase3_gpu.py` | PUBLIC_HISTORICAL_SOURCE_SNAPSHOT | Earlier Modal package layout and 102400 MiB ephemeral disk instead of 524288 MiB. |
| `1a40378cf2387f5298c5a518013377b8a7207dcc` | `RAG/results/phase3_e9_claim_verification/modal_gpu/modal_phase3_gpu.py` | PUBLIC_HISTORICAL_SOURCE_SNAPSHOT | Intermediate Modal layout using /opt/phase3 with the later disk setting. |
| `bffe88699a68e555820cfc6d9c90ee4790144242` | `RAG/results/phase3_e9_claim_verification/scripts/nli_features.py` | PUBLIC_HISTORICAL_SOURCE_SNAPSHOT | Intermediate frozen E9 features before per-pair input hashes. |
| `18675dcdd946dfcdc3ab0394e53cfa03360759e1` | `RAG/results/phase3_e9_claim_verification/scripts/run_decomposition.py` | PUBLIC_HISTORICAL_SOURCE_SNAPSHOT | Earlier transport without serialized spacing and completed-response replay; preserves failed-attempt behavior. |
| `64d236b32d6edd87323175c865ea8f18d4549800` | `RAG/results/phase3_e11_task_adaptation/validate_teacher_protocol.py` | PUBLIC_HISTORICAL_SOURCE_SNAPSHOT | Original teacher-protocol root and GPU-manifest resolution before portability correction. |
| `bfe9692af66c955d8bee07340bd5feecd7ccf191` | `RAG/results/phase3_e9_claim_verification/scripts/smoke_three.py` | PUBLIC_HISTORICAL_SOURCE_SNAPSHOT | Uses decomposer instead of decomposer_v1; distinct implementation dependency. |
| `5d09d8ce13bada7ad74d065d90c35c5251dd0eb4` | `RAG/results/rag_e7_agentic_v1/scripts/e7_common.py` | PUBLIC_HISTORICAL_SOURCE_SNAPSHOT | Original E7 access guard before Windows shell-probe handling and expanded diagnostics. |
| `4902cddb409eedb61c1d791ad3ff7a73b470ba3a` | `RAG/results/rag_e7_agentic_v1/scripts/preflight.py` | PRIVATE_SUPERSEDED_NO_UNIQUE_FUNCTIONALITY | Only guard phase label changed; executable procedure and assertions unchanged. |
| `4324fa258b7cbb077dc12b2db1c7640d2bbef1cf` | `RAG/results/rag_module4/continuation_v1/mpnet_provenance_v2/tests/test_mpnet_provenance_static.py` | PUBLIC_FUNCTIONAL_TEST | Unique absent AST tests for pinned MPNet revision and local_files_only; restore at original functional path. |
| `ee74fe504276271fc66a73965126b5ced3df997c` | `RAG/results/rag_e7_agentic_v1/scripts/evaluation_common.py` | PUBLIC_HISTORICAL_SOURCE_SNAPSHOT | Earlier estimator/CV guards before added pre/post-fit assertions. |
| `ae6588adc3bb555c2956cf29c71e158d325e203a` | `RAG/results/rag_e7_agentic_v1/scripts/prepare_evaluation.py` | PUBLIC_HISTORICAL_SOURCE_SNAPSHOT | Earlier imported guard reference and subset hash comparison before exact map equality. |
| `dcd8faea7bed70a9fa3196e4288c133e907a7594` | `RAG/results/rag_e7_agentic_v1/tests/test_e7.py` | PUBLIC_HISTORICAL_SOURCE_SNAPSHOT | Earlier zero-based synthetic folds, cosine values and median expectations; distinct historical routing fixtures. |
| `133b206c87ec2159a7492ec12345845ff0a38a7c` | `RAG/results/rag_e6_v2/scripts/report_v2.py` | PRIVATE_SUPERSEDED_NO_UNIQUE_FUNCTIONALITY | Only unmatched quote differs; current report retains all logic with corrected syntax. Broken original preserved privately. |
| `8f0d08bf8575ea0e2c747061212c86245d4a17b5` | `RAG/results/phase3_e11_task_adaptation/build_scoring_manifest.py` | PUBLIC_HISTORICAL_SOURCE_SNAPSHOT | Initial benchmark-001 builder before asset hashes and explicit remote-layout contracts. |
| `fb0f3595d804a40ab62453383e3f633aaca15050` | `RAG/results/phase3_e11_task_adaptation/e11_modal.py` | PUBLIC_HISTORICAL_SOURCE_SNAPSHOT | Original E11 image/import layout before explicit module path, assets and shallow-image repair. |
| `6e527da610242ca0b888a5b7c997831cc91e1669` | `RAG/results/phase3_e11_task_adaptation/run_detector.py` | PRIVATE_SUPERSEDED_NO_UNIQUE_FUNCTIONALITY | Only unused ROOT import removed; detector functions and behavior unchanged. |
| `9e17fe62e1f8f469477e7506b1d790fe11431759` | `RAG/results/phase3_e11_task_adaptation/scoring_common.py` | PUBLIC_HISTORICAL_SOURCE_SNAPSHOT | Original fixed-ancestor ROOT before local/remote separation; historical layout limitation. |
| `1a98655bb5df77da3b040fe356133e155aadb94f` | `RAG/results/phase3_e11_task_adaptation/test_scoring.py` | PUBLIC_HISTORICAL_SOURCE_SNAPSHOT | Original scoring tests before separate-working-directory and local-root regression tests. |
| `b672c0a1ba8f009a6a21ed2178f63c57903d9dfe` | `RAG/results/phase3_e11_task_adaptation/e11a_modal.py` | PUBLIC_HISTORICAL_SOURCE_SNAPSHOT | Smoke-only Modal interface before explicitly gated full-fold execution. |
| `a17ea1a8ebbbe4d4c8c4c716388dfdd00fffa494` | `RAG/results/phase3_e11_task_adaptation/e11a_train_fold.py` | PUBLIC_HISTORICAL_SOURCE_SNAPSHOT | Original E11-A reporting before per-epoch losses; objective and optimizer unchanged. |
| `6fe956954b94855ed307e621cb35f880136a5e00` | `RAG/results/phase3_e11_task_adaptation/build_scoring_manifest.py` | PUBLIC_HISTORICAL_SOURCE_SNAPSHOT | Intermediate benchmark-002 commands before benchmark-003. |
| `2092da822a3bc99dc9da7ca5fec0b184e56e24ec` | `RAG/results/phase3_e11_task_adaptation/import_layout_smoke.py` | PUBLIC_HISTORICAL_SOURCE_SNAPSHOT | Intermediate import smoke before AST ancestor-depth audit and remote-root assertions. |
| `ecf7a94da5ccd992518027200ce10a51801962d5` | `RAG/results/phase3_e11_task_adaptation/test_scoring.py` | PUBLIC_HISTORICAL_SOURCE_SNAPSHOT | Intermediate scoring tests before ancestor-depth/local-root regression assertions. |
| `b307db7c6f31b543d82274f1b629249d8ebaceba` | `solution/src/main.py` | PRIVATE_SUPERSEDED_NO_UNIQUE_FUNCTIONALITY | Old solution CLI subset: train/evaluate/pseudo_label arguments and calls retained; current adds NLI and ensemble commands. Original torch entry-point import preserved privately. |

The recovered test is at `RAG/results/rag_module4/continuation_v1/mpnet_provenance_v2/tests/test_mpnet_provenance_static.py`. Both AST-only tests passed. No training, inference or model import was involved.

## Integrity and privacy

The previous 844-file staging and its private snapshot were independently rehashed after the interruption and matched their baseline. All original staging manifests, including the 71,819-record selection manifest, remain in that protected snapshot. Original Git blobs, notebook occurrences and targeted sources are separately preserved.

The completed candidate is checked by an independent verifier against its full inventory and source provenance. Byte-preserving copies and modified public-safe derivatives have different verification levels. The old scientific hashes still identify original artifacts, not redacted derivatives. No frozen hash guard was bypassed.

Full-file text scans cover personal local paths, credential filenames, secret formats, private endpoints/service identifiers and internal references, with no size exclusion. All JSON and CSV structures were inspected for row-level research data; CSVs contain aggregate metrics plus the explicit public ID/fold projection. Empty teacher-stage JSONL placeholders contain zero rows. Synthetic technical fixtures are retained. No weights, full datasets, private prediction tables, private selection manifests, credentials or nested Git repositories are included. Pattern scanning cannot prove the absence of every conceivable secret.

## Static verification and limits

All notebook code cells passed syntax checks after IPython syntax transformation; notebooks passed structural/output checks without execution. Python syntax passed except the pre-existing E8 `report_e8.py` line-138 error. Imports, literal source references, dynamic path mechanisms and Markdown links were inventoried. Static checks do not establish environment compatibility or runtime resolution of dynamic imports.

The two E11 Markdown links to the withheld full fold CSV were already replaced with external-data explanations in the saved preview. The main reproducibility guide now explicitly distinguishes the full CSV from the public ID/fold projection. Full canonical row-level inputs are supplied separately where permitted.

## Licenses and publication decisions

Selected FactCG source retains its MIT notice. Selected BERTScore 0.3.13 files retain the MIT notice and were checked against installed distribution RECORD hashes. Organizer baseline/checker/scorer source, organizer README documents, and local parser-library copies without verified accompanying notices are private. Parser versions are documented as external requirements. No project-wide license was created.

Before publication: review and approve the candidate; decide whether to authorize a separate E8 syntax repair; decide a project-wide license; maintain authorized separate access to full datasets and frozen artifacts. Withheld third-party materials must not be added without verified redistribution rights. Full executable reproduction needs environment-specific verification in a separately authorized phase. None of these withheld files is an unresolved unique thesis implementation source in the targeted list.

## Public manifest inventory

| Manifest | Purpose |
|---|---|
| source_provenance.public.json | Selected file hashes, experiment mapping, source hashes and transformations |
| file_inventory.public.json | Every final candidate path and size; SHA-256 for every other file; own digest stored in private verification evidence |
| historical_source_review.public.json | All 28 individual historical decisions |
| notebook_coverage.public.json | All 38 original occurrences and public representatives |
| notebook_cell_changes.public.json | Original/public cell hashes and transformations |
| targeted_source_review.public.json | 94 focused manual-review source decisions |
| configuration_review.public.json | 21 configuration candidates, seven restored configurations/freezes |
| canonical_fold_assignments.public.csv | Canonical ID/fold assignments only; not the original row schema |
| e11_checkpoint_recovery_manifest.json | 25 external checkpoints, 215 files, 43,785,823,364 bytes; historical verification evidence only |
| external_artifacts.public.json | Privately retained artifacts and reasons |
| license_review.public.json | Included third-party notices and withheld components |
| final_publication_decisions.public.json | Additional conservative organizer-document exclusions |
| static_import_path_audit.public.json | Static import candidates, literal paths and limitations |

Exact final counts, sizes and SHA-256 values are in the final inventory; independently checked digests and the complete preservation inventory are retained privately. No original project, verified backup, recovered weights or previous staging were modified.
