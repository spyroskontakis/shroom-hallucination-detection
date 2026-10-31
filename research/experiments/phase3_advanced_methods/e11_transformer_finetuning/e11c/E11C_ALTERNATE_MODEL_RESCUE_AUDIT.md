# E11-C alternate-model rescue

These Azure gpt-5-mini judgments are excluded from the homogeneous gpt-5.6-sol pool.

```json
{
  "status": "PASS",
  "provider": "Azure / Microsoft Foundry",
  "deployment": "gpt-5-mini",
  "rescue_teacher": "gpt-5-mini",
  "original_teacher": "gpt-5.6-sol",
  "deployment_type": "not exposed by Responses API",
  "protocol_sha256": "792bbe4ef1d0752e606c81dc511684f7bb0a051b2a5c24a937c49d7cb928f818",
  "requested_candidates": 4,
  "task": "PG",
  "completed": 4,
  "results": [
    {
      "sample_key": "1f2a34940a94ab535d5fba86b8e0eee6b4426a1e81f33455ed3e38b338b74adc",
      "task": "PG",
      "label": "not_hallucination",
      "reason": "The hypothesis only adds the word \"even\" for emphasis and preserves the original meaning, so it remains faithful to the reference.",
      "attempt": 1,
      "returned_model": "gpt-5-mini",
      "response_id": "resp_037a61347466e680016abe73b827488195b713b0c82f6aeb2b",
      "raw_response_path": "private\\azure_alternate_rescue\\1f2a34940a94ab535d5fba86b8e0eee6b4426a1e81f33455ed3e38b338b74adc\\attempt_1.json",
      "raw_response_sha256": "ff2e8eb7190cd63685ab70ce546c961a21377dcb90805c8d68e4b79e1a4d5ae9",
      "excluded_from_original_supervision": true
    },
    {
      "sample_key": "f4fdbac32e85fe991167d007dee366f195f1ecab7808e9ebe3ac4eb7b3416e39",
      "task": "PG",
      "label": "hallucination",
      "reason": "The hypothesis shifts meaning from morally 'bad people' to those who merely 'look bad,' which is not supported by the reference.",
      "attempt": 1,
      "returned_model": "gpt-5-mini",
      "response_id": "resp_0cc13499256475be016abe73baced481948f7d95b146713113",
      "raw_response_path": "private\\azure_alternate_rescue\\f4fdbac32e85fe991167d007dee366f195f1ecab7808e9ebe3ac4eb7b3416e39\\attempt_1.json",
      "raw_response_sha256": "cb9aa712cb2fcd320e1a2d1b95ad1c435a1bc1baba4fd76c6ed2c854ad1da7ec",
      "excluded_from_original_supervision": true
    },
    {
      "sample_key": "24d9c782312eaaa9fca602f5688d43605af8470a8b6c83da8e81dd4c003f2382",
      "task": "PG",
      "label": "not_hallucination",
      "reason": "Paraphrase preserves the same meaning\u2014colloquial spelling \"winnin'\" corresponds to standard \"winning.\"",
      "attempt": 1,
      "returned_model": "gpt-5-mini",
      "response_id": "resp_03b8a8d5c855f6f1016abe73bda2cc819093c8efc561359dd8",
      "raw_response_path": "private\\azure_alternate_rescue\\24d9c782312eaaa9fca602f5688d43605af8470a8b6c83da8e81dd4c003f2382\\attempt_1.json",
      "raw_response_sha256": "664a9ac86f640466dd2d535fbbadc3884f493728d7748b0fe575571a7eecac1d",
      "excluded_from_original_supervision": true
    },
    {
      "sample_key": "baa5feb7b943ad163b7d3ad434ef3aaf27505092f4cc772fda2f59c956fdb833",
      "task": "PG",
      "label": "not_hallucination",
      "reason": "Adding the pronoun 'it' only makes the object explicit but preserves the original meaning of refusing to sign, so the paraphrase is faithful.",
      "attempt": 1,
      "returned_model": "gpt-5-mini",
      "response_id": "resp_0eceeae2e35ea761016abe73c0b3208197ac86c921aa7688b5",
      "raw_response_path": "private\\azure_alternate_rescue\\baa5feb7b943ad163b7d3ad434ef3aaf27505092f4cc772fda2f59c956fdb833\\attempt_1.json",
      "raw_response_sha256": "1836a34807800e408acea86fb96fe6455497cf76bf616d424f00e81a01dced53",
      "excluded_from_original_supervision": true
    }
  ],
  "returned_models": [
    "gpt-5-mini"
  ],
  "configuration_differences": [
    "Azure provider and gpt-5-mini model instead of gpt-5.6-sol",
    "Synchronous Responses API instead of Batch; no Batch pricing assumption",
    "Separate rescue attempt budget of at most three calls per candidate; SDK retries disabled"
  ],
  "unchanged_request_settings": [
    "prompt",
    "input and PG source reference",
    "schema",
    "label vocabulary",
    "medium reasoning",
    "2048 output token limit",
    "store=false",
    "omitted sampling parameters"
  ],
  "excluded_from_homogeneous_supervision": true,
  "original_definitive_labels": 11887,
  "original_uncertain_labels": 109,
  "original_terminal_outcomes": 11996,
  "original_pending": 4,
  "original_artifacts_unchanged": true,
  "previous_successful_outcomes_overwritten": false,
  "api_failures": 0,
  "schema_failures": 0,
  "retries": 0,
  "usage": {
    "input_tokens": 1263,
    "output_tokens": 831,
    "reasoning_tokens": 448,
    "cached_input_tokens": 0,
    "usage_records": 4
  },
  "azure_cost": null,
  "cost_note": "Responses does not expose billed cost; Azure deployment rate not assumed.",
  "student_training": false,
  "fold_construction": false,
  "dev_evaluation": false,
  "official_test_access": false,
  "prompt_tuning": false,
  "manual_correction": false,
  "commit": false,
  "push": false
}
```
