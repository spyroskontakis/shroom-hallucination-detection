"""Pre-fit E9-A feature and reference audit; no RF/model/API execution."""
import json
from collections import defaultdict
import numpy as np
import pandas as pd
import e9_common as c
from verify_baseline import verify
from run_decomposition import frozen_check
from aggregates import nli


def main():
    frozen_check()
    metadata, base, _, lock, _ = verify()
    matrix = pd.read_csv(c.OUT / 'features/E9-A.csv', float_precision='round_trip')
    c.require(matrix.columns.tolist() == ['canonical_id'] + lock['features'] + c.A, '44-column order')
    c.require(np.array_equal(matrix[base.columns].to_numpy(), base.to_numpy()), 'baseline features unchanged')
    c.require(matrix.canonical_id.tolist() == metadata.canonical_id.tolist(), 'canonical ID order')
    claims = defaultdict(list)
    for line in (c.OUT / 'claims/full_claims.jsonl').read_text(encoding='utf-8').splitlines():
        item = json.loads(line)
        claims[item['canonical_id']].append(item['claim_text'])
    scores = defaultdict(list)
    for line in (c.OUT / 'features/nli_claim_audit.jsonl').read_text().splitlines():
        for score in json.loads(line)['scores']:
            scores[score['canonical_id']].append(score)
    pairs = [json.loads(line) for line in (c.OUT / 'features/nli_input_hashes.jsonl').read_text().splitlines()]
    c.require(len(pairs) == len({r['pair_id'] for r in pairs}) == sum(map(len, claims.values())), 'pair coverage')
    mapping = {r['pair_id']: r for r in pairs}
    for row in metadata.itertuples():
        ref = row.src if row.task == 'PG' else row.tgt
        for index, text in enumerate(claims[row.canonical_id]):
            pair = mapping[f'{row.canonical_id}:{index}']
            c.require(pair['reference_column'] == ('src' if row.task == 'PG' else 'tgt'), 'reference policy')
            c.require(pair['premise_sha256'] == c.hashlib.sha256(ref.encode()).hexdigest(), 'premise identity')
            c.require(pair['hypothesis_sha256'] == c.hashlib.sha256(text.encode()).hexdigest(), 'hypothesis identity')
    for row in matrix.itertuples():
        values = scores[row.canonical_id]
        c.require(len(values) == len(claims[row.canonical_id]) >= 1, 'claim score coverage')
        c.require([v['pair_id'] for v in values] == [f'{row.canonical_id}:{i}' for i in range(len(values))], 'claim score order')
        expected = nli([[v[k] for k in ['entailment', 'neutral', 'contradiction']] for v in values])
        c.require(np.array_equal(list(expected.values()), [getattr(row, k) for k in c.A]), 'exact aggregation')
    c.write_json(c.OUT / 'reports/E9-A_pre_fit_integrity.json', {'status': 'PASS', 'samples': 561,
        'features': 44, 'baseline_columns': 'exact numeric and order identity',
        'reference_policy': 'PASS', 'aggregations_reconstructed': 'PASS', 'rf_fits_at_audit': 0})
    print('E9-A pre-fit integrity PASS: 561 rows, 44 features, exact baseline and claim aggregates.')


if __name__ == '__main__':
    main()
