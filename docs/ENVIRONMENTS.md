# Environment matrix

| Area | Available specification | Important constraint |
|---|---|---|
| E1-E4 | Notebook metadata and canonical runtime manifests | Historical notebook environment; paths require configuration |
| E5 Modules 1-2 | `RAG/requirements-rag-module1.txt`, `requirements-rag-module2.txt` | Uses the historical `shroom_ensemble` environment |
| E5 Module 4 | `requirements-module4-parser.txt` and runtime provenance | MPNet cache and external lexical data are separate |
| E6-v1-v3 | Per-run model/config/provenance manifests | Downloaded models are not in staging |
| E6-v4 | Pinned compatibility records | Feature extraction environment differs from RF evaluation |
| E7-E8 | Protocol/configuration manifests | Reuses frozen canonical features and folds |
| E9-E10 | `requirements_local.txt`, `requirements_gpu.txt`, lock files and run manifests | Some backends require external models or GPU environments |
| E11-A-E | `E11A_REQUIREMENTS.lock.txt` and C/D/E runtime manifests | Original training used A100 GPUs; weights are external |
| `solution/` | `solution/requirements.txt` | Independent historical implementation; not assumed equivalent to the final experiment suite |