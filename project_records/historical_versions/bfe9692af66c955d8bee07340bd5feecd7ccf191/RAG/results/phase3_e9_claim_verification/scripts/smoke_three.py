"""Exactly three development-only API requests; no retries or downstream execution."""
import argparse
import copy
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
LOCAL = OUT / 'claims/smoke_three_v1'
VERSION = 'e9-hyp-only-v1-indexed-smoke'
SCHEMA = copy.deepcopy(d.SCHEMA)
ITEM = SCHEMA['properties']['claims']['items']
ITEM['properties']['claim_index'] = {'type': 'integer'}
ITEM['required'].append('claim_index')
PRICING = {'input_per_million_usd': 2.5, 'cached_input_per_million_usd': 1.25,
           'output_per_million_usd': 10., 'source': 'https://developers.openai.com/api/docs/models/gpt-4o'}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write('\n')


def build_request(value):
    request = d.payload(value)
    request['response_format']['json_schema']['schema'] = SCHEMA
    request['messages'][0]['content'] += '\nSet claim_index to consecutive integers starting at zero, in claim order.'
    assert json.loads(request['messages'][1]['content']) == value
    assert set(value) == {'hyp', 'task'}
    assert request['model'] == 'gpt-4o-2024-08-06' and request['temperature'] == 0
    return request


def validate_indexed(output, hyp):
    claims = output['claims']
    if not isinstance(claims, list):
        raise ValueError('Claims array required')
    for index, claim in enumerate(claims):
        if type(claim.get('claim_index')) is not int or claim['claim_index'] != index:
            raise ValueError('Invalid claim_index')
    unindexed = copy.deepcopy(output)
    for claim in unindexed['claims']:
        del claim['claim_index']
    return d.validate(unindexed, hyp)


def select_rows():
    path = ROOT / 'codex/canonical_human_development_manifest.csv'
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    expected = json.loads((OUT / 'provenance/baseline_verification.json').read_text())['input_sha256'][path.relative_to(ROOT).as_posix()]
    if digest != expected:
        raise ValueError('Canonical manifest hash mismatch')
    # Labels and reference columns are not materialized. Split and ID are local selection metadata.
    frame = pd.read_csv(path, usecols=['canonical_id', 'source_split', 'task', 'hyp'], keep_default_na=False)
    assert len(frame) == frame.canonical_id.nunique() == 561
    dev = frame[frame.source_split == 'development_model_agnostic']
    assert len(dev) == 493
    selected = dev.sort_values('canonical_id').groupby('task', sort=True).head(1).sort_values('task')
    assert len(selected) == 3 and set(selected.task) == {'DM', 'MT', 'PG'}
    return selected[['canonical_id', 'task', 'hyp']].to_dict('records')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-api-calls', action='store_true')
    args = parser.parse_args()
    if not args.run_api_calls:
        raise SystemExit('API execution disabled')
    key = os.environ.get('OPENAI_API_KEY', '').strip()
    if not key:
        raise SystemExit('BLOCKED_DECOMPOSER_API: missing key')
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() == 'phase3-e9-claim-verification'
    rows = select_rows()
    # Exclusive marker prevents accidental repetition of billable calls.
    save(LOCAL / 'started.json', {'utc': datetime.now(timezone.utc).isoformat(), 'max_calls': 3,
                                 'prompt_version': VERSION, 'retries': 0, 'full_run_authorized': False})
    save(LOCAL / 'inputs.json', rows)
    results = []
    attempts = 0
    blocked = False
    for row in rows:
        request = build_request({'hyp': row['hyp'], 'task': row['task']})
        digest = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
        save(LOCAL / f"{row['task']}_request.json", {'cache_hash': digest, 'payload': request})
        req = urllib.request.Request('https://api.openai.com/v1/chat/completions',
            data=json.dumps(request).encode(), headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
        attempts += 1
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                raw = json.load(response)
        except urllib.error.HTTPError as error:
            save(LOCAL / f"{row['task']}_error.json", {'http_status': error.code, 'api_attempt': attempts})
            blocked = True
            break
        except (urllib.error.URLError, TimeoutError):
            save(LOCAL / f"{row['task']}_error.json", {'status': 'TRANSPORT_ERROR', 'api_attempt': attempts})
            blocked = True
            break
        # Persist raw successful responses immediately; never persist request headers.
        save(LOCAL / f"{row['task']}_response.json", raw)
        result = {'task': row['task'], 'canonical_id': row['canonical_id'], 'model': raw.get('model'),
                  'usage': raw.get('usage'), 'claim_count': None, 'json_parsed': False,
                  'structural_valid': False, 'at_least_one_valid_claim': False, 'cache_hash': digest}
        if raw.get('model') != d.MODEL:
            result['error'] = 'MODEL_MISMATCH'
            results.append(result)
            blocked = True
            break
        try:
            choice = raw['choices'][0]
            if choice['finish_reason'] != 'stop' or choice['message'].get('refusal'):
                raise ValueError('Refused or incomplete response')
            output = json.loads(choice['message']['content'])
            result['json_parsed'] = True
            claims = validate_indexed(output, row['hyp'])
            result.update(claim_count=len(claims), structural_valid=True, at_least_one_valid_claim=bool(claims))
            save(LOCAL / f"{row['task']}_parsed.json", output)
        except (ValueError, KeyError, TypeError):
            result['error'] = 'INVALID_OUTPUT'
        results.append(result)
        print(json.dumps({'task': row['task'], 'model': result['model'], 'claim_count': result['claim_count']}), flush=True)
    usage = {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0, 'cached_input_tokens': 0}
    for result in results:
        u = result['usage'] or {}
        usage['input_tokens'] += u.get('prompt_tokens', 0)
        usage['output_tokens'] += u.get('completion_tokens', 0)
        usage['total_tokens'] += u.get('total_tokens', 0)
        usage['cached_input_tokens'] += (u.get('prompt_tokens_details') or {}).get('cached_tokens', 0)
    cost = ((usage['input_tokens'] - usage['cached_input_tokens']) * 2.5 + usage['cached_input_tokens'] * 1.25 + usage['output_tokens'] * 10.) / 1e6
    summary = {'status': 'BLOCKED' if blocked else 'AWAITING_SEMANTIC_REVIEW', 'api_calls': attempts,
               'successful_api_responses': len(results), 'results': results, 'usage': usage, 'pricing': PRICING,
               'usage_priced_cost_usd': cost, 'actual_billed_cost_usd': None,
               'cost_note': 'Calculated from actual returned usage and standard list rates; billing ledger not accessed.',
               'projected_561_cost_usd': cost / 3 * 561 if len(results) == 3 else None,
               'projection_assumption': 'Same mean token usage and cache fraction; one request per sample, no retries.',
               'prompt_leakage_check': 'PASS', 'official_test_accessed': False,
               'full_decomposition': False, 'nli_calls': 0, 'minicheck_calls': 0, 'rf_fits': 0}
    save(LOCAL / 'summary.json', summary)
    # Public aggregate report excludes canonical IDs, hypotheses and claim text.
    public = {**summary, 'results': [{k: v for k, v in r.items() if k not in ['canonical_id', 'cache_hash']} for r in results]}
    save(OUT / 'reports/smoke_three_api_results.json', public)
    print(json.dumps(public, indent=2), flush=True)


if __name__ == '__main__':
    main()
