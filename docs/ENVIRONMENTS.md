# Environment matrix

| Area | Available specification | Important constraint |
|---|---|---|
| E1-E4 | Notebook metadata and canonical runtime manifests | Historical notebook environment; paths require configuration |
| E5 Modules 1-2 | [Module 1 requirements](../research/experiments/phase2_rag_features/e5_rag/modules/module1/configs/requirements-rag-module1.txt), [Module 2 requirements](../research/experiments/phase2_rag_features/e5_rag/modules/module2/configs/requirements-rag-module2.txt) | Uses the historical `shroom_ensemble` environment |
| E5 Module 4 | [Parser requirements](../research/shared_tools/lexical_evidence/configs/requirements-module4-parser.txt) and runtime provenance | MPNet cache and external lexical data are separate |
| E6-v1-v3 | Per-run model/config/provenance manifests | Downloaded models are not in staging |
| E6-v4 | Pinned compatibility records | Feature extraction environment differs from RF evaluation |
| E7-E8 | Protocol/configuration manifests | Reuses frozen canonical features and folds |
| E9-E10 | [Local requirements](../research/experiments/phase3_advanced_methods/e10_factcg/development/local_smoke/requirements_local.txt), [retrospective parser requirements](../research/experiments/phase3_advanced_methods/e10_factcg/retrospective_official_test/reconstructed_v1/requirements_parser.public.txt), `requirements_gpu.txt`, lock files and run manifests | Some backends require external models or GPU environments |
| E11-A-E | `E11A_REQUIREMENTS.lock.txt` and C/D/E runtime manifests | Original training used A100 GPUs; weights are external |
| Entailment prototype | [Requirements](../research/prototypes/entailment_prototype/requirements.txt) | Independent historical implementation; not assumed equivalent to the final experiment suite |
