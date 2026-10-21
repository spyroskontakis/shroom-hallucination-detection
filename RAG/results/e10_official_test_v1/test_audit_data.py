import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import audit_data as audit


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
