# E11-C rescue attempt

FAIL: API returned billing_hard_limit_reached. No retry Batch or new labels; four PG candidates remain pending.

```json
{
  "status": "FAIL_BLOCKED_BILLING",
  "protocol_sha256": "792bbe4ef1d0752e606c81dc511684f7bb0a051b2a5c24a937c49d7cb928f818",
  "billing_provenance": "rescue retry attempted with alternate API billing project/account as supplied by user; Batch creation rejected; no labeling executed",
  "api_error": "billing_hard_limit_reached",
  "batch_creation_attempts": 1,
  "retry_batch_id": null,
  "retry_requests_executed": 0,
  "returned_labels": [],
  "pending": 4,
  "pending_task": "PG",
  "labels": {
    "hallucination": 5111,
    "not_hallucination": 6776,
    "uncertain": 109
  },
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
  "uncertain_percent": 0.9083333333333333,
  "definitive_labels": 11887,
  "total_frozen_candidates": 12000,
  "terminal_outcomes": 11996,
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
  "preflight": "PASS",
  "tests_passed": 68,
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
      "log": "E11C_PRODUCTION_RESCUE_PREFLIGHT_TEST_1.txt",
      "sha256": "d65e32a0a206bfa11e8bad45af9908b0d5b2de16b6bd4fbe56ee19203160f6b5"
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
      "log": "E11C_PRODUCTION_RESCUE_PREFLIGHT_TEST_2.txt",
      "sha256": "e79c243349dc7902c4a1e148fbdbf519e28cb6e1d5b37f369f86da5986584106"
    }
  ],
  "preservation": {
    "frozen_protocol_unchanged": true,
    "frozen_preparation_unchanged": true,
    "pilot_artifacts_unchanged": true,
    "original_production_artifacts_unchanged": true,
    "prior_11996_terminal_outcomes_unchanged": true,
    "row_level_artifacts_git_ignored": true
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
  "git_status_short": [
    "?? RAG/results/phase3_e11_task_adaptation/",
    "?? RAG/results/phase3_e9_claim_verification/",
    "?? modal_gpu_check.py"
  ],
  "next_step": "An API credential with usable billing capacity is still required. Reconcile the new rescue upload and creation intents before another attempt; never resubmit the original production requests."
}
```
