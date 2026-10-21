"""Fixed five-fit evaluation component. Call only after validated features exist."""
import importlib.metadata
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import e9_common as c
from verify_baseline import verify


def evaluate(matrix, variant):
    c.require(variant in ['E9-A', 'E9-B'], 'predefined variants only')
    metadata, baseline, old, lock, _ = verify()
    config = c.read_json(c.OUT / 'config/run_config.json')
    from run_decomposition import frozen_check
    frozen_check()
    freeze = c.read_json(c.OUT / f'features/{variant}_freeze.json')
    c.require(freeze['status'] == 'PASS' and freeze['samples'] == 561, 'feature extraction incomplete')
    c.require(c.sha(c.OUT / f'features/{variant}.csv') == freeze['features_sha256'], 'feature file changed')
    names = config['e9_a_features' if variant == 'E9-A' else 'e9_b_features']
    c.require(matrix.columns.tolist() == ['canonical_id'] + names, 'feature schema')
    c.require(matrix.canonical_id.tolist() == baseline.canonical_id.tolist(), '561 canonical IDs')
    c.require(np.array_equal(matrix[baseline.columns].to_numpy(), baseline.to_numpy()), '36 frozen columns differ')
    c.require(np.isfinite(matrix[names].to_numpy(float)).all(), 'finite features')
    c.require(config['random_forest'] == lock['random_forest'], 'RF configuration changed')
    for package, version in lock['runtime']['packages'].items():
        c.require(importlib.metadata.version(package) == version, 'runtime changed')
    if variant == 'E9-B':
        prior = c.read_json(c.OUT / 'evaluation/E9-A_metrics.json')
        c.require(prior['status'] == 'COMPLETED', 'E9-A must complete first')
        import pandas as pd
        a = pd.read_csv(c.OUT / 'features/E9-A.csv', float_precision='round_trip')
        c.require(np.array_equal(matrix[a.columns].to_numpy(), a.to_numpy()), '44 E9-A columns differ')
    # Exclusive run marker prevents accidental duplicate fits or rerunning observed results.
    c.write_json(c.OUT / f'evaluation/{variant}_started.json', {'expected_rf_fits': 5, 'feature_count': len(names)})
    predictions = np.full(561, np.nan)
    for fold in range(1, 6):
        train = metadata.fold_id.to_numpy() != fold
        valid = ~train
        c.require(set(metadata.loc[train, 'canonical_id']).isdisjoint(metadata.loc[valid, 'canonical_id']), 'training leakage')
        model = RandomForestRegressor(**config['random_forest'])
        c.require(model.get_params() == lock['random_forest'], 'RF defaults changed')
        c.write_json(c.OUT / f'evaluation/fit_{variant}_{fold}_started.json', {
            'fold': fold, 'train_ids': metadata.loc[train, 'canonical_id'].tolist(),
            'validation_ids': metadata.loc[valid, 'canonical_id'].tolist(), 'parameters': lock['random_forest'],
            'train_x_sha256': c.hashlib.sha256(matrix.loc[train, names].to_numpy(float).tobytes()).hexdigest(),
            'train_y_sha256': c.hashlib.sha256(metadata.loc[train, 'p_hallucination'].to_numpy(float).tobytes()).hexdigest(),
            'validation_x_sha256': c.hashlib.sha256(matrix.loc[valid, names].to_numpy(float).tobytes()).hexdigest()})
        # No fitted preprocessing or corpus statistics; train targets are indexed explicitly.
        model.fit(matrix.loc[train, names].to_numpy(float), metadata.loc[train, 'p_hallucination'].to_numpy(float))
        predictions[valid] = np.clip(model.predict(matrix.loc[valid, names].to_numpy(float)), 0, 1)
        c.write_json(c.OUT / f'evaluation/fit_{variant}_{fold}.json', {'fold': fold, 'completed': True})
        print(f'{variant}: RF fits {fold}/5 complete', flush=True)
    result = old[['canonical_id', 'fold_id']].copy()
    result['prediction'] = predictions
    with (c.OUT / f'evaluation/{variant}_oof.csv').open('x', newline='', encoding='utf-8') as handle:
        result.to_csv(handle, index=False)
    report = {'status': 'COMPLETED', 'rf_fits': 5, 'feature_count': len(names),
              'metrics': c.diagnostics(metadata, predictions),
              'paired_vs_e6_v3': c.paired(metadata.label_bin, old.prediction, predictions),
              'features_sha256': freeze['features_sha256'],
              'oof_sha256': c.sha(c.OUT / f'evaluation/{variant}_oof.csv')}
    verify()
    c.write_json(c.OUT / f'evaluation/{variant}_metrics.json', report)
    return report


if __name__ == '__main__':
    import argparse
    import pandas as pd
    parser = argparse.ArgumentParser()
    parser.add_argument('--variant', choices=['E9-A', 'E9-B'], required=True)
    args = parser.parse_args()
    matrix = pd.read_csv(c.OUT / f'features/{args.variant}.csv', float_precision='round_trip')
    print(evaluate(matrix, args.variant))
