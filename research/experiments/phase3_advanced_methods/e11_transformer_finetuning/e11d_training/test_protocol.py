import json
import unittest
from prepare import HERE, E11, sha_file

class ProtocolTests(unittest.TestCase):
    def test_all_inherited_settings_exact(self):
        a=json.loads((E11/'E11A_TRAINING_PROTOCOL.json').read_text())
        d=json.loads((HERE/'E11D_LOSS_PROTOCOL.json').read_text())
        for key in ('data','model','input','reference_policy','training','output'):
            self.assertEqual(a[key],d[key])
        self.assertEqual(d['lambda'],.1);self.assertEqual(d['margin'],0)
        self.assertEqual(d['synthetic_rows'],0);self.assertEqual(d['fits'],5)

    def test_frozen_runtime_allowlist(self):
        manifest=json.loads((HERE/'RUNTIME_MANIFEST.json').read_text())
        rows=[name for name in manifest if name.endswith('.jsonl')]
        self.assertEqual(set(rows),{f'e11a_prepared/fold_{f}/{split}.jsonl' for f in range(1,6) for split in ('train','heldout')})
        for entry in manifest.values(): self.assertEqual(sha_file(HERE/entry['local_path']),entry['sha256'])

    def test_optimizer_schedule_and_inference_unchanged(self):
        a=(E11/'e11a_train_fold.py').read_text()
        d=(HERE/'train_fold.py').read_text()
        for start,end in [('def linear_lr(', '\n\ndef execute'),('    epochs = ', '    losses = []'),('            if (batch_idx + 1)', '        epoch_losses ='),('    if mode == "fold":\n        heldout', '    status_name =')]:
            self.assertEqual(a[a.index(start):a.index(end,a.index(start))],d[d.index(start):d.index(end,d.index(start))])

if __name__=='__main__':unittest.main()
