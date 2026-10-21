"""Verify saved E6-v3 numerically and by hash without fitting or opening test data."""
import json
import importlib.metadata
import sys
import pandas as pd
import numpy as np
import e9_common as c


def verify():
    lock = c.read_json(c.V3 / 'config/run_config.json')
    freeze = c.read_json(c.V3 / 'config/feature_freeze.json')
    manifest = c.read_json(c.V3 / 'config/input_manifest.json')
    saved = c.read_json(c.V3 / 'evaluation/e6_v3_metrics.json')
    # Explicit paths only. Never traverse protected/test inventories.
    paths = [c.CANONICAL, c.FOLDS, c.V3 / 'features/e6_v3_36_features.csv',
             c.V3 / 'features/e6_v3_added_2_features.csv', c.V2 / 'features/e6_v2_34_features.csv',
             c.V3 / 'evaluation/e6_v3_oof_predictions.csv', c.V3 / 'inputs/locked_outer_folds.csv',
             c.ROOT / 'codex/canonical_feature_outputs/canonical_human_14_features.csv',
             c.V3 / 'config/run_config.json', c.V3 / 'config/feature_freeze.json',
             c.V3 / 'config/input_manifest.json', c.V3 / 'evaluation/e6_v3_metrics.json']
    hashes = {str(p.relative_to(c.ROOT)).replace('\\', '/'): c.sha(p) for p in paths}
    for p in [c.CANONICAL, c.FOLDS, paths[4], paths[7]]:
        key = p.relative_to(c.ROOT).as_posix()
        c.require(c.sha(p) == manifest['protected_sha256'][key], 'historical input hash: ' + key)
    for p in paths[2:4]:
        c.require(c.sha(p) == freeze['files'][p.relative_to(c.V3).as_posix()], 'feature hash')
    c.require(c.sha(paths[5]) == saved['oof_sha256'], 'OOF hash')
    c.require(c.sha(paths[6]) == lock['frozen_files']['inputs/locked_outer_folds.csv'], 'locked fold hash')
    pin = c.OUT / 'provenance/baseline_verification.json'
    if pin.exists():
        c.require(hashes == c.read_json(pin)['input_sha256'], 'E9 input hashes changed')
    tables = [pd.read_csv(p, float_precision='round_trip') for p in paths[:8]]
    m, folds, features, added, base, oof, locked, mixed = tables
    ids = features.canonical_id.tolist()
    for frame in tables:
        c.require(len(frame) == frame.canonical_id.nunique() == 561, '561 unique canonical rows')
        c.require(frame.canonical_id.tolist() == ids, 'canonical ID order')
    c.require(m.source_split.value_counts().to_dict() == {'development_model_agnostic': 493, 'trial': 68}, 'development-only composition')
    c.require(set(m.task) == {'DM', 'MT', 'PG'}, 'task vocabulary')
    c.require(sorted(folds.fold_id.unique()) == [1, 2, 3, 4, 5], 'locked five folds')
    for frame in [oof, locked, mixed]:
        c.require(np.array_equal(folds.fold_id, frame.fold_id), 'fold identity')
    for key in ['task', 'label_bin', 'p_hallucination']:
        c.require(np.array_equal(m[key], mixed[key]), 'target metadata identity: ' + key)
    c.require(len(lock['features']) == 36 and features.columns.tolist() == ['canonical_id'] + lock['features'], 'feature order')
    c.require(base.columns.tolist() == ['canonical_id'] + lock['features'][:34], 'v2 order')
    c.require(np.array_equal(features.iloc[:, :35].to_numpy(), base.to_numpy()), 'first 34 numeric identity')
    c.require(np.array_equal(features[lock['new_features']].to_numpy(), added[lock['new_features']].to_numpy()), 'last two numeric identity')
    c.require(np.isfinite(features.iloc[:, 1:].to_numpy(float)).all(), 'finite features')
    m = m.copy()
    m['fold_id'] = folds.fold_id.to_numpy()
    metrics = c.diagnostics(m, oof.prediction.to_numpy())
    c.require(metrics['overall'] == {'n': 561, 'correct': 474, 'accuracy': 0.8449197860962567, 'spearman': 0.7816945786401444}, 'baseline score discrepancy')
    c.require(metrics['overall'] == saved['diagnostics']['all_rows']['E6-v3'], 'saved overall metrics')
    for group, saved_group in [('per_fold', 'per_fold'), ('per_task', 'per_task')]:
        for key, value in metrics[group].items():
            c.require(value == saved['diagnostics'][saved_group][key]['E6-v3'], 'saved subgroup metrics')
    runtime = {k: importlib.metadata.version(k) for k in lock['runtime']['packages']}
    c.require(runtime == lock['runtime']['packages'] and sys.version_info[:3] == (3, 11, 9), 'frozen runtime differs')
    report = {'status': 'PASS', 'population': 561, 'composition': m.source_split.value_counts().to_dict(),
              'fold_counts': {str(k): int(v) for k, v in folds.fold_id.value_counts().sort_index().items()},
              'feature_count': 36, 'numeric_and_order_identity': True, 'metrics': metrics,
              'rf_fits': 0, 'official_test_accessed': False, 'input_sha256': hashes, 'packages': runtime}
    return m, features, oof, lock, report


if __name__ == '__main__':
    print(json.dumps(verify()[-1], indent=2))
