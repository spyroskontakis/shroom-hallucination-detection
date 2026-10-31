"""Offline, idempotent candidate selection and protocol freeze. Never calls APIs."""
from collections import Counter
from e11c_common import *


def main():
    master = load_master()
    candidates = selected(master)
    candidate_data = rows_bytes(candidates)
    write_once(PRIVATE / 'candidates.jsonl', candidate_data)
    pool_hash = digest(candidate_data)
    counts = dict(Counter(r['task'] for r in candidates))
    docs = {
        'model': 'https://developers.openai.com/api/docs/models/gpt-5.6-sol',
        'batch': 'https://developers.openai.com/api/docs/guides/batch',
        'structured_output': 'https://developers.openai.com/api/docs/guides/structured-outputs',
        'pricing': 'https://developers.openai.com/api/docs/pricing'}
    spec = {
        'experiment': 'E11-C', 'status': 'FROZEN_LABELING_PROTOCOL_NOT_EXECUTED',
        'definition': 'Augment locked human training folds with one globally LLM-labeled model-agnostic SHROOM candidate pool; evaluate only the 561 held-out human rows.',
        'source': {'master_path':'RAG/results/phase3_e11_task_adaptation/unlabeled_master.jsonl',
                   'master_sha256':MASTER_SHA, 'rows':28649,
                   'raw_path':'Unlabeled train/SHROOM_unlabeled-training-data-v2/train.model-agnostic.json',
                   'raw_sha256':RAW_SHA, 'raw_rows':30000},
        'candidates': {'path':'private/candidates.jsonl', 'sha256':pool_hash,
                       'counts':counts, 'rows':12000,
                       'eligibility':'valid provenance, unique normalized full-sample key, nonempty hypothesis and permitted reference',
                       'ranking':'ascending (SHA256(UTF8("E11C-candidate-v1\\n" + sample_key)), sample_key); first 4000 per task; task order DM,MT,PG',
                       'label_blind':True, 'label_once_globally':True},
        'reference_policy':POLICY,
        'normalization': {'text':'Unicode NFC, trim and collapse whitespace, preserve case',
                          'hash':'SHA256 of normalized parts joined by U+241F',
                          'full':['task','src','tgt','hyp'], 'hyp':['hyp'],
                          'task_ref':['task','permitted_reference']},
        'teacher': {'model':'gpt-5.6-sol', 'reasoning_effort':'medium',
                    'metadata_status':'PUBLIC_DOCUMENTATION_VERIFIED; LIVE_ACCOUNT_METADATA_NOT_QUERIED',
                    'snapshot':'No separate dated snapshot listed in official model documentation on 2026-09-29.',
                    'api_returned_model_id':None,
                    'execution_gate':'Before any upload, retrieve exact model metadata; require id == gpt-5.6-sol. Save metadata. Require every response body.model == gpt-5.6-sol; stop/quarantine mismatch. No automatic alias/snapshot substitution.',
                    'sampling':'Omit temperature, top_p and seed; use supported defaults. No determinism guarantee or stochastic voting.',
                    'endpoint':'/v1/responses', 'max_output_tokens':2048,
                    'output_budget_includes_reasoning':True, 'tools':[], 'store':False},
        'prompt':PROMPT, 'prompt_sha256':digest(PROMPT.encode()),
        'schema':SCHEMA, 'schema_sha256':digest(encoded(SCHEMA)),
        'input_allowlist':['task','reference','hypothesis'],
        'acceptance': {'hallucination':'accepted class 1', 'not_hallucination':'accepted class 0',
                       'uncertain':'terminal rejection; never retry',
                       'other_rejections':['invalid schema','missing output','exhausted operational failures',
                                           'empty required text','malformed provenance','refusal'],
                       'confidence_or_detector_filters':False},
        'retry': {'maximum_attempts_per_sample':3, 'automatic_sdk_retries':0,
                  'retryable':['transport','HTTP 408','HTTP 429','HTTP 5xx','batch expired/cancelled missing output',
                               'invalid schema','missing output','incomplete output'],
                  'terminal':['uncertain','definitive label','refusal','nonretryable HTTP 4xx'],
                  'same_request_body':True, 'attempts_in_custom_id':True,
                  'minimum_round_delays_seconds':{'2':60,'3':300},
                  'submission_failure':'Never blindly repeat an ambiguous batch creation/upload; journal intent before request and reconcile its remote ID manually.',
                  'round_barrier':'All prior round shards must be terminal and parsed before building retries; no new candidates.'},
        'batch': {'endpoint':'/v1/responses', 'completion_window':'24h',
                  'shard_size':500, 'initial_shards':24,
                  'custom_id':'e11c-{protocol_sha256[:12]}-{sample_key}-a{attempt}',
                  'credentials':'OPENAI_API_KEY environment variable only; no key logs',
                  'api_disabled_by_default':True},
        'leakage_purge': {'before_balancing':True, 'folds_path':'codex/canonical_fold_assignments.csv',
                          'folds_sha256':FOLDS_SHA,
                          'human_path':'codex/canonical_human_development_manifest.csv',
                          'human_sha256':HUMAN_SHA, 'heldout_text_only':True,
                          'rules':['full','hyp','task_ref'],
                          'note':'Do not inherit the E11-B extra source-pair purge; E11-C uses exactly these three checks.'},
        'balancing': {'grouping':['fold','task'], 'n_keep':'min(H, NH, 1500)',
                       'class_cap':1500, 'maximum_per_task':3000, 'maximum_per_fold':9000,
                       'minimum_quota':0,
                       'ranking':'ascending (SHA256(UTF8("E11C-balance-v1\\n{fold_id}\\n{task}\\n{label}\\n{sample_key}")), sample_key)'},
        'provenance': ['source','sample_key','task','reference_field','reference_text_sha256',
                       'hypothesis_text_sha256','llm_label','llm_reason','teacher_model_id',
                       'prompt_sha256','request_custom_id','raw_response_path','raw_response_file_sha256',
                       'raw_response_line','raw_response_line_sha256','response_id','candidate_pool_sha256'],
        'student': {'model':'MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli',
                    'revision':'b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7',
                    'human_rows_by_fold':[448,449,449,449,449],
                    'human_synthetic_weighting':'NOT_FROZEN; decide after label yield, before any student training/OOF',
                    'training_execution':'NOT_PREPARED_OR_AUTHORIZED_IN_THIS_STEP'},
        'pricing': {'currency':'USD', 'date':'2026-09-29',
                    'standard_input_per_million':4.0, 'standard_output_per_million':20.0,
                    'batch_discount':0.5, 'no_cache_discount_assumed':True,
                    'note':'Promotional price documented through at least 2026-11-21; estimates exclude taxes and assume short-context requests. Recheck rates before paid execution.'},
        'documentation':docs,
        'prohibitions':['official-test access','model-aware data','human labels/p(H) in teacher',
                        'held-out labels for selection/purge','detector scores or prior predictions in teacher/acceptance',
                        'external definitions','claim decomposition','post-OOF prompt/quota tuning',
                        'API calls or label generation in preparation','student training now','commit','push']}
    spec['protocol_sha256'] = digest(encoded(spec))
    save(PROTOCOL, spec)
    write_once(HERE / 'E11C_PROTOCOL_SHA256.txt', (spec['protocol_sha256']+'\n').encode())
    manifest = {'status':'PASS', 'protocol_sha256':spec['protocol_sha256'],
                'source_master_sha256':MASTER_SHA, 'source_rows':28649,
                'source_task_counts':dict(Counter(r['task'] for r in master)),
                'candidate_path':'private/candidates.jsonl', 'candidate_sha256':pool_hash,
                'candidate_rows':12000, 'unique_keys':12000, 'task_counts':counts,
                'selection_rule':spec['candidates']['ranking'],
                'selected_sample_keys':[r['sample_key'] for r in candidates],
                'selected_keys_sha256':digest(encoded([r['sample_key'] for r in candidates])),
                'labels_generated':False}
    save(HERE / 'E11C_CANDIDATE_MANIFEST.json', manifest)
    print('Frozen protocol', spec['protocol_sha256'])
    print('Candidate manifest', sha(HERE / 'E11C_CANDIDATE_MANIFEST.json'))
    print('Candidates', counts, 'total',len(candidates))


if __name__ == '__main__':
    main()
