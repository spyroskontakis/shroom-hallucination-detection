"""Offline validation of the existing five returned jobs; no training imports."""
import math
import unittest
import prepare_training as p


class ReturnedResultsTests(unittest.TestCase):
    def test_existing_five_returns(self):
        spec=p.c.read_json(p.HERE/'E11C_TRAINING_PROTOCOL.json')
        ids=[]
        folds={r['canonical_id']:int(r['fold_id']) for r in p.a.csv_rows(p.c.root()/p.a.load_protocol()['data']['folds_path'])}
        for f in range(1,6):
            data=p.c.read_json(p.PRIVATE/f'returned/fold_{f}.json')
            self.assertEqual(data['fold_id'],f)
            s1,s2=data['stages']
            for stage,report in enumerate((s1,s2),1):
                self.assertEqual(report['stage'],stage)
                self.assertEqual(report['protocol_sha256'],spec['protocol_sha256'])
                self.assertTrue(report['losses_all_finite'])
            self.assertEqual(s1['checkpoint_sha256'],s2['initial_model_weights_sha256'])
            self.assertEqual(p.c.digest(data['predictions_jsonl'].encode()),s2['heldout_predictions_sha256'])
            rows=[p.c.strict_json(x) for x in data['predictions_jsonl'].splitlines()]
            self.assertEqual({r['predicted_class'] for r in rows},{0,1})
            for row in rows:
                self.assertEqual(folds[row['sample_id']],f)
                self.assertTrue(math.isfinite(row['p_H']) and 0<=row['p_H']<=1)
            ids.extend(r['sample_id'] for r in rows)
        self.assertEqual(len(ids),561)
        self.assertEqual(len(set(ids)),561)
        self.assertEqual(set(ids),set(folds))
