"""Local-only, one-time export of frozen claim/reference fields; no ML imports."""
import csv
import hashlib
import io
import json
import urllib.request
import zipfile
from gpu_common import HERE, MODEL, REVISION, COMMIT, SETTINGS, POLICY, require, sha, read, jsonl, digest, write

def main():
    require(not (HERE / 'GPU_RUN_MANIFEST.json').exists(), 'Package already frozen; do not regenerate')
    root, e9 = HERE.parents[3], HERE.parent
    canonical = root / 'codex/canonical_human_development_manifest.csv'
    provenance = read(e9 / 'provenance/baseline_verification.json')
    require(sha(canonical) == provenance['input_sha256']['codex/canonical_human_development_manifest.csv'], 'canonical freeze')
    freeze = read(e9 / 'features/E9-A_freeze.json')
    require(freeze['status'] == 'PASS' and freeze['feature_count'] == 44, 'E9-A freeze')
    require(sha(e9 / 'features/E9-A.csv') == freeze['features_sha256'], 'E9-A hash')
    require(sha(e9 / 'claims/full_claims.jsonl') == freeze['claims_sha256'], 'claims hash')
    # Preserve a full E9 inventory before package generation; excludes only this new directory.
    inventory = {p.relative_to(root).as_posix(): sha(p) for p in sorted(e9.rglob('*'))
                 if p.is_file() and HERE not in p.parents and '__pycache__' not in p.parts}
    with canonical.open(encoding='utf-8', newline='') as f:
        refs = [{k: r[k] for k in ['canonical_id', 'task', 'source_split', 'src', 'tgt']} for r in csv.DictReader(f)]
    require(len(refs) == len({r['canonical_id'] for r in refs}) == 561, 'canonical population')
    require(sum(r['source_split'] == 'development_model_agnostic' for r in refs) == 493 and
            sum(r['source_split'] == 'trial' for r in refs) == 68, 'development-only population')
    refs = {r['canonical_id']: r for r in refs}
    claims = jsonl(e9 / 'claims/full_claims.jsonl')
    audit = {r['pair_id']: r for r in jsonl(e9 / 'features/nli_input_hashes.jsonl')}
    rows = []
    for r in claims:
        ref = refs[r['canonical_id']]
        require(r['task'] == ref['task'], 'task mismatch')
        row = {k: r[k] for k in ['canonical_id', 'task', 'claim_index', 'claim_text']}
        row['reference_text'] = ref[POLICY[r['task']]]
        old = audit[f"{r['canonical_id']}:{r['claim_index']}"]
        for field, expected in [('claim_text', old['hypothesis_sha256']), ('reference_text', old['premise_sha256'])]:
            require(hashlib.sha256(row[field].encode()).hexdigest() == expected, 'E9-A pair hash mismatch')
        rows.append(row)
    require(len(rows) == 575 and {r['canonical_id'] for r in rows} == set(refs), 'claims population')
    with (HERE / 'minicheck_inputs.jsonl').open('x', encoding='utf-8', newline='\n') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n')
    source_hashes = {}
    for name in ['__init__.py', 'minicheck.py', 'inference.py', 'utils.py']:
        url = f'https://raw.githubusercontent.com/Liyan06/MiniCheck/{COMMIT}/minicheck/{name}'
        source_hashes[name] = hashlib.sha256(urllib.request.urlopen(url).read()).hexdigest()
    # Bundle only the English Punkt tables used by official document chunking.
    data_url = 'https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/tokenizers/punkt_tab.zip'
    data = urllib.request.urlopen(data_url).read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in z.namelist():
            if name.startswith('punkt_tab/english/') and not name.endswith('/'):
                path = HERE / 'nltk_data/tokenizers' / name
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open('xb') as f:
                    f.write(z.read(name))
    config = read(e9 / 'config/run_config.json')
    versions = {'torch': '2.4.0', 'torchvision': '0.19.0', 'vllm': '0.6.3.post1',
                'xformers': '0.0.27.post2', 'transformers': '4.45.2', 'tokenizers': '0.20.1',
                'numpy': '1.26.4', 'nltk': '3.9.1', 'huggingface-hub': '0.26.2',
                'safetensors': '0.4.5', 'sentencepiece': '0.2.0', 'pandas': '2.2.3',
                'datasets': '3.1.0', 'openai': '1.54.4', 'psutil': '6.1.0', 'minicheck': '0.1.0'}
    for line in (HERE / 'requirements_gpu.lock.txt').read_text().splitlines():
        if '==' in line and not line.startswith('#'):
            name, version = line.strip().split('==')
            versions[name] = version
    local_names = ['claims/full_claims.jsonl', 'features/E9-A.csv', 'features/E9-A_freeze.json',
                   'features/nli_input_hashes.jsonl', 'config/run_config.json']
    local_hashes = {(e9 / n).relative_to(root).as_posix(): sha(e9 / n) for n in local_names}
    local_hashes[canonical.relative_to(root).as_posix()] = sha(canonical)
    payload_files = [p for p in HERE.rglob('*') if p.is_file() and
                     (p.suffix in {'.py', '.txt', '.md', '.jsonl', '.tab'} or p.name == '.gitignore')]
    m = dict(schema_version=1, model_id=MODEL, model_revision=REVISION, minicheck_commit=COMMIT,
             sample_count=561, claim_count=575, reference_policy=POLICY, settings=SETTINGS,
             claims_references_sha256=digest(rows), e9_a_features=config['e9_a_features'],
             local_frozen_sha256=local_hashes, preexisting_e9_sha256=inventory,
             official_source_sha256=source_hashes, dependency_versions=versions,
             punkt_download_url=data_url, punkt_archive_sha256=hashlib.sha256(data).hexdigest(),
             package_sha256={p.relative_to(HERE).as_posix(): sha(p) for p in sorted(payload_files)},
             upstream_sources=[f'https://github.com/Liyan06/MiniCheck/tree/{COMMIT}',
                               f'https://huggingface.co/{MODEL}/tree/{REVISION}'],
             validation_scope='Local offline validation only; Linux CUDA execution remains unverified',
             precision_policy='BF16 only; block on older GPUs; no quantization, CPU fallback or context reduction',
             dependency_resolution=dict(tool='uv 0.8.22', python='3.11', platform='x86_64-manylinux_2_28',
                                        exclude_newer='2024-11-30T00:00:00Z',
                                        note='Original pyairports source pinned because historical PyPI release is unavailable'),
             dependency_note='Full Linux transitive lock; preflight checks locked versions; pip freeze records actual environment')
    write(HERE / 'GPU_RUN_MANIFEST.json', m)
    from gpu_common import validate_inputs
    validate_inputs()
    print(json.dumps({'samples': 561, 'claims': 575, 'input_sha256': sha(HERE / 'minicheck_inputs.jsonl'),
                      'manifest_sha256': sha(HERE / 'GPU_RUN_MANIFEST.json')}, indent=2))

if __name__ == '__main__':
    main()
