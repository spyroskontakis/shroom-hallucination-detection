import collections
import csv
import hashlib
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
import audit_data as audit

def load(name):
    return json.loads((HERE/name).read_text(encoding='utf-8'))

class RecoveryAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=load('E10_OFFICIAL_TEST_STRICT_TRAIN_MANIFEST.json')
        cls.test,_=audit.sanitized_test(ROOT/'Labeled test/SHROOM_test-labeled/test.model-agnostic.json')
        with (ROOT/'codex/canonical_human_development_manifest.csv').open(encoding='utf-8-sig') as f:
            cls.original=list(csv.DictReader(f))

    def test_retained_rows_unchanged_and_partition_complete(self):
        m=self.manifest
        excluded={r['canonical_id'] for r in m['excluded']}
        self.assertEqual(len(excluded),14)
        self.assertEqual(m['retained_rows'],[r for r in self.original if r['canonical_id'] not in excluded])
        self.assertEqual(len(m['retained_rows']),547)
        self.assertEqual(len({r['canonical_id'] for r in m['retained_rows']}),547)

    def test_strict_pool_has_no_source_target_overlap(self):
        pairs={audit.key(r,('task','src','tgt')) for r in self.test}
        self.assertTrue(all(audit.key(r,('task','src','tgt')) not in pairs for r in self.manifest['retained_rows']))

    def test_exclusion_identity_hypothesis_and_no_exact_overlap(self):
        for removed in self.manifest['excluded']:
            r=self.original[removed['canonical_index']]
            self.assertEqual(r['canonical_id'],removed['canonical_id'])
            self.assertEqual(r['task'],'MT')
            self.assertEqual(int(r['original_row_index']),removed['original_source_index'])
            for i,test_id in zip(removed['test_indices'],removed['test_ids']):
                t=self.test[i]
                self.assertEqual(t['id'],test_id)
                self.assertEqual(audit.key(r,('task','src','tgt')),audit.key(t,('task','src','tgt')))
                self.assertNotEqual(audit.norm(r['hyp']),audit.norm(t['hyp']))
        self.assertFalse({audit.key(r) for r in self.original}&{audit.key(r) for r in self.test})

    def test_missing_term_table_complete(self):
        required=load('REQUIRED_TERMS.json')
        with (HERE/'WIKTIONARY_RECOVERY_TABLE.csv').open(encoding='utf-8-sig') as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),557)
        self.assertEqual({r['term'] for r in rows},set(required['missing_terms']))
        ids=[]
        for r in rows:
            self.assertEqual(json.loads(r['required_by_test_ids']),required['all_DM_terms'][r['term']])
            self.assertEqual(r['frozen_content_found'],'false')
            ids+=json.loads(r['required_by_test_ids'])
        self.assertEqual(len(ids),561)
        self.assertEqual(len(set(ids)),561)
        self.assertEqual(sum(len(required['all_DM_terms'][t]) for t in required['already_acquired']),2)

    def test_preserved_frozen_sources(self):
        source=json.loads((HERE.parent/'E10_OFFICIAL_TEST_FEATURE_MANIFEST.json').read_text(encoding='utf-8'))
        for p,expected in source['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),expected,p)
        verification=load('VERIFICATION.json')
        self.assertTrue(all(verification['parent_audit_hashes'].values()))
        self.assertEqual(verification['existing_file_metadata_changes'],[])

    def test_summary_qualifications_and_historical_identity(self):
        summary=load('RECOVERY_SUMMARY.json')
        self.assertEqual(summary['recovered_frozen_terms'],0)
        self.assertEqual(summary['official_DM_examples_resource_reproducible'],2)
        for k in ['model_fits','inference_runs','new_test_predictions','new_test_scoring_runs','network_retrievals','modal_runs']:
            self.assertEqual(summary[k],0)
        verification=load('VERIFICATION.json')['historical_test_input_identity']
        self.assertTrue(verification['text_multiset_equal'])
        self.assertTrue(verification['id_set_equal'])
        self.assertFalse(verification['gold_values_compared'])

if __name__=='__main__':
    unittest.main()
