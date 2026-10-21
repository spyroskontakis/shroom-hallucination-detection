"""Pre-extraction contracts: direction, masking, score semantics, cache and folds."""
import sys, unittest, copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import numpy as np
import pandas as pd
import v3_common as c
from prepare_inputs import select_pairs
from extract_features import assemble,digest,validate_cache
from evaluate_v3 import metric,paired

class Contracts(unittest.TestCase):
    def test_exact_saved_projection(self):
        expected=select_pairs(c.read_json(c.V2/'inputs/nli_pairs_label_free.json'))
        actual=c.read_json(c.OUT/'inputs/hhem_pairs_label_free.json')
        self.assertEqual(actual,expected);self.assertEqual(len(actual),754)
        self.assertEqual(sum(p['group']=='A' for p in actual),561)
        self.assertEqual(sum(p['group']=='C' for p in actual),193)
        bad=copy.deepcopy(actual[:1]);bad[0]['label_bin']=1
        with self.assertRaises(AssertionError):select_pairs(bad)

    def test_assemble_missing_definition(self):
        base=pd.DataFrame({'canonical_id':['x','y'],'rag_evidence_available':[1,0],'old':[.123456789123,2.]})
        pairs=[{'pair_id':p} for p in ['x:A','x:C','y:A']]
        scores=[{'pair_id':p,'consistency':s} for p,s in [('x:A',.91),('x:C',.32),('y:A',.07)]]
        new,full=assemble(base,pairs,scores)
        np.testing.assert_array_equal(full[base.columns],base)
        self.assertEqual(new[c.NEW[1]].tolist(),[.32,0.])
        with self.assertRaises(AssertionError):assemble(base,pairs,scores[:-1])

    def test_cache_corruption_and_identity(self):
        p={'pair_id':'x:A','canonical_id':'x','group':'A','premise':'source','hypothesis':'claim'}
        s={k:p[k] for k in ['pair_id','canonical_id','group']};s.update(logit=0.,consistency=.5)
        a={k:p[k] for k in ['pair_id','canonical_id','group']}
        a.update(original_tokens=8,encoded_tokens=8,truncated=False,premise_tokens_removed=0,
                 hypothesis_tokens_removed=0,batch_padded_length=8)
        payload={'config_sha256':'fixed','pairs_sha256':digest([p]),'pair_ids':['x:A'],'scores':[s],'truncation':[a]}
        cache={**payload,'payload_sha256':digest(payload)}
        self.assertEqual(validate_cache(cache,[p],'fixed'),([s],[a]))
        changed=copy.deepcopy(cache);changed['scores'][0]['consistency']=.7
        with self.assertRaises(AssertionError):validate_cache(changed,[p],'fixed')
        for wrong_batch,wrong_config in [([{**p,'hypothesis':'changed'}],'fixed'),([p],'other')]:
            with self.assertRaises(AssertionError):validate_cache(cache,wrong_batch,wrong_config)
        changed=copy.deepcopy(payload);changed['scores'][0]['consistency']=1.
        changed['payload_sha256']=digest(changed)
        with self.assertRaises(AssertionError):validate_cache(changed,[p],'fixed')

    def test_single_sigmoid_and_pair_masking(self):
        import torch
        from hhem_backend import infer_batch
        from transformers import AutoTokenizer
        tokenizer=AutoTokenizer.from_pretrained(str(c.OUT/'model'),local_files_only=True,trust_remote_code=False)
        class FakeModel:
            def __call__(self,**kw):
                assert kw['input_ids'].shape==kw['attention_mask'].shape
                assert kw['input_ids'].shape[1]<=512
                assert not torch.is_grad_enabled() and torch.is_inference_mode_enabled()
                return type('Outputs',(),{'logits':torch.tensor([[-2.],[0.],[2.]])})()
        pairs=[{'pair_id':str(i),'canonical_id':str(i),'group':'TEST','premise':p,'hypothesis':h}
               for i,(p,h) in enumerate([('Source.','Claim.'),('Long text. '*600,'More text. '*600),('Short.','Short.')])]
        scores,audits=infer_batch(tokenizer,FakeModel(),pairs)
        np.testing.assert_array_equal([s['consistency'] for s in scores],torch.sigmoid(torch.tensor([-2.,0.,2.])).numpy())
        self.assertEqual(scores[1]['consistency'],.5);self.assertTrue(audits[1]['truncated'])

    def test_locked_fold_isolation(self):
        folds=pd.read_csv(c.OUT/'inputs/locked_outer_folds.csv')
        self.assertEqual(folds.fold_id.value_counts().sort_index().tolist(),[113,112,112,112,112])
        seen=[]
        for fold in range(1,6):
            train=folds[folds.fold_id!=fold];valid=folds[folds.fold_id==fold]
            self.assertTrue(set(train.canonical_id).isdisjoint(valid.canonical_id))
            self.assertEqual(len(train)+len(valid),561);seen+=valid.canonical_id.tolist()
        self.assertEqual(len(seen),len(set(seen)));self.assertEqual(set(seen),set(folds.canonical_id))

    def test_metric_and_pairing(self):
        f=pd.DataFrame({'canonical_id':['a','b','c','d'],'label_bin':[0,1,0,1],
                        'p_hallucination':[0.,1.,.2,.8],'E6-v2':[.1,.4,.2,.7],
                        'E6-v3':[.5-.00000000000001,.5,.8,.9]})
        self.assertEqual(metric(f,'E6-v3')['correct'],3)
        p=paired(f);self.assertEqual(p['corrected'],1);self.assertEqual(p['introduced_errors'],1)
        self.assertEqual(p['mcnemar_exact_two_sided_p'],1.)
        self.assertEqual(p['bootstrap']['accuracy_difference'],0.)

    def test_all_sources_compile(self):
        for p in list((c.OUT/'scripts').glob('*.py'))+list((c.OUT/'tests').glob('*.py')):
            compile(p.read_text(encoding='utf-8'),str(p),'exec')

if __name__=='__main__':unittest.main()
