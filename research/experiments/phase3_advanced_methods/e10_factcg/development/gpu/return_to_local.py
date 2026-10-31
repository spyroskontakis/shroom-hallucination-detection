"""Validate GPU return and append exactly one feature to frozen E6-v3 cells."""
import argparse
import csv
from pathlib import Path
from factcg_common import HERE, ROOT, FEATURE, POLICY, require, sha, write, validate_inputs, validate_outputs

def verify_local(m):
    for name, expected in m['local_frozen_sha256'].items():
        require(sha(ROOT / name) == expected, 'local frozen hash: ' + name)
    with (ROOT / 'codex/canonical_human_development_manifest.csv').open(encoding='utf-8', newline='') as f:
        rows = [{k: r[k] for k in ['canonical_id', 'task', 'hyp', 'src', 'tgt', 'source_split']} for r in csv.DictReader(f)]
    require(len(rows) == 561 and all(r['source_split'] in {'development_model_agnostic', 'trial'} for r in rows), 'development population')
    rebuilt = [dict(canonical_id=r['canonical_id'], task=r['task'], whole_hypothesis=r['hyp'],
                    reference_text=r[POLICY[r['task']]]) for r in rows]
    require(rebuilt == validate_inputs()[1], 'whole hypotheses/reference mismatch')

def build(output, destination):
    m, _ = validate_inputs()
    verify_local(m)
    rows = validate_outputs(output, output.parent / 'FACTCG_GPU_REPORT.json')
    scores = {r['canonical_id']: r['support_probability'] for r in rows}
    baseline = ROOT / 'RAG/results/rag_e6_v3/features/e6_v3_36_features.csv'
    with baseline.open(encoding='utf-8', newline='') as f:
        matrix = list(csv.reader(f))
    require(matrix[0] == ['canonical_id'] + m['e6_features'], '36-feature schema')
    require(len(matrix) == 562 and len({r[0] for r in matrix[1:]}) == 561 and
            {r[0] for r in matrix[1:]} == set(scores), 'baseline population')
    result = [matrix[0] + [FEATURE]]
    for r in matrix[1:]:
        require(len(r) == 37, 'baseline width')
        result.append(r + [repr(scores[r[0]])])
    require(all(new[:37] == old for new, old in zip(result, matrix)), 'baseline cells changed')
    destination.mkdir(parents=True, exist_ok=False)
    path = destination / 'E10.csv'
    with path.open('x', encoding='utf-8', newline='') as f:
        csv.writer(f).writerows(result)
    write(destination / 'E10_freeze.json', dict(status='PASS', samples=561, feature_count=37,
          features_sha256=sha(path), baseline_sha256=sha(baseline), gpu_output_sha256=sha(output),
          manifest_sha256=sha(HERE / 'GPU_RUN_MANIFEST.json'), e6_cells_preserved=True, rf_fits=0))
    # Keep the validated raw scores and report beside the matrix for future evaluation checks.
    for name, source in [('factcg_scores.jsonl', output), ('FACTCG_GPU_REPORT.json', output.parent / 'FACTCG_GPU_REPORT.json')]:
        with (destination / name).open('xb') as f:
            f.write(source.read_bytes())
    return path

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--destination', type=Path, default=HERE.parent / 'features/e10_return')
    args = parser.parse_args()
    print(build(args.output, args.destination))
