"""Future one-shot E10 evaluation. No fits without explicit --run-rf and validated scores."""
import argparse
import sys
from factcg_common import HERE, FEATURE, require, read, sha, write, validate_inputs, validate_outputs
from return_to_local import verify_local

def evaluate():
    m, _ = validate_inputs()
    verify_local(m)
    # Existing local frozen evaluator utilities; no GPU dependency imports.
    sys.path.insert(0, str(HERE.parent / 'scripts'))
    from verify_baseline import verify
    import e9_common as c
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestRegressor
    metadata, baseline, old, lock, _ = verify()
    require(lock['random_forest'] == m['evaluation']['random_forest'], 'RF settings changed')
    require(lock['features'] == m['e6_features'], 'baseline schema changed')
    folder = HERE.parent / 'features/e10_return'
    freeze = read(folder / 'E10_freeze.json')
    require(freeze['status'] == 'PASS' and freeze['samples'] == 561 and freeze['feature_count'] == 37, 'E10 matrix incomplete')
    require(freeze['manifest_sha256'] == sha(HERE / 'GPU_RUN_MANIFEST.json'), 'E10 manifest mismatch')
    require(freeze['features_sha256'] == sha(folder / 'E10.csv') and
            freeze['gpu_output_sha256'] == sha(folder / 'factcg_scores.jsonl'), 'E10 hashes')
    scores = validate_outputs(folder / 'factcg_scores.jsonl', folder / 'FACTCG_GPU_REPORT.json')
    matrix = pd.read_csv(folder / 'E10.csv', float_precision='round_trip')
    names = m['e6_features'] + [FEATURE]
    require(matrix.columns.tolist() == ['canonical_id'] + names, '37-feature schema')
    require(matrix.canonical_id.tolist() == baseline.canonical_id.tolist(), 'canonical order')
    require(np.array_equal(matrix[baseline.columns].to_numpy(), baseline.to_numpy()), '36 baseline features changed')
    by_id = {r['canonical_id']: r['support_probability'] for r in scores}
    require(np.array_equal(matrix[FEATURE].to_numpy(), np.array([by_id[cid] for cid in matrix.canonical_id])), 'raw FactCG feature changed')
    require(np.isfinite(matrix[names].to_numpy(float)).all(), 'nonfinite matrix')
    # Fixed destination, exclusive marker: no rerun or alternate output directory.
    out = HERE.parent / 'evaluation/E10'
    out.mkdir(exist_ok=False)
    write(out / 'E10_started.json', dict(expected_rf_fits=5, samples=561, feature_count=37,
          features_sha256=sha(folder / 'E10.csv'), parameters=lock['random_forest']))
    predictions = np.full(561, np.nan)
    for fold in range(1, 6):
        train = metadata.fold_id.to_numpy() != fold
        valid = ~train
        require(train.any() and valid.any(), 'empty fold')
        model = RandomForestRegressor(**lock['random_forest'])
        require(model.get_params() == lock['random_forest'], 'RF defaults differ')
        write(out / f'fit_{fold}_started.json', dict(fold=fold,
              train_ids=metadata.loc[train, 'canonical_id'].tolist(),
              validation_ids=metadata.loc[valid, 'canonical_id'].tolist(), parameters=lock['random_forest']))
        model.fit(matrix.loc[train, names].to_numpy(float), metadata.loc[train, 'p_hallucination'].to_numpy(float))
        predictions[valid] = np.clip(model.predict(matrix.loc[valid, names].to_numpy(float)), 0, 1)
        write(out / f'fit_{fold}_completed.json', dict(completed=True, fold=fold))
    require(np.isfinite(predictions).all(), 'incomplete OOF predictions')
    result = old[['canonical_id', 'fold_id']].copy()
    result['prediction'] = predictions
    with (out / 'E10_oof.csv').open('x', encoding='utf-8', newline='') as f:
        result.to_csv(f, index=False)
    metrics = c.diagnostics(metadata, predictions)
    paired = c.paired(metadata.label_bin, old.prediction, predictions)
    current = metrics['overall']
    better = (current['accuracy'], current['spearman']) > (0.8449197860962567, 0.7816945786401444)
    report = dict(status='COMPLETED', rf_fits=5, feature_count=37, oof_predictions=561,
                  metrics=metrics, paired_vs_e6_v3=paired,
                  selected='E10' if better else 'E6-v3',
                  selection_rule='Accuracy first, Spearman on exact accuracy tie; exact tie retains E6-v3',
                  features_sha256=sha(folder / 'E10.csv'), oof_sha256=sha(out / 'E10_oof.csv'))
    verify()
    verify_local(m)
    write(out / 'E10_metrics.json', report)
    with (out / 'E10_RESULTS.md').open('x', encoding='utf-8') as f:
        import json
        f.write('# Frozen E10 results\n\n```json\n' + json.dumps(report, indent=2) + '\n```\n')
    print(report)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-rf', action='store_true', required=True,
                        help='Only after GPU scores have been validated and imported; runs exactly five fits once')
    parser.parse_args()
    evaluate()
