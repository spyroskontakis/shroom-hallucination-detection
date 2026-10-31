import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Current-layout test loader. H1 source identity is distinct from H0 data replay.
import hashlib
import importlib.util
import sys


def _load_audit_source(origin=__file__):
    root = next((p for p in Path(origin).resolve().parents
                 if (p / ".git").exists()
                 and (p / "research/shared_tools/canonical_execution_context.py").is_file()), None)
    if root is None:
        raise RuntimeError("Reviewed checkout root not found")
    def load(name, path, expected):
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise RuntimeError("Reviewed source identity mismatch")
        if name in sys.modules:
            module = sys.modules[name]
            if Path(module.__file__).resolve() != path.resolve():
                raise RuntimeError("Ambiguous preloaded source")
            return module
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            exec(compile(raw, str(path), "exec"), module.__dict__)
        except BaseException:
            sys.modules.pop(name, None)
            raise
        return module
    support_path = root / "research/shared_tools/canonical_execution_context.py"
    support = load("canonical_execution_context", support_path,
                   "c668cce4282d6865373f50525fc78fb5a87b5be14463cc4fef3e93284b326247")
    support.confined(root, "research/shared_tools/canonical_execution_context.py")
    path = support.confined(root, "research/experiments/phase3_advanced_methods/e10_factcg/retrospective_official_test/audit_data.py")
    return load("audit_data", path, "a55837297bb51463e2a372cbe8486aca37609226271dc51311328be8a7803d71")


audit = _load_audit_source()



class ProjectionTests(unittest.TestCase):
    def project(self, rows):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'fixture.json'
            path.write_text(json.dumps(rows, ensure_ascii=False), encoding='utf-8')
            return audit.sanitized_test(path)

    def test_gold_values_never_decoded(self):
        decoder = json.JSONDecoder
        decoded = []

        class ObservedDecoder(decoder):
            def raw_decode(self, *args, **kwargs):
                value, end = super().raw_decode(*args, **kwargs)
                decoded.append(value)
                return value, end

        row = {'id': 9, 'task': 'DM', 'src': 'context', 'tgt': 'reference',
               'hyp': 'answer', 'label': 'SECRET_GOLD',
               'labels': ['SECRET_GOLD', {'nested': 'SECRET_GOLD'}],
               'p(Hallucination)': 0.123456789}
        with patch.object(audit.json, 'JSONDecoder', ObservedDecoder):
            projected, fields = self.project([row])
        self.assertEqual(set(projected[0]), {'id', 'task', 'src', 'tgt', 'hyp'})
        self.assertNotIn('SECRET_GOLD', str(decoded))
        self.assertNotIn(0.123456789, decoded)
        self.assertIn('label', fields[0])

    def test_nested_escaped_and_unicode_skipping(self):
        rows = [{'labels': ['braces } ] and \\"', {'x': [None, True, 2]}],
                 'label': 'ετικέτα', 'p(Hallucination)': None,
                 'id': 1, 'task': 'PG', 'src': 'κείμενο', 'hyp': 'text'}]
        result, _ = self.project(rows)
        self.assertEqual(result, [{k: v for k, v in rows[0].items() if k in audit.SAFE}])

    def test_empty_and_multiple_rows(self):
        self.assertEqual(self.project([]), ([], []))
        self.assertEqual(self.project([{'id': 1}, {'id': 2}])[0], [{'id': 1}, {'id': 2}])

    def test_full_example_and_source_pair_distinguished(self):
        a = dict(task='MT', src=' same  source ', tgt='target', hyp='first')
        b = dict(task='MT', src='same source', tgt='target', hyp='second')
        self.assertNotEqual(audit.key(a), audit.key(b))
        self.assertEqual(audit.key(a, ('task', 'src', 'tgt')),
                         audit.key(b, ('task', 'src', 'tgt')))

    def test_malformed_value_rejected(self):
        with self.assertRaises((ValueError, AssertionError, IndexError)):
            audit.skip_value('[{"unterminated": true]', 0)


if __name__ == '__main__':
    unittest.main()
