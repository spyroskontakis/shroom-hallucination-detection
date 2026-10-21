"""Amendment 01 smoke only: nine label-blind development rows, no downstream run."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
import pandas as pd
import decomposer as d

OUT = Path(__file__).resolve().parents[1]
ROOT = OUT.parents[2]
LOCAL = OUT / 'claims/smoke_nine_v2'
PRICING = {'input_per_million_usd': 2.5, 'cached_input_per_million_usd': 1.25,
           'output_per_million_usd': 10., 'source': 'https://developers.openai.com/api/docs/models/gpt-4o'}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write('\n')


def select_rows():
    path = ROOT / 'codex/canonical_human_development_manifest.csv'
    expected = json.loads((OUT / 'provenance/baseline_verification.json').read_text())['input_sha256'][path.relative_to(ROOT).as_posix()]
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError('Canonical manifest hash mismatch')
    frame = pd.read_csv(path, usecols=['canonical_id', 'source_split', 'task', 'hyp'], keep_default_na=False)
    assert len(frame) == frame.canonical_id.nunique() == 561
    dev = frame[frame.source_split == 'development_model_agnostic']
    assert len(dev) == 493
    selected = dev.sort_values('canonical_id').groupby('task', sort=True).head(3).sort_values(['task', 'canonical_id'])
    assert len(selected) == 9 and selected.task.value_counts().to_dict() == {'DM': 3, 'MT': 3, 'PG': 3}
    return selected[['canonical_id', 'task', 'hyp']].to_dict('records')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-api-calls', action='store_true')
    args = parser.parse_args()
    if not args.run_api_calls:
        raise SystemExit('API execution disabled')
    key = os.environ.get('OPENAI_API_KEY', '').strip()
    if not key:
        raise SystemExit('BLOCKED_DECOMPOSER_API: key unavailable')
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() == 'phase3-e9-claim-verification'
    assert d.MODEL == 'gpt-4o-2024-08-06' and d.VERSION == 'e9-hyp-only-semantic-v2'
    rows = select_rows()
    save(LOCAL / 'started.json', {'utc': datetime.now(timezone.utc).isoformat(), 'sample_count': 9,
        'max_calls': 27, 'max_attempts_per_row': 3, 'prompt_version': d.VERSION,
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'decomposer_sha256': hashlib.sha256(Path(d.__file__).read_bytes()).hexdigest(),
        'full_run_authorized': False})
    save(LOCAL / 'inputs.json', rows)
    counters = {'llm_calls': 0, 'cache_hits': 0, 'fallbacks': 0}
    responses = []
    results = []
    blocked = False
    for row in rows:
        value = {'hyp': row['hyp'], 'task': row['task']}
        request = d.payload(value)
        assert set(json.loads(request['messages'][1]['content'])) == {'hyp', 'task'}
        assert json.loads(request['messages'][1]['content']) == value
        assert request['model'] == d.MODEL and request['temperature'] == 0
        digest = d.cache_key(value)
        save(LOCAL / f"{row['canonical_id']}_request.json", {'payload': request, 'cache_hash': digest})

        def call(request):
            number = counters['llm_calls']
            assert request == d.payload(value) and number <= 27
            req = urllib.request.Request('https://api.openai.com/v1/chat/completions',
                data=json.dumps(request).encode(), headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
            try:
                with urllib.request.urlopen(req, timeout=45) as response:
                    raw = json.load(response)
            except urllib.error.HTTPError as error:
                save(LOCAL / f'call_{number:02d}_error.json', {'http_status': error.code})
                raise d.BlockedAPI('BLOCKED_DECOMPOSER_API: HTTP ' + str(error.code)) from None
            except (urllib.error.URLError, TimeoutError):
                save(LOCAL / f'call_{number:02d}_error.json', {'status': 'TRANSPORT_ERROR'})
                raise d.BlockedAPI('BLOCKED_DECOMPOSER_API: transport failure') from None
            save(LOCAL / f'call_{number:02d}_response.json', raw)
            responses.append({'task': row['task'], 'model': raw.get('model'), 'usage': raw.get('usage')})
            if raw.get('model') != d.MODEL:
                raise d.BlockedAPI('BLOCKED_DECOMPOSER_API: model mismatch')
            choice = raw['choices'][0]
            if choice.get('finish_reason') != 'stop' or choice['message'].get('refusal'):
                raise ValueError('Incomplete or refused response')
            return {'output': json.loads(choice['message']['content']), 'model_snapshot': raw['model'],
                    'response_id': raw.get('id'), 'system_fingerprint': raw.get('system_fingerprint')}

        try:
            record = d.decompose(value, LOCAL / 'cache', counters, call)
        except d.BlockedAPI as error:
            print(str(error), flush=True)
            blocked = True
            break
        result = {'canonical_id': row['canonical_id'], 'task': row['task'],
            'claim_count': len(record['claims']), 'decomposition_fallback': record['decomposition_fallback'],
            'decomposition_status': record['decomposition_status'], 'model': record['model_snapshot'],
            'cache_hash': digest}
        save(LOCAL / f"{row['canonical_id']}_claims.json", {'hyp': row['hyp'], **result,
            'claims': [{'claim_index': i, 'claim_text': text} for i, text in enumerate(record['claims'])]})
        results.append(result)
        print(json.dumps(result), flush=True)
    usage = {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0, 'cached_input_tokens': 0}
    for response in responses:
        u = response['usage']
        assert u and u['total_tokens'] == u['prompt_tokens'] + u['completion_tokens']
        usage['input_tokens'] += u['prompt_tokens']
        usage['output_tokens'] += u['completion_tokens']
        usage['total_tokens'] += u['total_tokens']
        usage['cached_input_tokens'] += (u.get('prompt_tokens_details') or {}).get('cached_tokens', 0)
    cost = ((usage['input_tokens'] - usage['cached_input_tokens']) * 2.5 + usage['cached_input_tokens'] * 1.25 + usage['output_tokens'] * 10.) / 1e6
    summary = {'status': 'BLOCKED' if blocked else 'AWAITING_SEMANTIC_REVIEW',
        'prompt_version': d.VERSION, 'counters': counters, 'successful_api_responses': len(responses),
        'results': results, 'usage': usage, 'pricing': PRICING, 'usage_priced_cost_usd': cost,
        'actual_billed_cost_usd': None, 'projected_561_cost_usd': cost / 9 * 561 if len(results) == 9 else None,
        'projection_assumption': 'Same observed per-sample usage including retries; small label-blind smoke estimate, not a budget guarantee.',
        'all_samples_have_claims': len(results) == 9 and all(r['claim_count'] >= 1 for r in results),
        'sample_retention': len(results), 'prompt_leakage_checks': 'PASS', 'official_test_accessed': False,
        'full_run_started': False, 'nli_calls': 0, 'minicheck_calls': 0, 'rf_fits': 0}
    save(LOCAL / 'summary.json', summary)
    public = {**summary, 'results': [{k: v for k, v in r.items() if k not in ['canonical_id', 'cache_hash']} for r in results]}
    save(OUT / 'reports/smoke_nine_api_results.json', public)
    print(json.dumps(public, indent=2), flush=True)


if __name__ == '__main__':
    main()
