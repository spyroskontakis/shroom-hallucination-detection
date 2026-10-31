"""Offline tests: pinned tokenizer, source equivalence and temporary synthetic returns."""
import ast
import contextlib
import copy
import csv
import io
import json
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch
import factcg_common as c
import factcg_backend as backend
import return_to_local as local
import run_factcg_gpu as runner

class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m, cls.inputs = c.validate_inputs()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='e10_synthetic_')
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.output = self.folder / 'factcg_scores.jsonl'
        self.rows = [dict(canonical_id=r['canonical_id'], support_probability=(i % 3) / 2,
                         model_id=c.MODEL, inference_metadata=c.row_metadata(self.m, r)) for i, r in enumerate(self.inputs)]

    def save(self, rows=None):
        self.output.write_text(''.join(json.dumps(r) + '\n' for r in (self.rows if rows is None else rows)), encoding='utf-8')

    def report(self):
        c.write(self.folder / 'FACTCG_GPU_REPORT.json', dict(status='PASS', model_loaded=True,
                samples_processed=561, retries=0, inference_errors=[], output_sha256=c.sha(self.output),
                manifest_sha256=c.sha(c.HERE / 'GPU_RUN_MANIFEST.json'), model_id=c.MODEL,
                model_revision=c.REVISION, settings=c.SETTINGS, dependencies=self.m['dependency_versions'],
                device=dict(cuda_available=True, torch_cuda='12.1')))

    def test_complete_shuffled_scores(self):
        self.save(list(reversed(self.rows)))
        self.report()
        self.assertEqual(len(c.validate_outputs(self.output, self.folder / 'FACTCG_GPU_REPORT.json')), 561)

    def test_missing_duplicate_extra_unknown_ids(self):
        bad = copy.deepcopy(self.rows)
        bad[0]['canonical_id'] = 'UNKNOWN'
        for rows in [self.rows[:-1], self.rows + [self.rows[0]], [self.rows[0]] + self.rows[:-1], bad]:
            self.save(rows)
            with self.assertRaises(ValueError):
                c.validate_outputs(self.output)

    def test_bad_probabilities(self):
        for p in [-0.1, 1.1, float('nan'), float('inf'), True, '0.5', None]:
            self.rows[0]['support_probability'] = p
            self.save()
            with self.subTest(p=p), self.assertRaises(ValueError):
                c.validate_outputs(self.output)

    def test_model_metadata_and_extra_fields(self):
        for k, v in [('model_id', 'another/model'), ('inference_metadata', {}), ('label', 1)]:
            rows = copy.deepcopy(self.rows)
            rows[0][k] = v
            self.save(rows)
            with self.assertRaises(ValueError):
                c.validate_outputs(self.output)

    def test_report_hash_and_status(self):
        self.save()
        self.report()
        self.rows[0]['support_probability'] = 0.12
        self.save()
        with self.assertRaises(ValueError):
            c.validate_outputs(self.output, self.folder / 'FACTCG_GPU_REPORT.json')

    def test_exact_36_cells_plus_one_raw_feature(self):
        self.save(list(reversed(self.rows)))
        self.report()
        out = local.build(self.output, self.folder / 'matrix')
        with out.open(encoding='utf-8', newline='') as f:
            new = list(csv.reader(f))
        with (c.ROOT / 'RAG/results/rag_e6_v3/features/e6_v3_36_features.csv').open(encoding='utf-8', newline='') as f:
            old = list(csv.reader(f))
        self.assertEqual(len(new), 562)
        self.assertTrue(all(len(row) == 38 for row in new))
        self.assertEqual([row[:37] for row in new], old)
        expected = {r['canonical_id']: r['support_probability'] for r in self.rows}
        self.assertTrue(all(float(row[-1]) == expected[row[0]] for row in new[1:]))
        with self.assertRaises(FileExistsError):
            local.build(self.output, out.parent)

    def test_input_content_and_field_tamper(self):
        package = self.folder / 'package'
        package.mkdir()
        for name in self.m['package_sha256']:
            dest = package / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(c.HERE / name, dest)
        shutil.copyfile(c.HERE / 'GPU_RUN_MANIFEST.json', package / 'GPU_RUN_MANIFEST.json')
        with patch.object(c, 'HERE', package):
            c.validate_inputs()
            with (package / 'factcg_inputs.jsonl').open('a') as f:
                f.write('\n')
            with self.assertRaisesRegex(ValueError, 'package hash'):
                c.validate_inputs()

    def test_duplicate_json_keys(self):
        with self.assertRaises(ValueError):
            c.loads('{"canonical_id":"a", "canonical_id":"b"}')

    def test_block_on_windows_and_no_cuda(self):
        with patch.object(runner.platform, 'system', return_value='Windows'):
            with self.assertRaisesRegex(runner.Blocked, 'Linux'):
                runner.preflight(self.m, {})
        fake_torch = types.SimpleNamespace(__version__='2.2.1', version=types.SimpleNamespace(cuda=None),
                                          cuda=types.SimpleNamespace(is_available=lambda: False))
        with patch.object(runner.platform, 'system', return_value='Linux'), \
             patch.object(runner.platform, 'machine', return_value='x86_64'), \
             patch.object(runner.metadata, 'version', side_effect=lambda name: self.m['dependency_versions'][name]), \
             patch.object(runner.subprocess, 'run', return_value=types.SimpleNamespace(returncode=0, stdout='', stderr='')), \
             patch.dict(sys.modules, {'torch': fake_torch}):
            with self.assertRaisesRegex(runner.Blocked, 'CPU fallback prohibited'):
                runner.preflight(self.m, {})

    def test_mock_complete_runner_and_import(self):
        def fake_preflight(m, report):
            report['dependencies'] = m['dependency_versions']
            report['device'] = dict(cuda_available=True, torch_cuda='12.1')
        with patch.object(runner, 'preflight', side_effect=fake_preflight), \
             patch.object(backend, 'load', return_value=(None, None)), \
             patch.object(backend, 'score', return_value=(0.5, dict(reference_chunks=1, truncated_chunks=0, max_untruncated_tokens=20))), \
             contextlib.redirect_stdout(io.StringIO()):
            dest = self.folder / 'mock_gpu'
            code = runner.execute(dest, True, self.folder / 'cache')
        self.assertEqual(code, 0)
        self.assertEqual(len(c.validate_outputs(dest / 'factcg_scores.jsonl', dest / 'FACTCG_GPU_REPORT.json')), 561)

    def test_mock_inference_failure_no_complete_output(self):
        with patch.object(runner, 'preflight'), patch.object(backend, 'load', return_value=(None, None)), \
             patch.object(backend, 'score', side_effect=RuntimeError('synthetic backend error')), \
             contextlib.redirect_stdout(io.StringIO()):
            dest = self.folder / 'mock_failure'
            self.assertEqual(runner.execute(dest, True, self.folder / 'cache'), 1)
        self.assertFalse((dest / 'factcg_scores.jsonl').exists())
        self.assertEqual(c.read(dest / 'FACTCG_GPU_REPORT.json')['status'], 'FAIL')

    def test_rf_requires_explicit_flag(self):
        result = subprocess.run([sys.executable, '-B', str(c.HERE / 'evaluate_e10.py')], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('--run-rf', result.stderr)
        self.assertFalse((c.HERE.parent / 'evaluation/E10').exists())

    def test_original_e9_and_minicheck_unchanged(self):
        for name, expected in self.m['preexisting_e9_sha256'].items():
            self.assertEqual(c.sha(c.ROOT / name), expected, name)

class OfficialSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import nltk
        from transformers import AutoTokenizer
        nltk.data.path.insert(0, str(c.HERE / 'nltk_data'))
        cls.tokenizer = AutoTokenizer.from_pretrained(str(c.HERE / 'tokenizer_snapshot'), use_fast=True, local_files_only=True)
        tree = ast.parse((c.HERE / 'upstream/factcg/inference.py').read_text())
        node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Inferencer')
        ns = dict(nltk=nltk, sent_tokenize=nltk.sent_tokenize, List=list,
                  INSTRUCTION_TEMPLATE=backend.INSTRUCTION_TEMPLATE)
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<official class, no model initialization>', 'exec'), ns)
        cls.official = ns['Inferencer'].__new__(ns['Inferencer'])
        cls.official.model_name = 'microsoft/deberta-v3-large'

    def test_official_template_exact(self):
        ns = {}
        exec((c.HERE / 'upstream/factcg/utils.py').read_text(), ns)
        self.assertEqual(backend.INSTRUCTION_TEMPLATE, ns['INSTRUCTION_TEMPLATE'])

    def test_reference_chunk_equivalence(self):
        _, rows = c.validate_inputs()
        examples = [r['reference_text'] for r in rows] + ['', 'word ' * 560 + '.', 'First.\nSecond.', ('A sentence with words. ' * 200)]
        for text in examples:
            self.assertEqual(backend.chunk_reference(text), self.official.chunking_src(text))

    def test_real_pinned_tokenization_all_561_and_long_input(self):
        import numpy as np
        class NumpyTokenizer:
            def __init__(self, original):
                object.__setattr__(self, 'original', original)
            def __getattr__(self, name):
                return getattr(self.original, name)
            def __setattr__(self, name, value):
                setattr(self.original, name, value)
            def __call__(self, *args, **kwargs):
                # Tensor container only; IDs/masks and all tokenization kwargs stay identical.
                self_test.assertEqual(kwargs.pop('return_tensors'), 'pt')
                return self.original(*args, **kwargs, return_tensors='np')
        self_test = self
        tokenizer = NumpyTokenizer(self.tokenizer)
        self.official.tokenizer = tokenizer
        _, rows = c.validate_inputs()
        pairs = [(chunk, r['whole_hypothesis']) for r in rows for chunk in backend.chunk_reference(r['reference_text'])]
        pairs.append(('word ' * 3000, 'Full hypothesis. Another sentence.'))
        for reference, hypothesis in pairs:
            expected = self.official.tokenize([reference], [hypothesis])
            actual = backend.tokenize(tokenizer, [reference], [hypothesis])
            self.assertEqual(set(expected), set(actual))
            for field in expected:
                self.assertTrue(np.array_equal(expected[field], actual[field]))
            self.assertLessEqual(actual['input_ids'].shape[-1], 2048)

if __name__ == '__main__':
    unittest.main(verbosity=2)
