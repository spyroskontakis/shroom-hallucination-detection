"""Explicit API opt-in; smoke first. Write only local, ignored claim artifacts."""
import argparse
import json
import os
import pandas as pd
import e9_common as c
from decomposer import BlockedAPI, decompose, cache_key
from verify_baseline import verify


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-api-calls', action='store_true')
    parser.add_argument('--mode', choices=['smoke', 'full'], default='smoke')
    args = parser.parse_args()
    if not args.run_api_calls:
        raise SystemExit('API execution disabled; explicit --run-api-calls required')
    if not os.environ.get('OPENAI_API_KEY'):
        raise SystemExit('BLOCKED_DECOMPOSER_API: OPENAI_API_KEY unavailable')
    verify()
    # Discard all evaluation metadata before constructing any model input.
    rows = pd.read_csv(c.CANONICAL, usecols=['canonical_id', 'task', 'hyp'], keep_default_na=False)
    c.require(len(rows) == rows.canonical_id.nunique() == 561, 'canonical population')
    smoke = rows.sort_values('canonical_id').groupby('task', sort=True).head(1)
    if args.mode == 'smoke':
        rows = smoke
    else:
        review = c.read_json(c.OUT / 'claims/smoke_review.json')
        expected = {r.canonical_id: cache_key({'hyp': r.hyp, 'task': r.task}) for r in smoke.itertuples()}
        c.require(review['status'] == 'PASS' and review['cache_hashes'] == expected,
                  'label-blind smoke semantic review required before full decomposition')
    counters = {'llm_calls': 0, 'cache_hits': 0, 'fallbacks': 0}
    output = []
    try:
        for row in rows.itertuples():
            record = decompose({'hyp': row.hyp, 'task': row.task}, c.OUT / 'claims/cache', counters)
            for index, text in enumerate(record['claims']):
                output.append({'canonical_id': row.canonical_id, 'task': row.task, 'claim_index': index,
                    'claim_text': text, **{k: record[k] for k in ['decomposition_status', 'decomposition_fallback',
                    'model_snapshot', 'prompt_version', 'cache_hash', 'hyp_sha256']}})
    except BlockedAPI as error:
        print(str(error))
        print(json.dumps(counters))
        raise SystemExit(2)
    c.require(set(r['canonical_id'] for r in output) == set(rows.canonical_id), 'lost claim row')
    path = c.OUT / f'claims/{args.mode}_claims.jsonl'
    with path.open('x', encoding='utf-8') as handle:
        for record in output:
            handle.write(json.dumps(record, ensure_ascii=False) + '\n')
    c.write_json(c.OUT / f'claims/{args.mode}_counts.json', counters)
    print(json.dumps(counters))


if __name__ == '__main__':
    main()
