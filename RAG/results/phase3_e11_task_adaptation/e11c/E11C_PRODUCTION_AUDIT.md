# E11-C full production audit

Status: FAIL_BLOCKED_BILLING
Protocol SHA256: `792bbe4ef1d0752e606c81dc511684f7bb0a051b2a5c24a937c49d7cb928f818`

300 pilot + 11,700 production = 12,000 unique candidates.

| Task | hallucination | not_hallucination | uncertain |
|---|---:|---:|---:|
| DM | 2781 | 1149 | 70 |
| MT | 1046 | 2951 | 3 |
| PG | 1284 | 2676 | 36 |

```json
{
  "status": "FAIL_BLOCKED_BILLING",
  "protocol_sha256": "792bbe4ef1d0752e606c81dc511684f7bb0a051b2a5c24a937c49d7cb928f818",
  "requested_teacher_model": "gpt-5.6-sol",
  "returned_model_ids": [
    "gpt-5.6-sol"
  ],
  "reasoning_effort": "medium",
  "batches": [
    {
      "stage": "pilot",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 300,
        "completed": 300,
        "failed": 0
      },
      "created_at": 1790663902,
      "completed_at": 1790664067,
      "expired_at": null,
      "cancelled_at": null
    },
    {
      "stage": "production",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 500,
        "completed": 500,
        "failed": 0
      },
      "created_at": 1790855238,
      "completed_at": 1790855434,
      "expired_at": null,
      "cancelled_at": null
    },
    {
      "stage": "production",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 500,
        "completed": 500,
        "failed": 0
      },
      "created_at": 1790855245,
      "completed_at": 1790855370,
      "expired_at": null,
      "cancelled_at": null
    },
    {
      "stage": "production",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 500,
        "completed": 500,
        "failed": 0
      },
      "created_at": 1790855250,
      "completed_at": 1790855392,
      "expired_at": null,
      "cancelled_at": null
    },
    {
      "stage": "production",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 500,
        "completed": 500,
        "failed": 0
      },
      "created_at": 1790855256,
      "completed_at": 1790855409,
      "expired_at": null,
      "cancelled_at": null
    },
    {
      "stage": "production",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 500,
        "completed": 500,
        "failed": 0
      },
      "created_at": 1790855262,
      "completed_at": 1790855425,
      "expired_at": null,
      "cancelled_at": null
    },
    {
      "stage": "production",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 500,
        "completed": 500,
        "failed": 0
      },
      "created_at": 1790855268,
      "completed_at": 1790855450,
      "expired_at": null,
      "cancelled_at": null
    },
    {
      "stage": "production",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 500,
        "completed": 500,
        "failed": 0
      },
      "created_at": 1790855274,
      "completed_at": 1790855461,
      "expired_at": null,
      "cancelled_at": null
    },
    {
      "stage": "production",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 500,
        "completed": 500,
        "failed": 0
      },
      "created_at": 1790855279,
      "completed_at": 1790855428,
      "expired_at": null,
      "cancelled_at": null
    },
    {
      "stage": "production",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 500,
        "completed": 500,
        "failed": 0
      },
      "created_at": 1790855286,
      "completed_at": 1790855417,
      "expired_at": null,
      "cancelled_at": null
    },
    {
      "stage": "production",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 500,
        "completed": 500,
        "failed": 0
      },
      "created_at": 1790855292,
      "completed_at": 1790855444,
      "expired_at": null,
      "cancelled_at": null
    },
    {
      "stage": "production",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 500,
        "completed": 500,
        "failed": 0
      },
      "created_at": 1790855297,
      "completed_at": 1790855470,
      "expired_at": null,
      "cancelled_at": null
    },
    {
      "stage": "production",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 500,
        "completed": 500,
        "failed": 0
      },
      "created_at": 1790855302,
      "completed_at": 1790855684,
      "expired_at": null,
      "cancelled_at": null
    },
    {
      "stage": "production",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 500,
        "completed": 500,
        "failed": 0
      },
      "created_at": 1790855308,
      "completed_at": 1790855450,
      "expired_at": null,
      "cancelled_at": null
    },
    {
      "stage": "production",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 500,
        "completed": 500,
        "failed": 0
      },
      "created_at": 1790855313,
      "completed_at": 1790855457,
      "expired_at": null,
      "cancelled_at": null
    },
    {
      "stage": "production",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 500,
        "completed": 500,
        "failed": 0
      },
      "created_at": 1790855319,
      "completed_at": 1790855461,
      "expired_at": null,
      "cancelled_at": null
    },
    {
      "stage": "production",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 500,
        "completed": 500,
        "failed": 0
      },
      "created_at": 1790855325,
      "completed_at": 1790855527,
      "expired_at": null,
      "cancelled_at": null
    },
    {
      "stage": "production",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 500,
        "completed": 500,
        "failed": 0
      },
      "created_at": 1790855331,
      "completed_at": 1790855488,
      "expired_at": null,
      "cancelled_at": null
    },
    {
      "stage": "production",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 500,
        "completed": 496,
        "failed": 4
      },
      "created_at": 1790855336,
      "completed_at": 1790855542,
      "expired_at": null,
      "cancelled_at": null
    },
    {
      "stage": "production",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 500,
        "completed": 500,
        "failed": 0
      },
      "created_at": 1790855342,
      "completed_at": 1790855468,
      "expired_at": null,
      "cancelled_at": null
    },
    {
      "stage": "production",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 500,
        "completed": 500,
        "failed": 0
      },
      "created_at": 1790855348,
      "completed_at": 1790855471,
      "expired_at": null,
      "cancelled_at": null
    },
    {
      "stage": "production",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 500,
        "completed": 500,
        "failed": 0
      },
      "created_at": 1790855355,
      "completed_at": 1790855478,
      "expired_at": null,
      "cancelled_at": null
    },
    {
      "stage": "production",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 500,
        "completed": 500,
        "failed": 0
      },
      "created_at": 1790855361,
      "completed_at": 1790855485,
      "expired_at": null,
      "cancelled_at": null
    },
    {
      "stage": "production",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 500,
        "completed": 500,
        "failed": 0
      },
      "created_at": 1790855367,
      "completed_at": 1790855488,
      "expired_at": null,
      "cancelled_at": null
    },
    {
      "stage": "production",
      "round": 1,
      "id": "private-service-id-withheld",
      "status": "completed",
      "request_counts": {
        "total": 200,
        "completed": 200,
        "failed": 0
      },
      "created_at": 1790855372,
      "completed_at": 1790855462,
      "expired_at": null,
      "cancelled_at": null
    }
  ],
  "production_rounds": 1,
  "pilot_rounds": 1,
  "pilot_count": 300,
  "production_count": 11700,
  "total_coverage": 12000,
  "per_task_counts": {
    "DM": 4000,
    "MT": 4000,
    "PG": 4000
  },
  "duplicate_count": 0,
  "missing_count": 0,
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
  "successful_structured_responses": 11996,
  "request_failures": 4,
  "retry_count": 0,
  "schema_failures": 0,
  "terminal_failures": 0,
  "pending_technical_failures": 4,
  "definitive_labels": 11887,
  "usage": {
    "pilot": {
      "input": 96675,
      "output": 21038,
      "reasoning": 9351,
      "cached": 0,
      "usage_records": 300,
      "mean_tokens_per_request": 392.37666666666667,
      "median_tokens_per_request": 376.0,
      "max_output_tokens_per_request": 337,
      "estimated_cost_usd": 0.40373
    },
    "production": {
      "input": 3772463,
      "output": 768512,
      "reasoning": 310321,
      "cached": 0,
      "usage_records": 11696,
      "mean_tokens_per_request": 388.25025649794804,
      "median_tokens_per_request": 371.0,
      "max_output_tokens_per_request": 526,
      "estimated_cost_usd": 15.230046
    },
    "combined": {
      "input": 3869138,
      "output": 789550,
      "reasoning": 319672,
      "cached": 0,
      "usage_records": 11996,
      "mean_tokens_per_request": 388.3534511503835,
      "median_tokens_per_request": 371.0,
      "max_output_tokens_per_request": 526,
      "estimated_cost_usd": 15.633776
    }
  },
  "operational_block": {
    "code": "billing_hard_limit_reached",
    "prepared_retry_requests": 4,
    "retry_batch_submitted": false,
    "batch_creation_http_400_failures": 2,
    "reconciliation": "Exhaustive Batch listing found no Batch for the processed retry input file.",
    "resume": "Restore billing capacity; reconcile round_2 submission intents before creating a Batch using the existing uploaded file. Do not rerun round 1."
  },
  "cost_basis": "Actual returned usage; frozen pricing; reasoning included in output; no cache discount; estimates, not invoices.",
  "preservation": {
    "frozen_protocol_unchanged": true,
    "pilot_artifacts_unchanged": true,
    "frozen_preparation_unchanged": true,
    "prior_E11_unchanged": true,
    "row_level_files_git_ignored": true
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
    "label_balancing": false
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
      "log": "E11C_PRODUCTION_FINAL_TEST_1.txt",
      "sha256": "0c1ed135f677155396e995ad9df6b30d34625a97908a08fb736bf90047fec83d"
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
      "log": "E11C_PRODUCTION_FINAL_TEST_2.txt",
      "sha256": "0d4f37b9e43c695797bd7c456b0d403d26feb00a49934ec27d09767842ad7c2b"
    }
  ],
  "artifact_sha256": {
    "private\\pilot_300\\round_1\\batch_001\\output_file.jsonl": "de40b8e9aed86ddb50ef70df8b6679ca32142da278dcfca3623607fd985a0e23",
    "private\\production_11700\\round_1\\batch_001\\output_file.jsonl": "116fd0ce0a8b247181e00dc80962a73d4f7e3abf4d17a1c0940a7fa345019bf6",
    "private\\production_11700\\round_1\\batch_002\\output_file.jsonl": "54c902c05151900633ba2ec3a1c714e5fb94126dba927e188a692c43a24cc147",
    "private\\production_11700\\round_1\\batch_003\\output_file.jsonl": "8daed952e6a5486a7ab7e6a3a6a11c1f4876f704fd32aec84152a3e8114e8962",
    "private\\production_11700\\round_1\\batch_004\\output_file.jsonl": "0848c0ba4219c738710641a2a4ad1c28ffab1f4cfe617d6cbde6943af6b96d82",
    "private\\production_11700\\round_1\\batch_005\\output_file.jsonl": "0ea2bd698742fec0b6a221b25c4ca9f680ffcb2b646bf41f0b03132f2d5f7935",
    "private\\production_11700\\round_1\\batch_006\\output_file.jsonl": "604212e3ce5cbe5ac44318c8c67d466b6298329c30a31feda086cf2a18b5dc9d",
    "private\\production_11700\\round_1\\batch_007\\output_file.jsonl": "f3030b29e92a0db5ece1a16b948065d4125acaa503e64d68276d3472b448e36b",
    "private\\production_11700\\round_1\\batch_008\\output_file.jsonl": "d1c9a87d838e1a608b5587602d2114f902e2f18f783ebbb22ab6216d95d70809",
    "private\\production_11700\\round_1\\batch_009\\output_file.jsonl": "c9636c53e3125b2fd9a1e89a764994b15453563601d1e3053008f74318a517f3",
    "private\\production_11700\\round_1\\batch_010\\output_file.jsonl": "120cf86562a8baa7bc9cda482f475cab0660271b1bf23ed455d6f15396a3a4ec",
    "private\\production_11700\\round_1\\batch_011\\output_file.jsonl": "aba7b662115946c7bb7237e742c3e632a26e5affa9b5d5ee2bb2d528b6f8e2a6",
    "private\\production_11700\\round_1\\batch_012\\output_file.jsonl": "b11855fbb17edfa5c5229b05de66ac16a55dcace426e0010acc4c2cd5b45cf46",
    "private\\production_11700\\round_1\\batch_013\\output_file.jsonl": "c1c7d2e909bd1f07811b3bb5a0424590518a20964da28d6df82dac80b15af8a5",
    "private\\production_11700\\round_1\\batch_014\\output_file.jsonl": "4c2062a3255f3a5f984d801ea931950935877b5bced7a7d7b882655ee750f86c",
    "private\\production_11700\\round_1\\batch_015\\output_file.jsonl": "52320f23f69c311e27a4570639084fb442381616954b987c674d50f5f1f21840",
    "private\\production_11700\\round_1\\batch_016\\output_file.jsonl": "c586b011fb84fed8cb0824c03324df2f046ebce9c0870f001c5386d7d1d26bc9",
    "private\\production_11700\\round_1\\batch_017\\output_file.jsonl": "7a6e4bcf216bb6cae84c43fccb7dbbbf787570ae152cceff403b9febf727ed54",
    "private\\production_11700\\round_1\\batch_018\\output_file.jsonl": "e254a8a61ed3f71fd7383a45118a038059641a64ea5b1f170f25d95861b14342",
    "private\\production_11700\\round_1\\batch_018\\error_file.jsonl": "e57710d60ccb447f81a18886f0a7147ea47ba358b46021bb8529a674c4a9ef0b",
    "private\\production_11700\\round_1\\batch_019\\output_file.jsonl": "da4e71ff0295fd19fb3baaeba407673cf96671629f7df06a941dc2dc7855bc36",
    "private\\production_11700\\round_1\\batch_020\\output_file.jsonl": "71b8f8b000e26c10042592a4b41d8423c4550bc7b40f614d2f534de87ed5d921",
    "private\\production_11700\\round_1\\batch_021\\output_file.jsonl": "3012feb2df48ab9856c85057d3169666e59e6fbc165aa074cc982c797f358174",
    "private\\production_11700\\round_1\\batch_022\\output_file.jsonl": "61d9a8c3cbbfb2bc0a5110cf8a31531677829afe631d4c2ca35e7f49fd7e2888",
    "private\\production_11700\\round_1\\batch_023\\output_file.jsonl": "bcf2d36d438a66b73ff998f6f146388536b0e408c6f6cee3852a63c5f51d3ef4",
    "private\\production_11700\\round_1\\batch_024\\output_file.jsonl": "1f680ee23e6e2b62ee9ecf2aa69807f0b17944445adb56c9473fc060d27413c1",
    "e11c_production.py": "674fdb250712e2d5bdd658236a9df877ecc305c6978ee6af9e10ae2bf4f115c6",
    "audit_e11c_production.py": "7864839678dc74a80c0971f1d4d5e7f6c20d92848a862261acc8fef81713c3fe",
    "test_e11c_production.py": "d01cf9133cff59f7c09f8c0d50fddf70a9aff48e3ce74cbf99d3f29445a4a638",
    "README_E11C_PRODUCTION.md": "7e550882f36d9c3e2a74f501e8f867b6eb6157abe20d7a164f412e8f49c5df26",
    "private\\production_11700\\full_audit_ledger.jsonl": "05b5dea8b7d028d81d68c602bc1b5b70376911c8c47561f2d93cd0d98ce1566d",
    "private\\production_11700\\parsed_labels.jsonl": "f62128efee9d8eee22a27707b68982fcabb8c41f8355f88886b2f918ec8330fc",
    "private\\production_11700\\future_binary_supervision.jsonl": "b071f6f01db297393cff6c64e7614ad9c241e8da28379a21740b0e5d3d50ccea",
    "private\\production_11700\\candidates.jsonl": "61f154395535b2908a4868b48c0dd5d0a4cff92a332864ebb588a21767c31408",
    "E11C_PRODUCTION_PREFLIGHT.json": "47d69b4efb783e0ba0f43da2c40fe9bf5a06d9059014cacf07c0e49cff3b9453",
    "E11C_PRODUCTION_PRESERVATION_BASELINE.json": "ea883a9c8f9827657af87752d64327587da21e73beb9b9a8f1063799a6e6bd63",
    "private\\production_11700\\round_1\\requests.jsonl": "df555abad7d6852289efa03824e2858d49cfdb7bc83eb2491982749e3d515514",
    "private\\production_11700\\round_1\\request_manifest.json": "705d6d6a1fde87f05f7064d60f9861c8d2caa71c30fa2c5db155ae355a9ce04c",
    "private\\production_11700\\round_1\\ledger.jsonl": "e8f02216edcf772d2fb558e39e25473eee09a6e4d6f336cee75bce3969874f9f",
    "private\\production_11700\\round_1\\parse_report.json": "bb06a6d511e0a6f0aa7105e9135cf2778bb661fa126b7c4fe52b205cdfaf398a"
  }
}
```
