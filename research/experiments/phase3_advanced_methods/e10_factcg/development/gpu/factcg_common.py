"""Frozen E10 contracts, with no ML imports or data discovery."""
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MODEL = 'yaxili96/FactCG-DeBERTa-v3-Large'
REVISION = '0430e3509dbd28d2dff7a117c0eae25359ff3e80'
SOURCE_COMMIT = '41f185413312ed9b3904ec03963fe899693498e0'
FEATURE = 'factcg_support_probability'
POLICY = {'DM': 'tgt', 'MT': 'tgt', 'PG': 'src'}
SETTINGS = dict(device='cuda:0', dtype='float32', use_safetensors=True,
                use_fast=True, max_length=2048, truncation='only_first', padding='longest',
                pad_token='eos_token', reference_chunk_words=550, batch_size=1,
                hypothesis_split=False, support_class_index=1, activation='softmax',
                reference_aggregation='max', temperature_scaling=None, quantization=None,
                autocast=False, matmul_allow_tf32=False, seed=42)
INPUT_KEYS = {'canonical_id', 'task', 'whole_hypothesis', 'reference_text'}

def require(condition, message):
    if not condition:
        raise ValueError(message)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                        separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def unique(pairs):
    result = {}
    for k, v in pairs:
        require(k not in result, 'duplicate JSON key: ' + k)
        result[k] = v
    return result

def loads(text):
    def bad(value):
        raise ValueError('nonfinite JSON: ' + value)
    return json.loads(text, object_pairs_hook=unique, parse_constant=bad)

def read(path):
    return loads(Path(path).read_text(encoding='utf-8'))

def jsonl(path):
    return [loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines()]

def write(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')

def validate_inputs():
    m = read(HERE / 'GPU_RUN_MANIFEST.json')
    require((m['model_id'], m['model_revision'], m['source_commit']) == (MODEL, REVISION, SOURCE_COMMIT), 'model identity')
    require(m['settings'] == SETTINGS and m['reference_policy'] == POLICY, 'inference policy')
    require(m['sample_count'] == 561 and m['feature_count'] == 37, 'frozen counts')
    for name, expected in m['package_sha256'].items():
        require(sha(HERE / name) == expected, 'package hash: ' + name)
    rows = jsonl(HERE / 'factcg_inputs.jsonl')
    require(len(rows) == 561, 'expected 561 inputs')
    seen = set()
    for r in rows:
        require(set(r) == INPUT_KEYS, 'input field allowlist')
        require(all(type(v) is str and bool(v.strip()) for v in r.values()), 'input value types/empty text')
        require(r['task'] in POLICY and r['canonical_id'] not in seen, 'task/duplicate ID')
        seen.add(r['canonical_id'])
    require(digest(rows) == m['input_content_sha256'], 'input content hash')
    return m, rows

def row_metadata(m, r):
    return dict(input_row_sha256=digest(r), input_sha256=m['package_sha256']['factcg_inputs.jsonl'],
                model_revision=REVISION, source_commit=SOURCE_COMMIT, settings_sha256=digest(SETTINGS))

def validate_outputs(path, report_path=None):
    m, inputs = validate_inputs()
    expected = {r['canonical_id']: r for r in inputs}
    rows = jsonl(path)
    require(len(rows) == 561, 'expected exactly 561 scores')
    seen = set()
    for r in rows:
        require(set(r) == {'canonical_id', 'support_probability', 'model_id', 'inference_metadata'}, 'output fields')
        cid = r['canonical_id']
        require(type(cid) is str and cid in expected and cid not in seen, 'unknown/duplicate canonical ID')
        seen.add(cid)
        p = r['support_probability']
        require(type(p) in (int, float) and math.isfinite(p) and 0 <= p <= 1, 'invalid probability')
        require(r['model_id'] == MODEL, 'output model')
        require(r['inference_metadata'] == row_metadata(m, expected[cid]), 'output provenance')
    require(seen == set(expected), 'missing IDs')
    if report_path is not None:
        report = read(report_path)
        require(report['status'] == 'PASS' and report['model_loaded'] is True and
                report['samples_processed'] == 561 and report['retries'] == 0 and not report['inference_errors'], 'GPU run incomplete')
        require(report['output_sha256'] == sha(path) and report['manifest_sha256'] == sha(HERE / 'GPU_RUN_MANIFEST.json'), 'report hashes')
        require(report['model_id'] == MODEL and report['model_revision'] == REVISION and
                report['settings'] == SETTINGS, 'report model/settings')
        require(report['device']['cuda_available'] is True and report['device']['torch_cuda'] == '12.1', 'GPU runtime evidence')
        require(report['dependencies'] == m['dependency_versions'], 'GPU dependencies')
    return rows
