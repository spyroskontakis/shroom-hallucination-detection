# E11-C closure attempt

FAIL: billing_hard_limit_reached. No retry Batch was created; four PG candidates remain pending. Existing results are unchanged.

```json
{
  "status": "FAIL_BLOCKED_BILLING",
  "protocol_sha256": "792bbe4ef1d0752e606c81dc511684f7bb0a051b2a5c24a937c49d7cb928f818",
  "prior_audit_sha256": "c10f573df6c6040e7139167530e192b8fe90e8a2da4ef07a27e6cdf6c3c6ec53",
  "preflight": "PASS",
  "tests_passed": 68,
  "batch_creation_attempts_this_continuation": 1,
  "api_http_status": 400,
  "api_error_code": "billing_hard_limit_reached",
  "retry_batch_id": null,
  "retry_requests_executed": 0,
  "retry_labels": [],
  "pending": 4,
  "pending_task": "PG",
  "by_task": {
    "DM": {
      "hallucination": 2781,
      "not_hallucination": 1149,
      "uncertain": 70
    },
    "MT": {
      "hallucination": 1046,
      "not_hallucination": 2951,
      "uncertain": 3
    },
    "PG": {
      "hallucination": 1284,
      "not_hallucination": 2676,
      "uncertain": 36
    }
  },
  "labels": {
    "hallucination": 5111,
    "not_hallucination": 6776,
    "uncertain": 109
  },
  "uncertain_percent": 0.9083333333333333,
  "definitive_labels": 11887,
  "retry_usage": {
    "input": 0,
    "output": 0,
    "reasoning": 0,
    "cached": 0,
    "estimated_cost_usd": 0
  },
  "combined_usage": {
    "input": 3869138,
    "output": 789550,
    "reasoning": 319672,
    "cached": 0,
    "usage_records": 11996,
    "mean_tokens_per_request": 388.3534511503835,
    "median_tokens_per_request": 371.0,
    "max_output_tokens_per_request": 526,
    "estimated_cost_usd": 15.633776
  },
  "preservation": {
    "frozen_protocol_unchanged": true,
    "pilot_files_unchanged": true,
    "original_production_artifacts_unchanged": true,
    "prior_successful_labels_unchanged": true,
    "frozen_preparation_unchanged": true,
    "row_level_files_git_ignored": true,
    "new_terminal_outcomes": 0
  },
  "actions": {
    "prompt_tuning": false,
    "manual_label_correction": false,
    "student_training": false,
    "development_evaluation": false,
    "official_test_access": false,
    "gpu_modal_run": false,
    "commit": false,
    "push": false,
    "fold_selection": false,
    "leakage_purge": false,
    "label_balancing": false,
    "contrastive_learning": false
  },
  "test_suites": [
    {
      "command": [
        "external-artifacts/local-21bcb77143c4/python.exe",
        "-m",
        "unittest",
        "discover",
        "-s",
        "RAG\\results\\phase3_e11_task_adaptation\\e11c",
        "-p",
        "test_e11c*.py",
        "-v"
      ],
      "exit_code": 0,
      "log": "E11C_PRODUCTION_CLOSURE_PREFLIGHT_TEST_1.txt",
      "sha256": "97ce3bfb703c6b1ca01fb3b53e91fa4b996bf576719aabe2dd78a25fab8996d7"
    },
    {
      "command": [
        "external-artifacts/local-21bcb77143c4/python.exe",
        "-m",
        "unittest",
        "discover",
        "-s",
        "RAG\\results\\phase3_e11_task_adaptation",
        "-p",
        "test_*.py",
        "-v"
      ],
      "exit_code": 0,
      "log": "E11C_PRODUCTION_CLOSURE_PREFLIGHT_TEST_2.txt",
      "sha256": "91a01d54ecb47af4eb06b013ea497919d04ce2435cc5ee7530c30175dbfb1c13"
    }
  ],
  "git_status_short": [
    "?? RAG/results/phase3_e11_task_adaptation/",
    "?? RAG/results/phase3_e9_claim_verification/",
    "?? modal_gpu_check.py"
  ],
  "next_step": "Restore API billing capacity before attempting closure again. Reconcile all submission intents and remote Batch state before any further POST. Reuse only the existing four-request file."
}
```
