"""Reject malformed OOF results without accepting incorrect experiment identity."""
import copy
import unittest
from evaluate import validate_rows, collect, HERE

class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.human={'a':{'label_bin':'0','task':'DM'},'b':{'label_bin':'1','task':'PG'}}
        self.folds={'a':1,'b':1}
        self.rows=[{'sample_id':'a','fold_id':1,'task':'DM','gold_label':0,'p_H':.2,'predicted_class':0},{'sample_id':'b','fold_id':1,'task':'PG','gold_label':1,'p_H':.8,'predicted_class':1}]

    def test_valid(self): validate_rows(self.rows,self.human,self.folds)

    def test_duplicate_missing_rejected(self):
        for rows in (self.rows[:1],self.rows+[self.rows[0]],[self.rows[0]]*2):
            with self.assertRaises(ValueError): validate_rows(rows,self.human,self.folds)

    def test_nonfinite_out_of_range_rejected(self):
        for p in (float('nan'),float('inf'),-.01,1.01):
            rows=copy.deepcopy(self.rows);rows[0]['p_H']=p
            with self.assertRaises(ValueError): validate_rows(rows,self.human,self.folds)

    def test_fold_task_label_threshold_drift(self):
        for key,value in [('fold_id',2),('task','MT'),('gold_label',1),('predicted_class',1)]:
            rows=copy.deepcopy(self.rows);rows[0][key]=value
            with self.assertRaises(ValueError): validate_rows(rows,self.human,self.folds)

    def test_class_collapse(self):
        rows=copy.deepcopy(self.rows);rows[1].update(p_H=.1,predicted_class=0)
        with self.assertRaises(ValueError): validate_rows(rows,self.human,self.folds)

    @unittest.skipUnless((HERE/'private/returned/fold_5.json').exists(),'training not complete')
    def test_actual_returns(self):
        rows,reports,_,_=collect()
        self.assertEqual(len(rows),561);self.assertEqual(len(reports),5)

if __name__=='__main__':unittest.main()
