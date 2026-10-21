import hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE/'vendor'))
sys.path[:0]=[str(HERE),str(HERE.parent),str(ROOT/'RAG/scripts'),str(ROOT/'RAG/results/rag_e6_v1/scripts')]
import audit_data
import module4_build_external_lexicon as lex
import predict_and_score as pipeline

class PipelineTests(unittest.TestCase):
    def test_label_free_input_projection(self):
        original,_=audit_data.sanitized_test(ROOT/'Labeled test/SHROOM_test-labeled/test.model-agnostic.json')
        saved=json.loads((HERE/'test_inputs_label_free.json').read_text(encoding='utf-8'))
        expected=[{k:audit_data.norm(v) if k in ('src','tgt','hyp') else v for k,v in r.items()} for r in original]
        self.assertEqual(saved,expected)
        self.assertEqual(len(saved),1500)
        self.assertEqual(len({r['id'] for r in saved}),1500)
        self.assertTrue(all(set(r)=={'id','task','src','tgt','hyp'} for r in saved))

    def test_missing_terms_exact_population(self):
        planned=json.loads((HERE/'reconstruction_terms.json').read_text(encoding='utf-8'))
        audited=json.loads((HERE.parent/'recovery_audit/REQUIRED_TERMS.json').read_text(encoding='utf-8'))
        self.assertEqual(len(planned),557)
        self.assertEqual({r['term_key'] for r in planned},set(audited['missing_terms']))
        self.assertNotIn('marrow',{r['term_key'] for r in planned})
        self.assertNotIn('bountiful',{r['term_key'] for r in planned})

    def test_parser_reproduces_frozen_lexicon_bytes(self):
        original=ROOT/'RAG/results/rag_module4/continuation_v1/schannel_run_v1/module4_external_lexical_snapshot.jsonl'
        replay=HERE/'parser_replay/snapshot.jsonl'
        self.assertEqual(replay.read_bytes(),original.read_bytes())
        self.assertEqual(len(replay.read_text(encoding='utf-8').splitlines()),462)

    def test_completed_reconstruction_coverage_and_hashes(self):
        manifest=json.loads((HERE/'E10_RECONSTRUCTION_MANIFEST.json').read_text(encoding='utf-8'))
        self.assertEqual(len(manifest['terms']),557)
        coverage=manifest['coverage']
        self.assertEqual(coverage['reconstructed_terms_with_senses']+coverage['unavailable_terms'],557)
        self.assertEqual(coverage['DM_with_reconstructed_definitions']+coverage['DM_with_frozen_definitions']+coverage['DM_original_missing_definition_behavior'],563)
        self.assertEqual(coverage['technical_failure_terms'],0)
        self.assertEqual(coverage['confirmed_no_sense_terms'],28)
        self.assertEqual(hashlib.sha256((HERE/'WIKTIONARY_RECONSTRUCTED_PROCESSED/combined_snapshot.jsonl').read_bytes()).hexdigest(),manifest['combined_snapshot_sha256'])
        for term in manifest['terms']:
            self.assertEqual(hashlib.sha256((HERE/term['processed_path']).read_bytes()).hexdigest(),term['processed_sha256'])
            self.assertTrue(term['requests'])

    def test_factcg_complete_identity_and_integrity(self):
        result=json.loads((HERE/'factcg_return.json').read_text(encoding='utf-8'))
        inputs=json.loads((HERE/'test_inputs_label_free.json').read_text(encoding='utf-8'))
        self.assertEqual(result['report']['status'],'PASS')
        self.assertEqual([r['id'] for r in result['scores']],[str(r['id']) for r in inputs])
        self.assertEqual(len(result['scores']),1500)
        raw=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in result['scores']).encode()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),result['report']['scores_sha256'])

    def test_frozen_contract_unchanged(self):
        contract=pipeline.contract()
        self.assertEqual(len(contract['ordered_features']),37)
        self.assertEqual(contract['threshold'],.5)
        from sklearn.ensemble import RandomForestRegressor
        self.assertEqual(RandomForestRegressor(**contract['rf_parameters']).get_params(),contract['rf_parameters'])

    def test_scoring_cannot_load_gold_before_frozen_predictions(self):
        with tempfile.TemporaryDirectory(dir=HERE) as d:
            with patch.object(pipeline,'HERE',Path(d)):
                with self.assertRaises(FileNotFoundError):pipeline.validated_predictions()

    def test_prediction_tampering_rejected(self):
        with tempfile.TemporaryDirectory(dir=HERE) as d:
            p=Path(d)
            (p/'E10_OFFICIAL_TEST_PREDICTIONS.json').write_text('{}')
            (p/'E10_OFFICIAL_TEST_PREDICTIONS_SHA256.txt').write_text('0'*64)
            with patch.object(pipeline,'HERE',p):
                with self.assertRaises(AssertionError):pipeline.validated_predictions()

    def test_original_no_definition_behavior(self):
        import e6_common as c
        import build_features as e6
        def prohibited(*args):raise AssertionError('Unexpected inference without definitions')
        row={'example_id':'x','task':'DM','term':'absent','src':'s','tgt':'t','rag_applicable':1}
        f=c.frozen.row_features(row,[],prohibited,prohibited)
        self.assertTrue(all(f[k]==0 for k in c.frozen.FEATURES))
        self.assertTrue(all(v==0 for v in e6.compare_hyp(None,'hyp',prohibited,prohibited).values()))

    def test_ranking_uses_query_only_and_deterministic_ties(self):
        import e6_common as c
        import build_features as e6
        query={'example_id':'x','task':'DM','term':'a','src':'s','rag_applicable':1}
        with self.assertRaises(ValueError):e6.reconstruct([{**query,'hyp':'LEAK'}],[],None)
        records=[{'candidate_term':'a','candidate_context':'Noun: b','source_entry_id':v,'evidence_id':v} for v in ['z','a']]
        seen=[]
        def embed(texts):seen.extend(texts);return [[1.,0.] for _ in texts]
        selected=c.frozen.select_top5('a\ns',records,embed)
        self.assertEqual([r['evidence_id'] for r,_ in selected],['a','z'])
        self.assertEqual(seen[0],'a\ns')

if __name__=='__main__':unittest.main()
