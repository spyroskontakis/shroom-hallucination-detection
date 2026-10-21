"""Execute the frozen decomposer on canonical hyp/task only; resumable persistent cache."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import threading
import time
import re
import urllib.error
import urllib.request
from uuid import uuid4
import numpy as np
import pandas as pd
import decomposer as d

OUT = Path(__file__).resolve().parents[1]
ROOT = OUT.parents[2]
LOCAL = OUT / 'claims/full_run'
CACHE = OUT / 'claims/cache'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')


def frozen_check():
    frozen = read(OUT / 'config/smoke_multi12_selection.json')['frozen_sha256']
    for rel, expected in frozen.items():
        if sha(OUT / rel) != expected:
            raise ValueError('Frozen file changed: ' + rel)
    assert d.MODEL == 'gpt-4o-2024-08-06' and d.VERSION == 'e9-hyp-only-semantic-v2'
    return frozen


def load_rows():
    path = ROOT / 'codex/canonical_human_development_manifest.csv'
    expected = read(OUT / 'provenance/baseline_verification.json')['input_sha256'][path.relative_to(ROOT).as_posix()]
    assert sha(path) == expected
    frame = pd.read_csv(path, usecols=['canonical_id', 'source_split', 'task', 'hyp'], keep_default_na=False)
    assert len(frame) == frame.canonical_id.nunique() == 561
    assert frame.source_split.value_counts().to_dict() == {'development_model_agnostic': 493, 'trial': 68}
    assert set(frame.task) == {'DM', 'MT', 'PG'}
    return frame[['canonical_id', 'task', 'hyp']].to_dict('records')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-api-calls', action='store_true')
    args = parser.parse_args()
    if not args.run_api_calls:
        raise SystemExit('API calls disabled')
    key = os.environ.get('OPENAI_API_KEY', '').strip()
    if not key:
        raise SystemExit('BLOCKED_DECOMPOSER_API: missing key')
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() == 'phase3-e9-claim-verification'
    if (OUT / 'claims/full_claims.jsonl').exists():
        raise SystemExit('Full claims already exist; refusing to rerun')
    frozen = frozen_check()
    rows = load_rows()
    groups = {}
    for row in rows:
        value = {'hyp': row['hyp'], 'task': row['task']}
        groups.setdefault(d.cache_key(value), []).append(row)
    CACHE.mkdir(parents=True, exist_ok=True)
    # Import only same-version, same-payload caches. No old v1 responses qualify.
    imported = 0
    for digest, group in groups.items():
        dest = CACHE / (digest + '.json')
        for directory in ['smoke_nine_v2', 'smoke_multi12_v2']:
            old = OUT / f'claims/{directory}/cache/{digest}.json'
            if old.exists():
                record = read(old)
                assert record['prompt_version'] == d.VERSION and record['model_snapshot'] == d.MODEL
                if dest.exists():
                    assert read(dest) == record, 'Conflicting frozen cache entries'
                else:
                    save(dest, record)
                    imported += 1
    start = LOCAL / 'started.json'
    if not start.exists():
        save(start, {'utc': datetime.now(timezone.utc).isoformat(), 'samples': 561,
                     'unique_payloads': len(groups), 'imported_smoke_caches': imported,
                     'frozen_sha256': frozen, 'workers': 4, 'model': d.MODEL, 'temperature': 0,
                     'max_attempts_per_unique_payload': 3, 'human_authorized_full_run': True})
    else:
        assert read(start)['frozen_sha256'] == frozen
    # User-authorized resume: serialize transport to reduce rate pressure. The
    # frozen per-row prompt, validation and three-attempt policy remain untouched.
    save(LOCAL / f'resume_{uuid4().hex}.json', {'utc': datetime.now(timezone.utc).isoformat(),
        'workers': 1, 'transport_spacing_seconds': 1,
        'frozen_sha256': frozen, 'reason': 'Explicit user continuation after HTTP 429'})
    prior_responses = {}
    for event_path in sorted((LOCAL / 'events').glob('*_response.json')):
        event = read(event_path)
        prior_responses.setdefault(event['cache_hash'], []).append(event)
    for events in prior_responses.values():
        events.sort(key=lambda e: e['utc'])
    aborted = threading.Event()

    def worker(digest, group):
        value = {'hyp': group[0]['hyp'], 'task': group[0]['task']}
        request = d.payload(value)
        assert request['model'] == d.MODEL and request['temperature'] == 0
        assert len(request['messages']) == 2 and json.loads(request['messages'][1]['content']) == value
        assert set(value) == {'hyp', 'task'}
        path = LOCAL / f'requests/{digest}.json'
        if path.exists():
            assert read(path) == request
        else:
            save(path, request)
        counters = {'llm_calls': 0, 'cache_hits': 0, 'fallbacks': 0}
        replay = iter(prior_responses.get(digest, []))

        def caller(payload):
            if aborted.is_set():
                raise d.BlockedAPI('BLOCKED_DECOMPOSER_API: stopped after availability failure')
            assert payload == request
            # Replay completed responses for an interrupted uncached row through
            # the unchanged validator; do not buy repeats or reset its attempts.
            previous = next(replay, None)
            if previous is not None:
                raw = previous['raw']
                assert raw['model'] == d.MODEL
                choice = raw['choices'][0]
                if choice.get('finish_reason') != 'stop' or choice['message'].get('refusal'):
                    raise ValueError('Incomplete or refused row output')
                return {'output': json.loads(choice['message']['content']), 'model_snapshot': raw['model'],
                        'response_id': raw.get('id'), 'system_fingerprint': raw.get('system_fingerprint')}
            time.sleep(1)
            event_id = uuid4().hex
            event = {'cache_hash': digest, 'attempt_within_invocation': counters['llm_calls'],
                     'utc': datetime.now(timezone.utc).isoformat()}
            save(LOCAL / f'events/{event_id}_started.json', event)
            req = urllib.request.Request('https://api.openai.com/v1/chat/completions',
                data=json.dumps(payload).encode(), headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
            try:
                with urllib.request.urlopen(req, timeout=90) as response:
                    raw = json.load(response)
            except urllib.error.HTTPError as error:
                details = {}
                try:
                    body = json.loads(error.read()).get('error', {})
                    for field in ['type', 'code']:
                        value = body.get(field)
                        if isinstance(value, str) and re.fullmatch(r'[a-zA-Z_0-9-]{1,80}', value):
                            details[field] = value
                except (ValueError, AttributeError):
                    pass
                save(LOCAL / f'events/{event_id}_error.json', {**event, 'http_status': error.code, 'details': details})
                aborted.set()
                raise d.BlockedAPI('BLOCKED_DECOMPOSER_API: HTTP ' + str(error.code)) from None
            except (urllib.error.URLError, TimeoutError):
                save(LOCAL / f'events/{event_id}_error.json', {**event, 'status': 'transport unavailable'})
                aborted.set()
                raise d.BlockedAPI('BLOCKED_DECOMPOSER_API: transport unavailable') from None
            save(LOCAL / f'events/{event_id}_response.json', {**event, 'raw': raw})
            if raw.get('model') != d.MODEL:
                aborted.set()
                raise d.BlockedAPI('BLOCKED_DECOMPOSER_API: model snapshot mismatch')
            choice = raw['choices'][0]
            if choice.get('finish_reason') != 'stop' or choice['message'].get('refusal'):
                raise ValueError('Incomplete or refused row output')
            return {'output': json.loads(choice['message']['content']), 'model_snapshot': raw['model'],
                    'response_id': raw.get('id'), 'system_fingerprint': raw.get('system_fingerprint')}

        record = d.decompose(value, CACHE, counters, caller)
        return digest, record, counters

    outputs = {}
    total = {'llm_calls': 0, 'cache_hits': 0, 'fallbacks': 0}
    completed = 0
    with ThreadPoolExecutor(max_workers=1) as pool:
        futures = {pool.submit(worker, digest, group): digest for digest, group in groups.items()}
        for future in as_completed(futures):
            try:
                digest, record, counters = future.result()
            except d.BlockedAPI as error:
                aborted.set()
                for pending in futures:
                    pending.cancel()
                raise SystemExit(str(error)) from None
            outputs[digest] = record
            size = len(groups[digest])
            total['llm_calls'] += counters['llm_calls']
            total['cache_hits'] += counters['cache_hits'] + size - 1
            total['fallbacks'] += record['decomposition_fallback'] * size
            completed += size
            if completed % 20 == 0 or completed == 561:
                print(f'Decomposition: {completed}/561 samples; API attempts this invocation {total["llm_calls"]}; fallback samples {total["fallbacks"]}', flush=True)
    claim_rows = []
    counts = []
    for row in rows:
        digest = d.cache_key({'hyp': row['hyp'], 'task': row['task']})
        record = outputs[digest]
        expected = [row['hyp']] if record['decomposition_fallback'] else d.validate(record['raw_output'], row['hyp'])
        assert record['claims'] == expected and len(expected) >= 1
        counts.append(len(expected))
        for index, text in enumerate(expected):
            claim_rows.append({'canonical_id': row['canonical_id'], 'task': row['task'], 'claim_index': index,
                'claim_text': text, **{k: record[k] for k in ['decomposition_status', 'decomposition_fallback',
                'model_snapshot', 'prompt_version', 'cache_hash', 'hyp_sha256']}})
    assert list(dict.fromkeys(r['canonical_id'] for r in claim_rows)) == [r['canonical_id'] for r in rows]
    assert len(set(r['canonical_id'] for r in claim_rows)) == 561
    frozen_check()
    with (OUT / 'claims/full_claims.jsonl').open('x', encoding='utf-8') as handle:
        for record in claim_rows:
            handle.write(json.dumps(record, ensure_ascii=False) + '\n')
    events = [read(path) for path in sorted((LOCAL / 'events').glob('*_response.json'))]
    usage = {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0, 'cached_input_tokens': 0}
    for event in events:
        raw = event['raw']
        assert raw['model'] == d.MODEL
        u = raw['usage']
        assert u['total_tokens'] == u['prompt_tokens'] + u['completion_tokens']
        usage['input_tokens'] += u['prompt_tokens']
        usage['output_tokens'] += u['completion_tokens']
        usage['total_tokens'] += u['total_tokens']
        usage['cached_input_tokens'] += (u.get('prompt_tokens_details') or {}).get('cached_tokens', 0)
    calls = len(list((LOCAL / 'events').glob('*_started.json')))
    first_calls = len(set(e['cache_hash'] for e in events))
    summary = {'status': 'PASS', 'samples': 561, 'unique_payloads': len(groups), 'total_final_claims': sum(counts),
        'mean_claims': float(np.mean(counts)), 'median_claims': float(np.median(counts)), 'max_claims': max(counts),
        'samples_one_claim': counts.count(1), 'samples_two_claims': counts.count(2),
        'samples_three_plus_claims': sum(n >= 3 for n in counts), 'fallback_count': total['fallbacks'],
        'api_calls': calls, 'successful_api_responses': len(events), 'retry_count': calls - first_calls,
        'sample_cache_hits': 561 - first_calls, 'unique_payload_cache_hits': len(groups) - first_calls,
        'usage': usage, 'estimated_cost_usd': ((usage['input_tokens'] - usage['cached_input_tokens']) * 2.5 + usage['cached_input_tokens'] * 1.25 + usage['output_tokens'] * 10.) / 1e6,
        'cost_scope': 'New full-run calls including retries; prior smoke costs excluded; cache hits incur no new call.',
        'actual_billed_cost_usd': None, 'model': d.MODEL, 'temperature': 0, 'prompt_version': d.VERSION,
        'canonical_ids_order': 'PASS', 'all_samples_nonempty': True, 'leakage_checks': 'PASS',
        'official_test_accessed': False, 'full_claims_sha256': sha(OUT / 'claims/full_claims.jsonl')}
    save(OUT / 'reports/full_decomposition_stats.json', summary)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
