"""Read-only provenance checks. Never decode test gold values; never fit or score."""
import csv
import hashlib
import json
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SAFE = {'id', 'task', 'src', 'tgt', 'hyp', 'ref', 'model'}

def skip_value(text, pos):
    """Skip JSON value lexically, without decoding its contents."""
    while text[pos].isspace():
        pos += 1
    start = pos
    stack = []
    quoted = False
    escaped = False
    while pos < len(text):
        char = text[pos]
        if quoted:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                quoted = False
                if not stack:
                    return pos + 1
        elif char == '"':
            quoted = True
        elif char in '[{':
            stack.append(char)
        elif char in ']}':
            if not stack:
                return pos
            assert stack.pop() == ('[' if char == ']' else '{')
            if not stack:
                return pos + 1
        elif char == ',' and not stack:
            return pos
        pos += 1
    raise ValueError(f'Unterminated JSON value at offset {start}')

def sanitized_test(path):
    text = path.read_text(encoding='utf-8-sig')
    decoder = json.JSONDecoder()
    pos = 0
    def whitespace(p):
        while p < len(text) and text[p].isspace():
            p += 1
        return p
    pos = whitespace(pos)
    assert text[pos] == '['
    pos += 1
    rows, fields = [], []
    while True:
        pos = whitespace(pos)
        if text[pos] == ']':
            pos += 1
            break
        assert text[pos] == '{'
        pos += 1
        row, keys = {}, []
        while True:
            pos = whitespace(pos)
            if text[pos] == '}':
                pos += 1
                break
            key, pos = decoder.raw_decode(text, pos)
            assert isinstance(key, str) and key not in keys
            keys.append(key)
            pos = whitespace(pos)
            assert text[pos] == ':'
            pos = whitespace(pos + 1)
            if key in SAFE:
                row[key], pos = decoder.raw_decode(text, pos)
            else:
                pos = skip_value(text, pos)
            pos = whitespace(pos)
            if text[pos] == ',':
                pos += 1
            else:
                assert text[pos] == '}'
        rows.append(row)
        fields.append(keys)
        pos = whitespace(pos)
        if text[pos] == ',':
            pos += 1
        else:
            assert text[pos] == ']'
    assert whitespace(pos) == len(text)
    assert all(set(r) <= SAFE for r in rows)
    return rows, fields

def norm(v):
    return ' '.join(unicodedata.normalize('NFC', str(v or '')).strip().split())

def key(row, names=('task', 'src', 'tgt', 'hyp')):
    return hashlib.sha256('\u241f'.join(norm(row.get(k)) for k in names).encode()).hexdigest()

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    canonical_path = ROOT / 'codex/canonical_human_development_manifest.csv'
    canonical = list(csv.DictReader(canonical_path.open(encoding='utf-8-sig', newline='')))
    paths = {
        'trial': ROOT / 'codex/data/Trial/SHROOM_trial-v1.1/trial-v1.json',
        'development_model_agnostic': ROOT / 'Dev/SHROOM_dev-v2/val.model-agnostic.json',
    }
    sources = {k: json.loads(p.read_text(encoding='utf-8')) for k, p in paths.items()}
    for row in canonical:
        original = sources[row['source_split']][int(row['original_row_index'])]
        assert key(row) == key(original) == row['exact_text_key']
        assert row['label'] == original['label']
        assert float(row['p_hallucination']) == original['p(Hallucination)']
    test_path = ROOT / 'Labeled test/SHROOM_test-labeled/test.model-agnostic.json'
    test, fields = sanitized_test(test_path)
    exact = {key(r) for r in test}
    pair = {key(r, ('task', 'src', 'tgt')) for r in test}
    overlap = [r['canonical_id'] for r in canonical if key(r) in exact]
    report = {
        'status': 'FAIL_CONTAMINATION' if overlap else 'PASS_SOURCE_MAPPING_AND_EXACT_DISJOINTNESS',
        'canonical_rows': len(canonical),
        'canonical_sources': dict(Counter(r['source_split'] for r in canonical)),
        'source_rows': {k: len(v) for k, v in sources.items()},
        'omitted_source_indices_zero_based': {k: sorted(set(range(len(v))) - {int(r['original_row_index']) for r in canonical if r['source_split']==k}) for k,v in sources.items()},
        'canonical_tasks': dict(Counter(r['task'] for r in canonical)),
        'source_labels_match': True,
        'canonical_test_exact_overlap_ids': overlap,
        'canonical_test_source_pair_overlap_ids': [r['canonical_id'] for r in canonical if key(r, ('task','src','tgt')) in pair],
        'raw_dev_test_exact_overlap_indices': [i for i,r in enumerate(sources['development_model_agnostic']) if key(r) in exact],
        'test_rows': len(test),
        'test_tasks': dict(Counter(r['task'] for r in test)),
        'test_id_count': sum('id' in r for r in test),
        'test_unique_ids': len({r.get('id') for r in test}),
        'test_unique_full_text_keys': len(exact),
        'test_empty_fields_by_task': {t:{k:sum(not norm(r.get(k)) for r in test if r['task']==t) for k in ['src','tgt','hyp']} for t in ['DM','MT','PG']},
        'test_schema_field_sets': sorted({tuple(sorted(f)) for f in fields}),
        'gold_value_policy': 'Test gold fields lexically skipped, not JSON-decoded, inspected, logged, or scored. Schema key names only checked. Gold value validation deferred until frozen predictions exist.',
        'files_sha256': {str(p.relative_to(ROOT)):sha(p) for p in [canonical_path, *paths.values(),test_path]},
    }
    destination = HERE/'PHASE0_DATA_CHECKS.json'
    with destination.open('x',encoding='utf-8') as f:
        json.dump(report,f,ensure_ascii=False,indent=2)
        f.write('\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if overlap:
        raise SystemExit('STOP: official-test exact examples occur in canonical pool.')

if __name__ == '__main__':
    main()
