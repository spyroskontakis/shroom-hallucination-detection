"""Read-only verification of E6 prerequisite artifacts; no model or retrieval calls."""
from pathlib import Path
import hashlib
import importlib.util
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'RAG/results/rag_module4/continuation_v1/schannel_run_v1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    spec = importlib.util.spec_from_file_location('release_verifier', ROOT / 'RAG/module4_release_v1/verify_module4.py')
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    release = verifier.verify(ROOT, ROOT / 'RAG/module4_release_v1/RELEASE_MANIFEST.json', 'local-artifacts')
    assert release['status'] == 'PASS', release
    expected = {
        'codex/canonical_human_development_manifest.csv': '754b66c6c4eca2e92902d0408db4854e922d7dfb396953a0cc043c5477bd6a9b',
        'codex/canonical_fold_assignments.csv': 'f5a5964923806a23dd34a8bcc137f3cf489437e033d645e9d0845bf40792eb5d',
        'codex/canonical_feature_outputs/canonical_human_14_features.csv': '3038bd8752a94064e05389e03b063484a1191f9e9a6164f06d11b40688a6828b',
        'RAG/results/rag_module4/continuation_v1/schannel_run_v1/features/module4_rag_features.csv': '708483b831430d876135d1484ad841bf6ba0d9c9a2d0a5f22df6280535fe3160',
    }
    observed = {p: sha(ROOT / p) for p in expected}
    assert observed == expected
    import pandas as pd
    # Only metadata and predictors are projected; no evaluation label access here.
    ids = pd.read_csv(ROOT / 'codex/canonical_human_development_manifest.csv', usecols=['canonical_id'])
    folds = pd.read_csv(ROOT / 'codex/canonical_fold_assignments.csv', usecols=['canonical_id', 'fold_id'])
    mixed = pd.read_csv(ROOT / 'codex/canonical_feature_outputs/canonical_human_14_features.csv', usecols=['canonical_id', 'fold_id'])
    fused = pd.read_csv(RUN / 'features/module4_fused_21_features.csv')
    assert len(ids) == ids.canonical_id.nunique() == 561
    for f in [folds, mixed, fused]:
        assert len(f) == f.canonical_id.nunique() == 561
        assert set(f.canonical_id) == set(ids.canonical_id)
    assert len(fused.columns) == 22
    joined = mixed.merge(folds, on='canonical_id', validate='one_to_one', suffixes=('_mixed', '_locked'))
    assert joined.fold_id_mixed.equals(joined.fold_id_locked)
    oof_hashes = {}
    for name in ['e3', 'e5']:
        path = RUN / f'evaluation/module4_{name}_oof_predictions.csv'
        pred = pd.read_csv(path)
        assert len(pred) == pred.canonical_id.nunique() == 561
        check = folds.merge(pred, on='canonical_id', validate='one_to_one', suffixes=('_locked', '_oof'))
        assert len(check) == 561 and check.fold_id_locked.equals(check.fold_id_oof)
        oof_hashes[str(path.relative_to(ROOT))] = sha(path)
    baseline = json.loads((RUN / 'evaluation/module4_development_oof_metrics.json').read_text())
    for name, count in [('E3', 445), ('E5', 446)]:
        m = baseline['diagnostics']['all_rows'][name]
        assert m['n'] == 561 and m['accuracy'] == count / 561
    result = {
        'checked_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'INPUT_HASHES_IDS_FOLDS_PASS_RANKING_MISSING',
        'release': release,
        'input_sha256': observed,
        'oof_sha256': oof_hashes,
        'protocol_sha256': sha(OUT / 'E6_PROTOCOL.md'),
        'script_sha256': sha(Path(__file__)),
        'rows': 561,
        'fold_sizes': folds.fold_id.value_counts().sort_index().to_dict(),
        'evidence_rows': int(fused.rag_evidence_available.sum()),
        'saved_baseline_metrics': baseline['diagnostics']['all_rows'],
        'baseline_metrics_check': 'Saved metrics checked; recomputation against labels deferred until feature freeze.',
        'ranking_issue': 'No persisted Module 4 ordered evidence list found. Snapshot order is not retrieval order. No reranking performed.',
        'model_inference_calls': 0, 'training_runs': 0, 'network_calls': 0,
    }
    dest = OUT / 'config/preflight.json'
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        raise FileExistsError(dest)
    dest.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ['status', 'rows', 'fold_sizes', 'evidence_rows', 'saved_baseline_metrics']}))


if __name__ == '__main__':
    main()
