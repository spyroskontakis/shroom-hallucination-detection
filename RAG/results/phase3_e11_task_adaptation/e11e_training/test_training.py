import unittest
from e11e_common import *


class FrozenTrainingTests(unittest.TestCase):
    def test_exact_c_settings(self):
        c=read(C/'E11C_TRAINING_PROTOCOL.json');e=read(HERE/'E11E_TRAINING_PROTOCOL.json')
        for k in ('model','input','stage1','stage2','output','folds','folds_sha256','seed','fits','requirements_sha256','teacher_protocol_sha256'):
            self.assertEqual(c[k],e[k])
        self.assertEqual(e['contrastive_applies_to_stages'],[1,2])
        self.assertEqual(e['stage1']['epochs'],1);self.assertEqual(e['stage2']['epochs'],5)

    def test_exact_d_loss_and_settings(self):
        self.assertEqual((HERE/'contrastive.py').read_bytes(),(D/'contrastive.py').read_bytes())
        d=read(D/'E11D_LOSS_PROTOCOL.json');e=read(HERE/'E11E_TRAINING_PROTOCOL.json')
        for k,v in e['contrastive'].items(): self.assertEqual(v,d[k])
        dcode=(D/'train_fold.py').read_text();ecode=(HERE/'train_stages.py').read_text()
        for start,end in [('    masks = sequence_masks(encoded)','    generator ='),('                outputs = model(', '            require(bool(torch.isfinite(loss)')]:
            self.assertEqual(dcode[dcode.index(start):dcode.index(end,dcode.index(start))],ecode[ecode.index(start):ecode.index(end,ecode.index(start))])

    def test_exact_prepared_data_and_exclusions(self):
        e=read(HERE/'E11E_TRAINING_PROTOCOL.json')
        self.assertEqual([e['folds'][str(f)]['synthetic_rows'] for f in range(1,6)],[11787,11791,11795,11787,11790])
        for f,meta in e['folds'].items():
            for name,sha in meta['files_sha256'].items():
                path=HERE/f'private/fold_{f}'/name
                self.assertEqual(sha_file(path),sha)
                self.assertEqual(path.read_bytes(),(C/f'private/fold_{f}'/name).read_bytes())
        checks=read(HERE/'PRETRAINING_CHECKS.json')
        self.assertEqual(checks['synthetic_pool'],11887)
        self.assertEqual(checks['uncertain_excluded'],109)
        self.assertEqual(checks['Azure_rescue_excluded'],4)
        self.assertEqual(checks['duplicate_input_exclusions'],82)
        self.assertEqual(checks['validation_overlap_exclusions'],[18,14,10,18,15])

    def test_unchanged_c_schedule_optimizer_inference(self):
        c=(C/'train_stages.py').read_text();e=(HERE/'train_stages.py').read_text()
        for start,end in [('def linear_lr(', '\n\ndef execute'),('    generator =', '    losses = []'),('            if (batch_idx + 1)', '        epoch_losses ='),('    if stage == 2:\n        heldout', '    status_name =')]:
            self.assertEqual(c[c.index(start):c.index(end,c.index(start))],e[e.index(start):e.index(end,e.index(start))])

    def test_content_hash_and_initialization_chain_guard(self):
        e=read(HERE/'E11E_TRAINING_PROTOCOL.json')
        self.assertEqual(digest(encoded({k:v for k,v in e.items() if k!='protocol_sha256'})),e['protocol_sha256'])
        for name,sha in e['runtime_code_sha256'].items():self.assertEqual(sha_file(HERE/name),sha)
        code=(HERE/'train_stages.py').read_text()
        self.assertIn("previous['protocol_sha256']==spec0['protocol_sha256']",code)
        self.assertIn("sha_file(model_dir/'model.safetensors')==previous['checkpoint_sha256']",code)


if __name__=='__main__':unittest.main()
