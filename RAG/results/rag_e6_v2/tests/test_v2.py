"""Focused E6-v2 feature-direction, fallback and metric contracts; no real fits."""
import unittest
import numpy as np
import pandas as pd
import v2_common as c
from prepare_inputs import pair_rows
from extract_features import assemble
from evaluate_v2 import metric


class Contracts(unittest.TestCase):
    def fixtures(self):
        rows=[{'canonical_id':task,'task':task,'src':f'{task} source','tgt':f'{task} target','hyp':f'{task} answer'}
              for task in ['DM','MT','PG']]
        definition={'rank':1,'score':.6,'evidence_id':'EXACT-V1','candidate_definition':'saved selected definition'}
        later={'rank':2,'score':.4,'evidence_id':'LATER','candidate_definition':'must not replace first'}
        ranking=[{'canonical_id':r['canonical_id'],'selected':[definition,later] if r['task']=='DM' else []} for r in rows]
        base=pd.DataFrame([{'canonical_id':r['canonical_id'],'rag_evidence_available':int(r['task']=='DM'),
                            'rag_sense_count':2 if r['task']=='DM' else 0,'rag_retrieval_top1_cosine':.6 if r['task']=='DM' else 0,
                            'unchanged_numeric':.12345678901234567} for r in rows])
        return rows,ranking,base

    def test_task_reference_and_both_directions(self):
        rows,ranking,base=self.fixtures();pairs,mapping=pair_rows(rows,ranking,base)
        by={p['pair_id']:p for p in pairs}
        for row in rows:
            cid=row['canonical_id'];ref=row['src'] if cid=='PG' else row['tgt']
            self.assertEqual((by[cid+':A']['premise'],by[cid+':A']['hypothesis']),(ref,row['hyp']))
            self.assertEqual((by[cid+':B']['premise'],by[cid+':B']['hypothesis']),(row['hyp'],ref))
        self.assertEqual(by['DM:C']['premise'],'saved selected definition')
        self.assertEqual(by['DM:C']['hypothesis'],'DM answer')
        self.assertNotIn('MT:C',by);self.assertNotIn('PG:C',by)

    def test_labels_and_missing_fields_rejected(self):
        rows,rank,base=self.fixtures()
        for field in ['label','labels','label_bin','p_hallucination','prediction']:
            with self.assertRaises(AssertionError):pair_rows([{**rows[0],field:0}],rank,base)
        with self.assertRaises(AssertionError):pair_rows([{**rows[0],'hyp':''}],rank,base)

    def test_fallback_preserves_ab_and_initial_features(self):
        rows,ranking,base=self.fixtures();pairs,_=pair_rows(rows,ranking,base)
        scores=[{**{k:p[k] for k in ['pair_id','canonical_id','group']},'entailment':.2,'neutral':.3,'contradiction':.5} for p in pairs]
        extra,full=assemble(base,pairs,list(reversed(scores)))
        np.testing.assert_array_equal(full[base.columns].to_numpy(),base.to_numpy())
        self.assertEqual(extra.columns.tolist(),['canonical_id']+c.NEW)
        self.assertTrue((extra.iloc[1:,7:]==0).all().all())
        self.assertTrue((extra[c.NEW[:6]]>0).all().all())

    def test_bad_probabilities_and_duplicate_pairs_rejected(self):
        rows,ranking,base=self.fixtures();pairs,_=pair_rows(rows,ranking,base)
        scores=[{**{k:p[k] for k in ['pair_id','canonical_id','group']},'entailment':.2,'neutral':.3,'contradiction':.5} for p in pairs]
        with self.assertRaises(AssertionError):assemble(base,pairs,scores+[scores[0]])
        scores[0]['neutral']=float('nan')
        with self.assertRaises(AssertionError):assemble(base,pairs,scores)

    def test_label_order_and_feature_order(self):
        self.assertEqual(c.LABELS,['entailment','neutral','contradiction'])
        self.assertEqual(len(c.NEW),9);self.assertEqual(len(set(c.NEW)),9)
        self.assertEqual(c.NEW[0],'nli2_ref_hyp_entailment')
        self.assertEqual(c.NEW[-1],'nli2_definition_hyp_contradiction')

    def test_accuracy_unrounded_spearman_rounded(self):
        f=pd.DataFrame({'label_bin':[0,1],'p_hallucination':[.1,.9],'prediction':[.5-1e-14,.5]})
        m=metric(f,'prediction');self.assertEqual(m['correct'],2);self.assertIsNone(m['spearman'])

    def test_source_compiles_before_freeze(self):
        for p in (c.OUT/'scripts').glob('*.py'):compile(p.read_text(encoding='utf-8'),str(p),'exec')
