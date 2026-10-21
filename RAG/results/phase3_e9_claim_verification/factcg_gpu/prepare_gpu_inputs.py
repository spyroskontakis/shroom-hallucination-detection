"""One-time local export. No model execution and no official-test paths."""
import csv
from factcg_common import HERE, ROOT, MODEL, REVISION, SOURCE_COMMIT, POLICY, SETTINGS, sha, read, write, digest, require

def main():
    require(not (HERE / 'GPU_RUN_MANIFEST.json').exists(), 'E10 package already frozen')
    e9 = HERE.parent
    v3 = ROOT / 'RAG/results/rag_e6_v3'
    canonical = ROOT / 'codex/canonical_human_development_manifest.csv'
    prior = read(e9 / 'provenance/baseline_verification.json')
    for name, expected in prior['input_sha256'].items():
        require(sha(ROOT / name) == expected, 'baseline provenance: ' + name)
    lock = read(v3 / 'config/run_config.json')
    freeze = read(v3 / 'config/feature_freeze.json')
    baseline = v3 / 'features/e6_v3_36_features.csv'
    require(sha(baseline) == freeze['files']['features/e6_v3_36_features.csv'], 'E6-v3 frozen matrix')
    with canonical.open(encoding='utf-8', newline='') as f:
        refs = [{k: r[k] for k in ['canonical_id', 'task', 'hyp', 'src', 'tgt', 'source_split']} for r in csv.DictReader(f)]
    require(len(refs) == len({r['canonical_id'] for r in refs}) == 561, '561 unique rows')
    require(sum(r['source_split'] == 'development_model_agnostic' for r in refs) == 493 and
            sum(r['source_split'] == 'trial' for r in refs) == 68, 'development/trial only')
    rows = [dict(canonical_id=r['canonical_id'], task=r['task'], whole_hypothesis=r['hyp'],
                 reference_text=r[POLICY[r['task']]]) for r in refs]
    import json
    with (HERE / 'factcg_inputs.jsonl').open('x', encoding='utf-8', newline='\n') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n')
    versions = {'torch': '2.2.1'}
    for line in (HERE / 'requirements_gpu.lock.txt').read_text().splitlines():
        if '==' in line and not line.startswith('#'):
            name, version = line.strip().split('==')
            versions[name] = version
    local_hashes = dict(prior['input_sha256'])
    for p in [v3 / 'config/feature_freeze.json', e9 / 'scripts/e9_common.py',
              e9 / 'scripts/verify_baseline.py', e9 / 'evaluation/E9-A_metrics.json',
              e9 / 'features/E9-A.csv', ROOT / 'RAG/AGENTS.md']:
        local_hashes[p.relative_to(ROOT).as_posix()] = sha(p)
    # Inventory existing E9 files, including the complete MiniCheck package;
    # no broad traversal of datasets, credentials or official-test directories.
    inventory = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(e9.rglob('*'))
                 if p.is_file() and HERE not in p.parents and '__pycache__' not in p.parts}
    payload = [p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    m = dict(schema_version=1, model_id=MODEL, model_revision=REVISION, source_commit=SOURCE_COMMIT,
             sample_count=561, feature_count=37, input_fields=['canonical_id', 'task', 'whole_hypothesis', 'reference_text'],
             reference_policy=POLICY, settings=SETTINGS, input_content_sha256=digest(rows),
             e6_features=lock['features'], dependency_versions=versions,
             package_sha256={p.relative_to(HERE).as_posix(): sha(p) for p in sorted(payload)},
             local_frozen_sha256=local_hashes, preexisting_e9_sha256=inventory,
             minicheck_manifest_sha256=sha(e9 / 'minicheck_gpu/GPU_RUN_MANIFEST.json'),
             minicheck_archive_sha256=sha(e9 / 'minicheck_gpu/minicheck_gpu_portable.zip'),
             evaluation=dict(random_forest=lock['random_forest'], expected_fits=5, oof_count=561,
                             target='p_hallucination', classification_threshold=0.5, clip=[0, 1],
                             spearman_round_decimals=12, bootstrap_samples=10000, bootstrap_seed=42,
                             selection='Accuracy first; Spearman breaks accuracy tie; exact tie retains E6-v3'),
             dependency_resolution=dict(tool='uv 0.8.22', python='3.11', platform='x86_64-manylinux_2_28', exclude_newer='2024-11-30T00:00:00Z'),
             sources=[f'https://github.com/derenlei/FactCG/tree/{SOURCE_COMMIT}',
                      f'https://huggingface.co/{MODEL}/tree/{REVISION}', 'https://arxiv.org/abs/2501.17144'],
             execution_status='PREPARED_ONLY_NO_INFERENCE_NO_RF')
    write(HERE / 'GPU_RUN_MANIFEST.json', m)
    from factcg_common import validate_inputs
    validate_inputs()
    print(json.dumps(dict(samples=561, input_sha256=sha(HERE / 'factcg_inputs.jsonl'),
                         manifest_sha256=sha(HERE / 'GPU_RUN_MANIFEST.json')), indent=2))

if __name__ == '__main__':
    main()
