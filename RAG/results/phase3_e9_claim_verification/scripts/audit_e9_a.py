"""Read-only audit of completed E9-A; no models, fitting or API requests."""
import json
from collections import defaultdict
import numpy as np
import pandas as pd
import e9_common as c
from verify_baseline import verify
from run_decomposition import frozen_check
from decomposer import payload, cache_key, validate
from aggregates import nli


def main():
    frozen_check()
    m, base, old, lock, baseline = verify()
    features = pd.read_csv(c.OUT / 'features/E9-A.csv', float_precision='round_trip')
    oof = pd.read_csv(c.OUT / 'evaluation/E9-A_oof.csv', float_precision='round_trip')
    report = c.read_json(c.OUT / 'evaluation/E9-A_metrics.json')
    freeze = c.read_json(c.OUT / 'features/E9-A_freeze.json')
    stats = c.read_json(c.OUT / 'reports/full_decomposition_stats.json')
    c.require(features.columns.tolist() == ['canonical_id'] + lock['features'] + c.A, '44-column order')
    c.require(np.array_equal(base.to_numpy(), features[base.columns].to_numpy()), 'baseline feature identity')
    c.require(oof.canonical_id.tolist() == m.canonical_id.tolist() and len(oof) == oof.canonical_id.nunique() == 561, 'OOF population/order')
    c.require(np.array_equal(oof.fold_id, m.fold_id), 'locked folds')
    c.require(c.sha(c.OUT / 'features/E9-A.csv') == freeze['features_sha256'] == report['features_sha256'], 'feature hash')
    c.require(c.sha(c.OUT / 'evaluation/E9-A_oof.csv') == report['oof_sha256'], 'OOF hash')
    c.require(c.diagnostics(m, oof.prediction.to_numpy()) == report['metrics'], 'saved metrics')
    c.require(c.sha(c.OUT / 'claims/full_claims.jsonl') == stats['full_claims_sha256'], 'claims hash')
    claims = [json.loads(line) for line in (c.OUT / 'claims/full_claims.jsonl').read_text(encoding='utf-8').splitlines()]
    by_id = defaultdict(list)
    for row in claims:
        by_id[row['canonical_id']].append(row)
    expected_pairs = {}
    for row in m.itertuples():
        value = {'hyp': row.hyp, 'task': row.task}
        digest = cache_key(value)
        request = c.read_json(c.OUT / f'claims/full_run/requests/{digest}.json')
        c.require(request == payload(value), 'hyp/task-only request')
        cached = c.read_json(c.OUT / f'claims/cache/{digest}.json')
        want = [row.hyp] if cached['decomposition_fallback'] else validate(cached['raw_output'], row.hyp)
        actual = by_id[row.canonical_id]
        c.require([x['claim_index'] for x in actual] == list(range(len(want))) and [x['claim_text'] for x in actual] == want and len(want) >= 1, 'claim coverage')
        ref = row.src if row.task == 'PG' else row.tgt
        for index, text in enumerate(want):
            expected_pairs[f'{row.canonical_id}:{index}'] = {
                'pair_id': f'{row.canonical_id}:{index}', 'canonical_id': row.canonical_id,
                'reference_column': 'src' if row.task == 'PG' else 'tgt',
                'premise_sha256': c.hashlib.sha256(ref.encode()).hexdigest(),
                'hypothesis_sha256': c.hashlib.sha256(text.encode()).hexdigest()}
    inputs = [json.loads(line) for line in (c.OUT / 'features/nli_input_hashes.jsonl').read_text().splitlines()]
    c.require(len(inputs) == len(expected_pairs) and {r['pair_id']: r for r in inputs} == expected_pairs, 'task reference policy/pair direction')
    scores = defaultdict(list)
    truncations = []
    for line in (c.OUT / 'features/nli_claim_audit.jsonl').read_text().splitlines():
        record = json.loads(line)
        truncations.extend(record['truncation'])
        for score in record['scores']:
            scores[score['canonical_id']].append(score)
    for row in features.itertuples():
        s = scores[row.canonical_id]
        c.require(len(s) == len(by_id[row.canonical_id]), 'scored claim coverage')
        c.require([x['pair_id'] for x in s] == [f'{row.canonical_id}:{i}' for i in range(len(s))], 'score order')
        aggregate = nli([[x[k] for k in ['entailment', 'neutral', 'contradiction']] for x in s])
        c.require(np.array_equal(np.array(list(aggregate.values())), np.array([getattr(row, k) for k in c.A])), 'aggregate definition identity')
    folds = []
    for fold in range(1, 6):
        started = c.read_json(c.OUT / f'evaluation/fit_E9-A_{fold}_started.json')
        done = c.read_json(c.OUT / f'evaluation/fit_E9-A_{fold}.json')
        train, valid = m.fold_id != fold, m.fold_id == fold
        c.require(started['train_ids'] == m.loc[train, 'canonical_id'].tolist() and started['validation_ids'] == m.loc[valid, 'canonical_id'].tolist(), 'fold split')
        c.require(started['parameters'] == lock['random_forest'] and done['completed'], 'frozen RF and completion')
        names = lock['features'] + c.A
        c.require(started['train_y_sha256'] == c.hashlib.sha256(m.loc[train, 'p_hallucination'].to_numpy(float).tobytes()).hexdigest(), 'training-only target')
        c.require(started['train_x_sha256'] == c.hashlib.sha256(features.loc[train, names].to_numpy(float).tobytes()).hexdigest(), 'training features')
        c.require(started['validation_x_sha256'] == c.hashlib.sha256(features.loc[valid, names].to_numpy(float).tobytes()).hexdigest(), 'validation features')
        folds.append(fold)
    audit = {'status': 'PASS', 'canonical_rows': 561, 'claim_count': len(claims), 'features': 44,
             'baseline_features_numeric_order': 'PASS', 'locked_folds': 'PASS', 'hyp_task_only_payloads': 'PASS',
             'reference_policy_direction': 'PASS', 'claim_aggregation': 'PASS', 'training_only_targets': 'PASS',
             'rf_fits': len(folds), 'oof_predictions': len(oof), 'official_test_accessed': False,
             'nli_truncated_pairs': sum(bool(t['truncated']) for t in truncations),
             'baseline': baseline['metrics']['overall'], 'semantic_limitations': 'Accepted frozen smoke limitations; no semantic retuning'}
    c.write_json(c.OUT / 'reports/E9-A_final_integrity.json', audit)
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()
