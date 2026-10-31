"""Offline contracts: synthetic data only; no API/model calls."""
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import e9_common as c
import decomposer as d
from aggregates import nli, minicheck, append_features


class Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (Path(__file__).parent / 'tmp').mkdir(exist_ok=True)

    def setUp(self):
        self.value = {'task': 'PG', 'hyp': 'Ada arrived.'}
        self.output = {'selection': 'semantic', 'disambiguation': 'clear', 'claims': [{
            'claim_index': 0,
            'claim_text': 'Ada arrived.', 'supporting_quotes': ['Ada arrived.'],
            'entailed_by_hyp': True, 'atomic': True, 'self_contained': True}]}

    def test_prompt_boundary(self):
        for forbidden in ['label', 'p_hallucination', 'src', 'tgt', 'source', 'target', 'fold_id', 'prediction', 'canonical_id']:
            with self.assertRaises(ValueError):
                d.payload({**self.value, forbidden: 'secret'})
        request = d.payload(self.value)
        self.assertEqual(json.loads(request['messages'][1]['content']), self.value)
        self.assertEqual(request['model'], 'gpt-4o-2024-08-06')
        self.assertEqual(request['temperature'], 0)

    def test_quotes_and_quality(self):
        self.assertEqual(d.validate(self.output, self.value['hyp']), ['Ada arrived.'])
        self.output['claims'][0]['supporting_quotes'] = ['Ada left.']
        with self.assertRaises(ValueError):
            d.validate(self.output, self.value['hyp'])

    def test_single_claim_is_verbatim(self):
        self.output['claims'][0]['claim_text'] = 'Someone arrived.'
        with self.assertRaises(ValueError):
            d.validate(self.output, self.value['hyp'])

    def test_definition_fragment_allowed(self):
        hyp = 'Resembling a weasel.'
        self.output['disambiguation'] = 'unresolved'
        claim = self.output['claims'][0]
        claim.update(claim_text=hyp, supporting_quotes=[hyp], self_contained=False)
        self.assertEqual(d.validate(self.output, hyp), [hyp])

    def test_indices_reject_duplicates(self):
        self.output['claims'][0]['claim_index'] = 1
        with self.assertRaises(ValueError):
            d.validate(self.output, self.value['hyp'])

    def test_cache(self):
        counts = dict(llm_calls=0, cache_hits=0, fallbacks=0)
        def fake(request):
            return {'output': self.output, 'model_snapshot': d.MODEL}
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent / 'tmp') as path:
            first = d.decompose(self.value, path, counts, fake)
            second = d.decompose(self.value, path, counts, lambda _: self.fail('cache missed'))
        self.assertEqual(first, second)
        self.assertEqual(counts, dict(llm_calls=1, cache_hits=1, fallbacks=0))
        self.assertNotEqual(d.cache_key(self.value), d.cache_key({**self.value, 'hyp': 'Ada left.'}))

    def test_fallback(self):
        empty = {'selection': 'none', 'disambiguation': 'unresolved', 'claims': []}
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent / 'tmp') as path:
            record = d.decompose(self.value, path, dict(llm_calls=0, cache_hits=0, fallbacks=0),
                                 lambda _: {'output': empty, 'model_snapshot': d.MODEL})
        self.assertEqual(record['claims'], [self.value['hyp']])
        self.assertEqual(record['decomposition_fallback'], 1)

    def test_availability_is_not_fallback(self):
        def blocked(_):
            raise d.BlockedAPI('blocked')
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent / 'tmp') as path:
            with self.assertRaises(d.BlockedAPI):
                d.decompose(self.value, path, dict(llm_calls=0, cache_hits=0, fallbacks=0), blocked)
            self.assertEqual(list(Path(path).iterdir()), [])

    def test_missing_key_without_network(self):
        with patch.dict('os.environ', {}, clear=True), patch('urllib.request.urlopen') as network:
            with self.assertRaises(d.BlockedAPI):
                d.call_api(d.payload(self.value))
            network.assert_not_called()

    def test_retry_limit_and_fallback(self):
        counts = dict(llm_calls=0, cache_hits=0, fallbacks=0)
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent / 'tmp') as path, patch.object(d.time, 'sleep'):
            record = d.decompose(self.value, path, counts, lambda _: {'output': {}, 'model_snapshot': d.MODEL})
        self.assertEqual(counts['llm_calls'], 3)
        self.assertEqual(record['claims'], [self.value['hyp']])
        self.assertEqual(record['decomposition_status'], 'fallback_invalid_after_retries')

    def test_cache_tampering(self):
        counts = dict(llm_calls=0, cache_hits=0, fallbacks=0)
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent / 'tmp') as path:
            record = d.decompose(self.value, path, counts, lambda _: {'output': self.output, 'model_snapshot': d.MODEL})
            cached = Path(path) / (record['cache_hash'] + '.json')
            record['claims'] = ['A fabricated claim.']
            cached.write_text(json.dumps(record), encoding='utf-8')
            with self.assertRaises(ValueError):
                d.decompose(self.value, path, counts, lambda _: self.fail('corrupt cache must hard fail'))

    def test_aggregates(self):
        a = nli([[.7, .2, .1], [.1, .2, .7]])
        self.assertEqual(list(a), c.A)
        self.assertAlmostEqual(a['claim_unsupported_ratio'], .5)
        self.assertAlmostEqual(a['claim_min_entailment_contradiction_margin'], -.6)
        self.assertEqual(nli([[.5, .5, 0]])['claim_unsupported_ratio'], 0)
        b = minicheck([.5])
        self.assertEqual(b['minicheck_unsupported_ratio'], 0)
        self.assertEqual(b['minicheck_support_std'], 0)
        with self.assertRaises(ValueError):
            nli([])
        with self.assertRaises(ValueError):
            minicheck([float('nan')])

    def test_append_integrity(self):
        base = pd.DataFrame({'canonical_id': [str(i) for i in range(561)], 'frozen': np.arange(561)})
        extra = pd.DataFrame({'canonical_id': base.canonical_id, **{k: np.zeros(561) for k in c.A}})
        joined = append_features(base, extra, c.A)
        self.assertTrue(joined[base.columns].equals(base))
        with self.assertRaises(ValueError):
            append_features(base, extra.iloc[:-1], c.A)
        with self.assertRaises(ValueError):
            append_features(base, extra.iloc[::-1], c.A)
        with self.assertRaises(ValueError):
            append_features(base, extra[extra.columns[::-1]], c.A)

    def test_paired_identical(self):
        result = c.paired([0, 1], [.1, .8], [.1, .8])
        self.assertEqual(result['bootstrap_95_ci'], [0, 0])
        self.assertEqual(result['mcnemar_exact_p'], 1)


if __name__ == '__main__':
    (Path(__file__).parent / 'tmp').mkdir(exist_ok=True)
    unittest.main()
