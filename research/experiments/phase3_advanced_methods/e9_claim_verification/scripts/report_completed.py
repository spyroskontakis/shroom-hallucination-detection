"""Build aggregate final reports after E9-A and the E9-B outcome are recorded."""
import json
from pathlib import Path
import e9_common as c


def table(metrics):
    lines = ['| Group | Correct / n | Accuracy | Spearman |', '|---|---:|---:|---:|']
    groups = [('Overall', metrics['overall'])]
    groups += [(k, v) for k, v in metrics['per_task'].items()]
    groups += [('Fold ' + k, v) for k, v in metrics['per_fold'].items()]
    for name, m in groups:
        lines.append(f"| {name} | {m['correct']}/{m['n']} | {m['accuracy']:.16f} | {m['spearman']} |")
    return '\n'.join(lines)


def main():
    d = c.read_json(c.OUT / 'reports/full_decomposition_stats.json')
    a = c.read_json(c.OUT / 'evaluation/E9-A_metrics.json')
    integrity = c.read_json(c.OUT / 'reports/E9-A_final_integrity.json')
    baseline = c.read_json(c.OUT / 'evaluation/baseline_metrics.json')
    c.require(d['status'] == 'PASS' and a['status'] == 'COMPLETED' and integrity['status'] == 'PASS', 'E9-A incomplete')
    b_path = c.OUT / 'evaluation/E9-B_metrics.json'
    b = c.read_json(b_path) if b_path.exists() else None
    preflight = c.read_json(c.OUT / 'reports/minicheck_preflight.json')
    status = 'PASS' if b else 'BLOCKED_MINICHECK_WITH_E9_A_COMPLETE'
    paired = a['paired_vs_e6_v3']
    text = f'''# E9 results — {status}

E9-A completed with exactly five Random Forest fits and 561 OOF predictions.
The frozen decomposer and Amendment 01 were unchanged. The accepted limitations
in claim atomicity/self-containment remain; no post-score tuning was performed.

## Full decomposition

Exactly {d['samples']} canonical samples, with {d['total_final_claims']} final claims.
Mean {d['mean_claims']}; median {d['median_claims']}; maximum {d['max_claims']}.
One-claim samples {d['samples_one_claim']}; two-claim samples {d['samples_two_claims']};
three-plus-claim samples {d['samples_three_plus_claims']}.
Fallbacks {d['fallback_count']}. API attempts {d['api_calls']}; successful responses
{d['successful_api_responses']}; additional attempts after first payload request
{d['retry_count']}. Sample-level cache reuse {d['sample_cache_hits']}; unique cached
payload reuse {d['unique_payload_cache_hits']}.

Input tokens {d['usage']['input_tokens']}; output tokens {d['usage']['output_tokens']};
total {d['usage']['total_tokens']}; provider-cached input tokens
{d['usage']['cached_input_tokens']}. Estimated incremental full-run API cost:
USD {d['estimated_cost_usd']:.8f}. This includes full-run validation attempts and
excludes previously paid smoke calls. HTTP 429 interrupted the initial invocation;
the user explicitly authorized continuation. Successful responses from an interrupted
row were replayed through the unchanged validator rather than purchased again.
Counts cover both invocations; initial HTTP failures are included in attempted calls.
Billing-ledger cost was not independently available.

## E6-v3 saved baseline

{table(baseline)}

## E9-A: 44 features

{table(a['metrics'])}

Corrections: {paired['corrections']}; regressions: {paired['regressions']};
net correct change: {paired['net_correct']}. Exact two-sided paired McNemar p:
{paired['mcnemar_exact_p']}. Accuracy difference: {paired['accuracy_difference']}.
Paired bootstrap percentile 95% CI: {paired['bootstrap_95_ci']} (accuracy units),
10,000 resamples, default_rng(42). These statistics were not used to tune the model.

## E9-B

'''
    if b:
        text += '49 features; five RF fits.\n\n' + table(b['metrics']) + '\n\n' + json.dumps(b['paired_vs_e6_v3'], indent=2) + '\n'
    else:
        text += 'BLOCKED_MINICHECK. ' + preflight['reason'] + '\n\nNo model substitution, MiniCheck inference, 49-column matrix or E9-B RF fit.\n'
    text += '''
## Integrity and stop

561 canonical IDs/order and original locked folds verified. All 36 baseline columns
are numerically/order-identical; claims are nonempty for every row. Requests contain
only hyp/task sample data. NLI input hashes verify DM/MT=tgt and PG=src with claim
as hypothesis. Every aggregate was reconstructed from saved claim probabilities.
Training records verify only training-row targets/features for each fit. No OOF
prediction is a feature. Baseline verification required zero refits.

The official 1,500-row test was not accessed, loaded, inspected, evaluated or used.
No historical E1-E8 file was modified. No threshold, feature, fold, RF configuration,
reference policy or decomposer change was made after results. No E9-C.
No commit or push. Exact changed paths are recorded in reports/FULL_RUN_FILES_CHANGED.md.
Row-level claims, NLI scores, features and OOF files remain local and ignored.
All findings are exploratory OOF results on the reused development pool.
'''
    (c.OUT / 'E9_RESULTS.md').write_text(text, encoding='utf-8')
    final = {'status': status, 'decomposition': d, 'E6-v3': baseline['overall'], 'E9-A': a,
             'E9-B': b or {'status': 'BLOCKED_MINICHECK', 'reason': preflight['reason']},
             'rf_fits': 5 + (5 if b else 0), 'baseline_refits': 0, 'leakage_checks': 'PASS',
             'official_test_accessed': False}
    c.write_json(c.OUT / 'reports/final_summary.json', final)
    print(json.dumps({'status': status, 'E9-A': a['metrics']['overall'], 'paired': paired}, indent=2))


if __name__ == '__main__':
    main()
