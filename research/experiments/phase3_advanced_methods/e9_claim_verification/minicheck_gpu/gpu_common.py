"""Strict, stdlib-only portable artifact contracts. No inference on import."""
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODEL = 'bespokelabs/Bespoke-MiniCheck-7B'
REVISION = '1ed7786bcda3fa1dc35f7c4ed9e3f36b785d33b8'
COMMIT = '00a1ed40715ba11b9718ef251a3b0c493992944e'
FEATURES = ['minicheck_support_mean', 'minicheck_support_min',
            'minicheck_support_max', 'minicheck_support_std', 'minicheck_unsupported_ratio']
POLICY = {'DM': 'tgt', 'MT': 'tgt', 'PG': 'src'}
INPUT_KEYS = {'canonical_id', 'task', 'claim_index', 'claim_text', 'reference_text'}
SETTINGS = dict(backend='vllm', attention_backend='FLASH_ATTN', dtype='bfloat16', quantization=None,
                tensor_parallel_size=1, max_model_len=32768, chunk_size=32468,
                enable_prefix_caching=False, seed=2024, temperature=0,
                max_tokens=1, logprobs=5, gpu_memory_utilization=0.9,
                cpu_offload_gb=0, kv_cache_dtype='auto', batch_claims=16,
                scoring='official whole-claim max over document chunks; sum exp(logprob) of yes tokens in top-5')

def require(ok, message):
    if not ok:
        raise ValueError(message)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        require(key not in obj, 'duplicate JSON key: ' + key)
        obj[key] = value
    return obj

def loads(text):
    return json.loads(text, object_pairs_hook=unique_object,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON')))

def read(path):
    return loads(Path(path).read_text(encoding='utf-8'))

def jsonl(path):
    return [loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines()]

def write(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')

def key(row):
    require(type(row['canonical_id']) is str and bool(row['canonical_id']), 'canonical ID type')
    require(type(row['claim_index']) is int and row['claim_index'] >= 0, 'claim index type')
    return row['canonical_id'], row['claim_index']

def manifest():
    m = read(HERE / 'GPU_RUN_MANIFEST.json')
    require(m['model_id'] == MODEL and m['model_revision'] == REVISION and
            m['minicheck_commit'] == COMMIT, 'model/implementation identity')
    require(m['settings'] == SETTINGS and m['reference_policy'] == POLICY, 'frozen settings')
    require(m['sample_count'] == 561 and m['claim_count'] == 575, 'frozen counts')
    for name, expected in m['package_sha256'].items():
        require(sha(HERE / name) == expected, 'package hash mismatch: ' + name)
    return m

def validate_inputs():
    m = manifest()
    rows = jsonl(HERE / 'minicheck_inputs.jsonl')
    require(len(rows) == 575, 'expected 575 claims')
    seen, groups = set(), {}
    for r in rows:
        require(set(r) == INPUT_KEYS, 'input field allowlist')
        k = key(r)
        require(k not in seen, 'duplicate input claim')
        seen.add(k)
        require(r['task'] in POLICY, 'task')
        for field in ['claim_text', 'reference_text']:
            require(type(r[field]) is str and bool(r[field].strip()), 'empty/nonstring ' + field)
        groups.setdefault(r['canonical_id'], []).append(r)
    require(len(groups) == 561, 'expected 561 canonical rows')
    for group in groups.values():
        require([r['claim_index'] for r in group] == list(range(len(group))), 'claim indices/order')
        require(len({(r['task'], r['reference_text']) for r in group}) == 1, 'inconsistent sample reference')
    require(digest(rows) == m['claims_references_sha256'], 'claims/references digest')
    return m, rows

def output_metadata(m, r):
    return dict(input_row_sha256=digest(r), input_sha256=m['package_sha256']['minicheck_inputs.jsonl'],
                model_revision=REVISION, minicheck_commit=COMMIT, settings_sha256=digest(SETTINGS))

def validate_outputs(path, report_path=None):
    m, inputs = validate_inputs()
    expected = {key(r): r for r in inputs}
    rows = jsonl(path)
    require(len(rows) == 575, 'expected 575 output claims')
    seen = set()
    for r in rows:
        require(set(r) == {'canonical_id', 'claim_index', 'support_probability', 'model_id', 'inference_metadata'}, 'output field allowlist')
        k = key(r)
        require(k in expected and k not in seen, 'unknown/duplicate output claim')
        seen.add(k)
        p = r['support_probability']
        require(type(p) in (int, float) and math.isfinite(p) and 0 <= p <= 1, 'invalid probability')
        require(r['model_id'] == MODEL, 'output model mismatch')
        require(r['inference_metadata'] == output_metadata(m, expected[k]), 'output provenance mismatch')
    require(seen == set(expected), 'missing output claims')
    if report_path is not None:
        report = read(report_path)
        require(report['status'] == 'PASS' and report['model_loaded'] is True and
                report['claims_processed'] == 575 and not report['inference_errors'] and report['retries'] == 0,
                'GPU report not successful')
        require(report['output_sha256'] == sha(path) and report['manifest_sha256'] == sha(HERE / 'GPU_RUN_MANIFEST.json'), 'report hashes')
        require(report['settings'] == SETTINGS and report['model_id'] == MODEL and
                report['model_revision'] == REVISION, 'report identity')
    return rows

def aggregate(probabilities):
    require(bool(probabilities), 'empty aggregation')
    mean = math.fsum(probabilities) / len(probabilities)
    return [mean, min(probabilities), max(probabilities),
            math.sqrt(math.fsum((p - mean) ** 2 for p in probabilities) / len(probabilities)),
            sum(p < 0.5 for p in probabilities) / len(probabilities)]
