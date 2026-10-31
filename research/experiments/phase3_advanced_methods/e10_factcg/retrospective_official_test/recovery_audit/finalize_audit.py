"""Finalize offline recovery reports; never imports model or network clients."""
import collections
import csv
import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
import audit_data as audit

def load(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))

def save(name, obj):
    (HERE / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

manifest = load('E10_OFFICIAL_TEST_STRICT_TRAIN_MANIFEST.json')
required = load('REQUIRED_TERMS.json')
inventory = load('SEARCH_INVENTORY.json')
supplement = load('SUPPLEMENTARY_SEARCH.json')
assert {r['term'] for r in inventory['recovery_candidates'] + supplement['candidates']} == {'bottomful'}
lines = ['# MT overlap audit', '', 'Proposed strict pool: **547** (479 development + 68 trial; DM 211, MT 202, PG 134). No model was fit.', '',
         'All 14 removed rows are MT development examples. Indices are zero-based. Every matched hypothesis differs, and no exact `(task,src,tgt,hyp)` example is shared anywhere in the original 561-row pool. Equality uses the existing audit NFC/whitespace normalization, preserving case. Labels are not used to select exclusions.', '',
         '| Canonical ID | Canonical index | Original source index | Source | Test ID | Different hypothesis | Exact example shared |',
         '|---|---:|---:|---|---|---|---|']
for r in manifest['excluded']:
    lines.append(f"| {r['canonical_id']} | {r['canonical_index']} | {r['original_source_index']} | {r['source']} | {', '.join(map(str,r['test_ids']))} | Yes | No |")
lines += ['', 'The retained rows are copied unchanged from the canonical manifest, including their existing training labels. The proposed manifest does not replace the canonical 561-row development artifacts. Removing these 14 rows is a stricter training-population choice, not a new E10 CV result.']
(HERE/'E10_OFFICIAL_TEST_MT_OVERLAP_AUDIT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

table_path = HERE/'WIKTIONARY_RECOVERY_TABLE.csv'
with table_path.open(encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)
for r in rows:
    r['frozen_content_found'] = 'false'
    r['status'] = 'REJECTED_INTERNAL_ANNOTATION_NOT_FROZEN_WIKTIONARY' if r['term']=='bottomful' else 'NOT_RECOVERED'
with table_path.open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)

checks = {}
checks['parent_audit_hashes'] = {}
for line in (HERE.parent/'E10_OFFICIAL_TEST_SHA256SUMS.txt').read_text().splitlines():
    expected,name=line.split(None,1)
    p=HERE.parent/name.strip()
    checks['parent_audit_hashes'][name.strip()] = digest(p)==expected
feature_manifest=json.loads((HERE.parent/'E10_OFFICIAL_TEST_FEATURE_MANIFEST.json').read_text(encoding='utf-8'))
checks['frozen_source_hashes']={p:digest(ROOT/p)==expected for p,expected in feature_manifest['source_sha256'].items()}
checks['existing_file_metadata_changes']=[]
for item in inventory['file_inventory']:
    p=ROOT/item['path']
    if not p.exists() or p.stat().st_size!=item['size'] or p.stat().st_mtime_ns!=item['mtime_ns']:
        checks['existing_file_metadata_changes'].append(item['path'])

checks['known_raw_content']=[]
for term,r in required['already_acquired'].items():
    for kind in ['revision','parse']:
        name=r[f'raw_{kind}_reference'];expected=r[f'raw_{kind}_sha256']
        matches=[ROOT/i['path'] for i in inventory['file_inventory'] if Path(i['path']).name==name]
        valid=[str(p.relative_to(ROOT)) for p in matches if digest(p)==expected]
        assert valid, (term,kind)
        checks['known_raw_content'].append({'term':term,'kind':kind,'sha256':expected,'matching_paths':valid,'test_ids':required['all_DM_terms'][term]})

test,_=audit.sanitized_test(ROOT/'Labeled test/SHROOM_test-labeled/test.model-agnostic.json')
old_path=ROOT/'codex/data/7. Ablation Synthetic Data/4.nli_similarity_features_dataset.csv'
with old_path.open(encoding='utf-8-sig') as f:
    reader=csv.reader(f);header=next(reader)
    indices={k:header.index(k) for k in ['id','task','src','tgt','hyp']}
    old=[{k:r[i] for k,i in indices.items()} for r in reader]
checks['historical_test_input_identity']={'rows':len(old),'text_multiset_equal':collections.Counter(audit.key(r) for r in old)==collections.Counter(audit.key(r) for r in test),'id_set_equal':{str(r['id']) for r in old}=={str(r['id']) for r in test},'gold_values_compared':False,'source_sha256':digest(old_path)}
checks['historical_timestamps']={}
for relative in ['codex/data/shroom_ensemble.ipynb','codex/data/7. Ablation Synthetic Data/4.nli_similarity_features_dataset.csv','codex/data/7. Ablation Synthetic Data/ablation_synthetic_ratio_results.csv','codex/data/7. Ablation Synthetic Data/ablation_synthetic_weight_results.csv']:
    p=ROOT/relative
    checks['historical_timestamps'][relative]={'sha256':digest(p),'filesystem_mtime_utc':datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat(),'not_authenticated_execution_time':True}
assert all(checks['parent_audit_hashes'].values())
assert all(checks['frozen_source_hashes'].values())
assert not checks['existing_file_metadata_changes']
save('VERIFICATION.json',checks)
status={'recovery_status':'C. EXACT RECOVERY IMPOSSIBLE','qualification':'Within the searched local repository, archives and Git object database; no assertion about unavailable remote backups.','strict_training_examples':547,'MT_overlap_exclusions':14,'missing_wiktionary_terms':557,'recovered_frozen_terms':0,'official_DM_examples_resource_reproducible':2,'official_DM_examples_total':563,'official_DM_examples_blocked':561,'full_test_feature_vectors_generated_or_numerically_verified':0,'test_gold_seen_before':True,'test_performance_computed_before':True,'required_evaluation_description':'retrospective evaluation on the official labeled test set','model_fits':0,'inference_runs':0,'new_test_predictions':0,'new_test_scoring_runs':0,'network_retrievals':0,'modal_runs':0,'recommended_next_action':'Keep full official evaluation blocked. Choose explicitly between a resource-eligible strict subset and a separately documented reconstructed retrospective evaluation; execute neither in this audit.'}
save('RECOVERY_SUMMARY.json',status)
(HERE/'RECOVERY_REPORT.md').write_text('''# E10 official-test prerequisite recovery

**RECOVERY STATUS: C. EXACT RECOVERY IMPOSSIBLE with the locally available frozen material.**

The strict training proposal contains 547 examples after 14 MT source/target-pair exclusions. All removed hypotheses differ from their matching test hypotheses; no exact example is shared. See the strict manifest and MT overlap audit for all IDs and indices.

## Recovery search

The search included ignored local files, all repository experiment/cache/raw-source/manifest directories, cleanup backups, previous runs, notebook source/output JSON, text/HTML, package archives, all branches/tags/remotes/reflogs, historical blobs, and unreachable Git blobs. `SEARCH_INVENTORY.json`, `SUPPLEMENTARY_SEARCH.json` and `GIT_UNREACHABLE_INVENTORY.txt` record scope and evidence. The first pass examined 375 archive objects, 2,606 archive members and 611 historical Git blobs. The additional pass examined 1,009 unreachable blobs and rescanned local text for generic definition mappings. Counts include repeated/duplicate content; they are not unique recovered resources.

No qualifying frozen material was recovered for the 557 missing terms (561 DM rows). `WIKTIONARY_RECOVERY_TABLE.csv` has exactly one row for each missing term, with its required test IDs, verdict, and available candidate provenance. Blank source/timestamp/hash fields mean that no frozen source was found, not that an empty definition was verified.

The only candidate term, `bottomful`, appears as evidence ID 17437 in three Module3 annotation CSVs. Its candidate context is an internal SHROOM example, the query term is `preciosity`, and it is marked irrelevant in completed annotations. These files provide neither the frozen external sense set nor Wiktionary revision provenance. They are rejected as exact E6/E10 recovery. Their file hashes and available filesystem timestamps remain in the recovery table; timestamps are Unix seconds, not authenticated acquisition times.

Known acquired terms are `marrow` and `bountiful`, covering two DM examples. Their revision/parse hashes were verified against actual local files (`VERIFICATION.json`). Hence **2/563 DM examples have the required frozen lexical material**, while **0 new full test feature vectors have been produced or numerically verified**. The distinction matters: this audit establishes resource coverage, not completed inference.

Scope limitations are explicit: dependency environments, `.git` working internals (searched separately through Git), and this output directory are excluded from the filesystem content pass. The 21 files over 100 MB are model/optimizer binaries, not lexical text resources. Arbitrary model binaries were not unpickled. No archive-reader errors occurred. Referenced raw source names and hashes are retained in the scanned manifest inventory; no manifest establishes a historical acquisition for any of the 557 missing terms. There is no claim to have searched unavailable remote storage or files outside this repository.

## Exact feature logic

See `E6_V3_DEFINITION_LOGIC.md`. Fifteen of E10's 37 features depend on the frozen dictionary sense set. Unknown acquisition cannot be silently interpreted as confirmed absence and zero-filled.

## Permissible alternatives, not executed

**Option 1 — strict frozen evaluation.** Restrict evaluation to examples for which all frozen features can be reconstructed. Dictionary coverage permits at most 939 examples (937 MT/PG plus 2 DM), pending the remaining feature checks. This is a strongly task-skewed subset and cannot yield an official 1,500-example leaderboard-comparable score. Report its composition and scope explicitly.

**Option 2 — reconstructed retrospective evaluation.** With a separate explicit decision, acquire missing terms using the SAME Wiktionary procedure: identical term extraction, redirects/revision capture, revision-bound parsing, English/POS extraction, normalization, deduplication, ranking and downstream feature definitions. Only the acquisition population needs extending beyond the original development terms. Preserve existing frozen content and save new content/provenance separately. Today's dictionary content may differ, so this is a documented deviation from frozen E10, even if the code is unchanged. Do not describe it as exact frozen reproduction or as an independent test evaluation.

Recommendation: keep the full evaluation blocked; select and document one alternative before any execution. No live retrieval was attempted here.

## Prior exposure

See `PRIOR_TEST_USE_AUDIT.md`: historical official gold inspection, test-derived CV, and synthetic-ratio/weight evaluation are directly evidenced. The historical 1,500-row feature CSV matches the official input IDs/texts. Later development-only fits do not restore independence. Test-input overlap filtering also directly affects the shared canonical training population. Use **retrospective evaluation on the official labeled test set**.

## Preservation and actions

All new work is confined to this recovery directory. Existing parent audit checksums and frozen source hashes pass; the inventoried existing files retain size and modification time. No training, inference, test scoring, new predictions, Modal, live retrieval, commit or push occurred. See `TEST_RESULTS.txt` for offline validation and `SHA256SUMS.txt` for the resulting audit artifacts.
''',encoding='utf-8')
(HERE/'GIT_STATUS_SHORT.txt').write_bytes(subprocess.check_output(['git','status','--short'],cwd=ROOT))
print(json.dumps(status,indent=2))
