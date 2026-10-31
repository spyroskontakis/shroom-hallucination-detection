"""Offline contract tests. Synthetic scores exist only in temporary directories."""
import copy
import csv
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import gpu_common as g
import return_to_local as local
import run_minicheck_gpu as runner

class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m, cls.inputs = g.validate_inputs()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='e9_synthetic_test_')
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'scores.jsonl'
        self.rows = [dict(canonical_id=r['canonical_id'], claim_index=r['claim_index'],
                         support_probability=[0.0, 0.5, 1.0][i % 3], model_id=g.MODEL,
                         inference_metadata=g.output_metadata(self.m, r)) for i, r in enumerate(self.inputs)]

    def save(self, rows=None):
        self.path.write_text(''.join(json.dumps(r) + '\n' for r in (self.rows if rows is None else rows)), encoding='utf-8')

    def report(self):
        g.write(self.path.parent / 'MINICHECK_GPU_REPORT.json', dict(status='PASS', model_loaded=True,
                claims_processed=575, inference_errors=[], retries=0, output_sha256=g.sha(self.path),
                manifest_sha256=g.sha(g.HERE / 'GPU_RUN_MANIFEST.json'), settings=g.SETTINGS,
                model_id=g.MODEL, model_revision=g.REVISION))

    def test_valid_complete_and_shuffled(self):
        self.save(list(reversed(self.rows)))
        self.assertEqual(len(g.validate_outputs(self.path)), 575)

    def test_missing_duplicate_extra(self):
        for rows in [self.rows[:-1], self.rows + [self.rows[0]], [self.rows[0]] + self.rows[:-1]]:
            with self.subTest(count=len(rows)):
                self.save(rows)
                with self.assertRaises(ValueError):
                    g.validate_outputs(self.path)

    def test_bad_probability(self):
        for p in [float('nan'), float('inf'), -0.01, 1.01, True, '0.5', None]:
            with self.subTest(p=p):
                self.rows[0]['support_probability'] = p
                self.save()
                with self.assertRaises(ValueError):
                    g.validate_outputs(self.path)

    def test_wrong_id_index_model_metadata_fields(self):
        changes = [('canonical_id', 'unknown'), ('claim_index', True), ('claim_index', 99),
                   ('model_id', 'other/model'), ('inference_metadata', {}), ('label', 1)]
        for name, value in changes:
            rows = copy.deepcopy(self.rows)
            rows[0][name] = value
            self.save(rows)
            with self.subTest(name=name), self.assertRaises(ValueError):
                g.validate_outputs(self.path)

    def test_strict_json(self):
        with self.assertRaises(ValueError):
            g.loads('{"x": 1, "x": 2}')

    def test_aggregate_boundary_std(self):
        values = g.aggregate([0, 0.5, 1])
        self.assertEqual(values[:3], [0.5, 0, 1])
        self.assertAlmostEqual(values[3], math.sqrt(1 / 6))
        self.assertEqual(values[4], 1 / 3)
        self.assertEqual(g.aggregate([0.5]), [0.5, 0.5, 0.5, 0, 0])

    def test_import_preserves_44_cells_and_49_features(self):
        self.save(list(reversed(self.rows)))
        self.report()
        result = local.build(self.path, Path(self.tmp.name) / 'matrix')
        with result.open(newline='', encoding='utf-8') as f:
            new = list(csv.reader(f))
        with (g.HERE.parent / 'features/E9-A.csv').open(newline='', encoding='utf-8') as f:
            old = list(csv.reader(f))
        self.assertEqual(len(new), 562)
        self.assertTrue(all(len(r) == 50 for r in new))
        self.assertEqual([r[:45] for r in new], old)
        with self.assertRaises(FileExistsError):
            local.build(self.path, result.parent)

    def test_report_hash_failure(self):
        self.save()
        self.report()
        self.rows[0]['support_probability'] = 0.125
        self.save()
        with self.assertRaises(ValueError):
            g.validate_outputs(self.path, self.path.parent / 'MINICHECK_GPU_REPORT.json')

    def test_input_tamper(self):
        with patch.object(g, 'HERE', Path(self.tmp.name)):
            for name in ['GPU_RUN_MANIFEST.json', 'minicheck_inputs.jsonl']:
                (g.HERE / name).write_bytes((local.HERE / name).read_bytes())
            with (g.HERE / 'minicheck_inputs.jsonl').open('a') as f:
                f.write('\n')
            with self.assertRaises((ValueError, FileNotFoundError)):
                g.validate_inputs()

    def test_windows_preflight_blocks_without_loading(self):
        with patch.object(runner.platform, 'system', return_value='Windows'):
            with self.assertRaisesRegex(runner.Blocked, 'Linux'):
                runner.preflight(self.m, {})

    def test_preexisting_e9_unchanged(self):
        for name, expected in self.m['preexisting_e9_sha256'].items():
            self.assertEqual(g.sha(g.HERE.parents[3] / name), expected, name)

if __name__ == '__main__':
    unittest.main(verbosity=2)
