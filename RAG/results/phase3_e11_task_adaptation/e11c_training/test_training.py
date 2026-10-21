import ast
import unittest
from pathlib import Path
import prepare_training as p
import train_stages as train


class TrainingTests(unittest.TestCase):
    def test_leakage_ignores_labels_and_catches_source(self):
        human={'task':'PG','src':' A source ','tgt':'target','hyp':'heldout','label':0}
        row={'sample_key':'x','task':'PG','src':'a SOURCE','tgt':'other','hyp':'different'}
        self.assertEqual(p.purge([row],[human])[0],[])
        changed={**human,'label':1,'p_hallucination':0.99}
        self.assertEqual(p.purge([row],[human]),p.purge([row],[changed]))

    def test_fixed_stage2_and_split_integrity(self):
        spec=p.c.read_json(p.HERE/'E11C_TRAINING_PROTOCOL.json')
        original=p.a.load_protocol()
        self.assertEqual(spec['stage2'],original['training'])
        self.assertEqual(spec['model'],original['model'])
        self.assertEqual(spec['input'],original['input'])
        self.assertEqual(spec['stage1']['epochs'],1)
        for f,meta in spec['folds'].items():
            folder=p.PRIVATE/f'fold_{f}'
            for name,digest in meta['files_sha256'].items():self.assertEqual(p.c.sha(folder/name),digest)
            trainrows=p.c.read_rows(folder/'train.jsonl');heldout=p.c.read_rows(folder/'heldout.jsonl')
            self.assertTrue(all(r['fold_id']!=int(f) for r in trainrows))
            self.assertTrue(all(r['fold_id']==int(f) for r in heldout))
            self.assertEqual((folder/'train.jsonl').read_bytes(),(p.E11/f'e11a_prepared/fold_{f}/train.jsonl').read_bytes())
            self.assertEqual((folder/'heldout.jsonl').read_bytes(),(p.E11/f'e11a_prepared/fold_{f}/heldout.jsonl').read_bytes())

    def test_no_heldout_leakage_and_homogeneous_pool(self):
        spec=p.c.read_json(p.HERE/'E11C_TRAINING_PROTOCOL.json')
        pool={r['sample_key']:r for r in p.c.load_candidates()}
        accepted={r['sample_key'] for r in p.c.read_rows(p.production.PRIVATE/'future_binary_supervision.jsonl')}
        humans=p.a.csv_rows(p.c.root()/p.a.load_protocol()['data']['canonical_path'])
        folds={r['canonical_id']:int(r['fold_id']) for r in p.a.csv_rows(p.c.root()/p.a.load_protocol()['data']['folds_path'])}
        for f in range(1,6):
            rows=p.c.read_rows(p.PRIVATE/f'fold_{f}/synthetic.jsonl')
            ids=[r['sample_id'] for r in rows]
            self.assertEqual(len(ids),len(set(ids)))
            self.assertTrue(set(ids)<=accepted)
            _,removed=p.purge([pool[k] for k in ids],[r for r in humans if folds[r['canonical_id']]==f])
            self.assertEqual(removed,[])

    def test_exact_e11a_training_loop_and_schedule(self):
        original=(p.E11/'e11a_train_fold.py').read_text()
        current=(p.HERE/'train_stages.py').read_text()
        start='    optimizer = torch.optim.AdamW'
        end='    checkpoint = target / "final_checkpoint"'
        self.assertEqual(original[original.index(start):original.index(end)],current[current.index(start):current.index(end)])
        self.assertAlmostEqual(train.linear_lr(1e-5,1,100,10),1e-6)
        self.assertEqual(train.linear_lr(1e-5,100,100,10),0)
        for name in ('train_stages.py','modal_training.py','prepare_training.py'):
            ast.parse((p.HERE/name).read_text())


if __name__=='__main__':unittest.main()
