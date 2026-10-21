"""Local-only import. Preserve all 44 E9-A cells; never import or fit an RF."""
import argparse
import csv
import io
from pathlib import Path
from gpu_common import (HERE, FEATURES, POLICY, require, sha, read, jsonl,
                        validate_inputs, validate_outputs, aggregate, write)

def verify_local(m):
    root = HERE.parents[3]
    for name, expected in m['local_frozen_sha256'].items():
        require(sha(root / name) == expected, 'local frozen hash mismatch: ' + name)
    with (root / 'codex/canonical_human_development_manifest.csv').open(encoding='utf-8', newline='') as f:
        # Select only the fields needed for reference/claim integrity.
        refs = {r['canonical_id']: {k: r[k] for k in ['task', 'src', 'tgt', 'source_split']} for r in csv.DictReader(f)}
    claims = jsonl(HERE.parent / 'claims/full_claims.jsonl')
    rebuilt = []
    for r in claims:
        ref = refs[r['canonical_id']]
        require(ref['source_split'] in {'development_model_agnostic', 'trial'}, 'nondevelopment row')
        require(r['task'] == ref['task'], 'local task mismatch')
        rebuilt.append({k: r[k] for k in ['canonical_id', 'task', 'claim_index', 'claim_text']} |
                       {'reference_text': ref[POLICY[r['task']]]})
    require(rebuilt == validate_inputs()[1], 'local claims/reference mismatch')

def build(output, destination):
    m, inputs = validate_inputs()
    verify_local(m)
    rows = validate_outputs(output, output.parent / 'MINICHECK_GPU_REPORT.json')
    groups = {}
    for r in sorted(rows, key=lambda r: (r['canonical_id'], r['claim_index'])):
        groups.setdefault(r['canonical_id'], []).append(r['support_probability'])
    with (HERE.parent / 'features/E9-A.csv').open(encoding='utf-8', newline='') as f:
        matrix = list(csv.reader(f))
    require(matrix[0] == ['canonical_id'] + m['e9_a_features'], 'E9-A feature order')
    require(len(matrix) == 562 and len(matrix[0]) == 45, 'E9-A shape')
    require(len({r[0] for r in matrix[1:]}) == 561 and {r[0] for r in matrix[1:]} == set(groups), 'E9-A population')
    augmented = [matrix[0] + FEATURES]
    for r in matrix[1:]:
        require(len(r) == 45, 'E9-A row width')
        augmented.append(r + [repr(v) for v in aggregate(groups[r[0]])])
    require(all(new[:45] == old for new, old in zip(augmented, matrix)), 'E9-A cells changed')
    # Everything is validated before creating the new, exclusive output directory.
    destination.mkdir(parents=True, exist_ok=False)
    path = destination / 'E9-B.csv'
    with path.open('x', encoding='utf-8', newline='') as f:
        csv.writer(f).writerows(augmented)
    write(destination / 'E9-B_freeze.json', dict(status='PASS', samples=561, feature_count=49,
          claims=575, features_sha256=sha(path), gpu_output_sha256=sha(output),
          e9_a_sha256=sha(HERE.parent / 'features/E9-A.csv'), rf_fits=0,
          threshold=0.5, std_ddof=0, e9_a_cells_preserved=True))
    return path

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--destination', type=Path, default=HERE.parent / 'features/minicheck_return')
    args = parser.parse_args()
    print(build(args.output, args.destination))
