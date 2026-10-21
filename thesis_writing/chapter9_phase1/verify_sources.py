"""Read-only verification of the thesis phase-one sources; no model execution."""
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
P9 = ROOT / 'RAG/results/phase3_e9_claim_verification'
P11 = ROOT / 'RAG/results/phase3_e11_task_adaptation'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def ranks(values):
    result = [0.0] * len(values)
    order = sorted(range(len(values)), key=values.__getitem__)
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and values[order[j]] == values[order[i]]:
            j += 1
        for k in range(i, j):
            result[order[k]] = (i + j + 1) / 2
        i = j
    return result

def metrics(ids, predictions, gold):
    # Same threshold and 12-decimal rank convention as E9/e9_common.py.
    correct = sum((predictions[i] >= .5) == bool(int(gold[i]['label_bin'])) for i in ids)
    rho = statistics.correlation(
        ranks([float(gold[i]['p_hallucination']) for i in ids]),
        ranks([round(predictions[i], 12) for i in ids]))
    return dict(n=len(ids), correct=correct, accuracy=correct / len(ids), spearman=rho)

def check_metrics(actual, expected):
    for k in ['n', 'correct']:
        assert actual[k] == expected[k], (k, actual, expected)
    for k in ['accuracy', 'spearman']:
        assert math.isclose(actual[k], expected[k], abs_tol=1e-12, rel_tol=0), (k, actual, expected)

def main():
    sources = {}
    def record(path, expected=None):
        digest = sha(path)
        if expected is not None:
            assert digest == expected, str(path)
        sources[path.relative_to(ROOT).as_posix()] = digest
    doc = ROOT / 'thesis_writing/Draft_Final_Experiments_Revised.docx'
    record(doc, 'c3011d3d271b6ea327c7067a43c3daf0e683238ca37fc31e44df5c181e57bb6b')
    baseline = read(P9 / 'provenance/baseline_verification.json')
    for name, digest in baseline['input_sha256'].items():
        record(ROOT / name, digest)
    gold = {r['canonical_id']: r for r in rows(ROOT / 'codex/canonical_human_development_manifest.csv')}
    folds = {r['canonical_id']: r['fold_id'] for r in rows(ROOT / 'codex/canonical_fold_assignments.csv')}
    assert len(gold) == 561
    verified = {}
    variants = [('E6-v3', ROOT / 'RAG/results/rag_e6_v3/evaluation/e6_v3_oof_predictions.csv', P9 / 'evaluation/baseline_metrics.json')]
    variants += [(v, P9 / f'evaluation/{v}_oof.csv', P9 / f'evaluation/{v}_metrics.json') for v in ['E9-A', 'E9-B']]
    variants += [('E10', P9 / 'evaluation/E10/E10_oof.csv', P9 / 'evaluation/E10/E10_metrics.json')]
    for v, oof, report_path in variants:
        report = read(report_path)
        if v != 'E6-v3':
            assert report['status'] == 'COMPLETED'
            record(oof, report['oof_sha256'])
        else:
            record(oof)
        record(report_path)
        rr = rows(oof)
        assert len(rr) == len({r['canonical_id'] for r in rr}) == 561
        assert set(r['canonical_id'] for r in rr) == set(gold)
        predictions = {r['canonical_id']: float(r['prediction']) for r in rr}
        assert all(math.isfinite(p) and 0 <= p <= 1 for p in predictions.values())
        assert all(r['fold_id'] == folds[r['canonical_id']] for r in rr)
        expected = report.get('metrics', report)
        check_metrics(metrics(list(gold), predictions, gold), expected['overall'])
        for task in ['DM', 'MT', 'PG']:
            check_metrics(metrics([i for i in gold if gold[i]['task'] == task], predictions, gold), expected['per_task'][task])
        for fold in range(1, 6):
            check_metrics(metrics([i for i in gold if folds[i] == str(fold)], predictions, gold), expected['per_fold'][str(fold)])
        verified[v] = expected
    manifest = read(P11 / 'E11_FINAL_MANIFEST.json')
    record(P11 / 'E11_FINAL_MANIFEST.json')
    for name, digest in manifest['files_sha256'].items():
        record(P11 / name, digest)
    summary = read(P11 / 'E11_FINAL_SUMMARY.json')
    for name, digest in manifest['source_artifacts_sha256'].items():
        if name.endswith('_RESULTS.json') or name.endswith('_PROTOCOL.json'):
            record(ROOT / name, digest)
    for item in summary['table']:
        if item['correct'] is not None:
            assert item['correct'] / item['denominator'] == item['accuracy']
    for name in ['E9_PROTOCOL.md', 'E9_PROTOCOL_AMENDMENT_01.md', 'config/run_config.json', 'config/decomposition_prompt.json', 'reports/full_decomposition_stats.json', 'minicheck_gpu/returned_phase3-003/MINICHECK_GPU_REPORT.json', 'factcg_gpu/FACTCG_PROTOCOL.md']:
        record(P9 / name)
    report = {'status':'PASS', 'scope':'Read-only source and saved OOF verification; no fits, inference, teacher calls or official-test access.', 'e9_e10_verification':'Independent arithmetic replay of saved OOF; overall, per-task and per-fold match within 1e-12. Not a new experiment.', 'metrics':verified, 'e11_verified_frozen_summary':summary['table'], 'sources_sha256':sources}
    (OUT / 'SOURCE_VERIFICATION.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('PASS:',len(sources),'source hashes; E6-v3/E9-A/E9-B/E10 saved OOF overall/task/fold metrics; E11 frozen summary integrity.')

if __name__ == '__main__':
    main()
