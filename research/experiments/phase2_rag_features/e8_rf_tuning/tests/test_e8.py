"""Pre-fit E8 contracts using synthetic fixtures; zero estimator fits."""
import copy
import unittest
import numpy as np
import pandas as pd
from nested_rf import configurations, metrics, select, generate_splits, validate_splits, tune_training_only


def fixture():
    rows = []
    for i in range(561):
        rows.append({'canonical_id': f'mock-{i:04d}', 'fold_id': i % 5 + 1,
                     'task': ['DM', 'MT', 'PG'][i % 3], 'label_bin': (i // 3) % 2,
                     'p_hallucination': ((i // 3) % 2) * .8 + .1, 'feature': float(i)})
    return pd.DataFrame(rows)


class Contracts(unittest.TestCase):
    def scores(self):
        return [{'configuration': f'C{i}', 'order': i, 'accuracy': .8, 'spearman': .6} for i in range(6)]

    def test_exact_order_and_only_two_parameter_changes(self):
        configs = configurations()
        self.assertEqual([c['id'] for c in configs], [f'C{i}' for i in range(6)])
        self.assertEqual([(c['parameters']['min_samples_leaf'], c['parameters']['max_features']) for c in configs],
                         [(1,1.0),(3,1.0),(5,1.0),(1,.5),(3,.5),(5,.5)])
        base = configs[0]['parameters']
        self.assertEqual(len(base),18)
        for c in configs:
            self.assertTrue({k for k in base if base[k] != c['parameters'][k]} <= {'min_samples_leaf','max_features'})

    def test_accuracy_priority(self):
        scores = self.scores(); scores[2].update(accuracy=.81, spearman=-.8)
        self.assertEqual(select(scores),'C2')

    def test_spearman_secondary(self):
        scores = self.scores(); scores[4]['spearman'] = .7
        self.assertEqual(select(scores),'C4')

    def test_first_configuration_full_tie(self):
        self.assertEqual(select(self.scores()),'C0')

    def test_undefined_correlation_ranks_last(self):
        scores = self.scores()
        for i,r in enumerate(scores): r['spearman'] = [None, float('nan'), -.9, None, None, None][i]
        self.assertEqual(select(scores),'C2')
        for r in scores: r['spearman'] = None
        self.assertEqual(select(scores),'C0')

    def test_threshold_rounding_and_undefined_metrics(self):
        m = metrics([0,1],[.1,.9],[.5-1e-14,.5])
        self.assertEqual(m['correct'],2)
        self.assertIsNone(m['spearman'])  # Rounded predictions are constant.
        self.assertIsNone(metrics([0],[.2],[.3])['spearman'])

    def test_actual_strata_use_label_bin(self):
        f = fixture(); a=generate_splits(f)
        f['p_hallucination'] = .99
        self.assertEqual(a,generate_splits(f))

    def test_split_determinism_and_isolation(self):
        f = fixture(); a = generate_splits(f)
        self.assertEqual(a,generate_splits(f))
        validate_splits(a,f.canonical_id.tolist())
        damaged = copy.deepcopy(a)
        damaged[0]['inner'][0]['train_ids'][0] = a[0]['validation_ids'][0]
        with self.assertRaises(AssertionError): validate_splits(damaged,f.canonical_id.tolist())

    def test_insufficient_stratum_rejected(self):
        f = fixture(); f.loc[1,'task']='rare'
        with self.assertRaises(AssertionError): generate_splits(f)

    def test_selector_only_sees_training_shared_splits_and_pooled_scores(self):
        f=fixture(); split=generate_splits(f)[0]
        frame=f.set_index('canonical_id',drop=False).loc[split['train_ids']].reset_index(drop=True)
        frame=frame[['canonical_id','task','label_bin','p_hallucination','feature']]
        calls=[]
        index=frame.set_index('canonical_id')
        def fake(x,y,v,cfg,ti,vi,k):
            self.assertTrue(set(ti).isdisjoint(split['validation_ids']))
            self.assertTrue(set(vi).isdisjoint(split['validation_ids']))
            np.testing.assert_array_equal(x,index.loc[ti,['feature']].to_numpy(float))
            np.testing.assert_array_equal(y,index.loc[ti,'p_hallucination'].to_numpy(float))
            calls.append((cfg['id'],k,ti,vi))
            return index.loc[vi,'p_hallucination'].to_numpy() if k==1 else 1-index.loc[vi,'p_hallucination'].to_numpy()
        scores, winner, oof = tune_training_only(frame,split['inner'],configurations(),['feature'],fake)
        self.assertEqual(len(calls),18); self.assertEqual(winner,'C0')
        expected=len(split['inner'][0]['validation_ids'])/len(frame)
        self.assertEqual(scores[0]['accuracy'],expected)
        self.assertEqual(len(oof),6*len(frame))
        for cfg in range(6):
            self.assertEqual([(k,ti,vi) for _,k,ti,vi in calls[cfg*3:cfg*3+3]],
                             [(k,ti,vi) for _,k,ti,vi in calls[:3]])
        for forbidden in ['E6','fold_id','outer_label']:
            with self.assertRaises(AssertionError):
                tune_training_only(frame.assign(**{forbidden:0}),split['inner'],configurations(),['feature'],fake)
