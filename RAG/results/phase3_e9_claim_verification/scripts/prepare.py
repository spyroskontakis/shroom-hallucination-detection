"""Local preparation only. No model/API inference and no Random Forest fits."""
import os
import subprocess
from datetime import datetime, timezone
import e9_common as c
from verify_baseline import verify
from decomposer import MODEL, VERSION, PROMPT, SCHEMA


def main():
    metadata, features, oof, baseline, audit = verify()
    for name in ['config', 'scripts', 'claims', 'features', 'evaluation', 'reports', 'provenance', 'tests']:
        (c.OUT / name).mkdir(exist_ok=True)
    c.write_json(c.OUT / 'provenance/baseline_verification.json', audit)
    c.write_json(c.OUT / 'evaluation/baseline_metrics.json', audit['metrics'])
    config = {'baseline_features': baseline['features'], 'e9_a_features': baseline['features'] + c.A,
              'e9_b_features': baseline['features'] + c.A + c.B, 'random_forest': baseline['random_forest'],
              'runtime': baseline['runtime'], 'target': 'p_hallucination', 'threshold': .5,
              'spearman_round_decimals': 12, 'bootstrap_seed': 42, 'bootstrap_samples': 10000,
              'decomposer': {'model': MODEL, 'temperature': 0, 'prompt_version': VERSION, 'max_attempts': 3},
              'nli_model': 'MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli',
              'nli_revision': 'b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7',
              'minicheck_model': 'bespokelabs/Bespoke-MiniCheck-7B', 'minicheck_std_ddof': 0,
              'minicheck_unsupported_threshold': .5, 'reference_policy': {'DM': 'tgt', 'MT': 'tgt', 'PG': 'src'},
              'api_enabled_by_default': False, 'smoke_selection': 'first canonical_id sorted row per task',
              'selection': 'highest accuracy, then Spearman; exact tie prefers E9-A; no significance-based tuning'}
    c.write_json(c.OUT / 'config/run_config.json', config)
    c.write_json(c.OUT / 'config/decomposition_prompt.json', {'version': VERSION, 'system': PROMPT, 'schema': SCHEMA})
    # No text or labels are exported while API-blocked. Smoke selection uses task/ID only.
    available = bool(os.environ.get('OPENAI_API_KEY'))
    state = {'status': 'READY_FOR_SMOKE' if available else 'BLOCKED_DECOMPOSER_API',
             'reason': 'API key present; model access untested' if available else 'OPENAI_API_KEY unavailable in process environment',
             'utc': datetime.now(timezone.utc).isoformat(), 'baseline_verification': 'PASS',
             'e9_a': 'NOT_RUN', 'e9_b': 'NOT_STARTED_REQUIRES_E9_A',
             'rf_fits': 0, 'llm_calls': 0, 'cache_hits': 0, 'fallbacks': 0, 'minicheck_inferences': 0,
             'official_test_accessed': False,
             'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=c.ROOT, text=True).strip()}
    c.write_json(c.OUT / 'reports/execution_status.json', state)
    print(state['status'])


if __name__ == '__main__':
    main()
