"""Offline contract tests; tiny in-memory fixtures, no datasets or model inference."""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_features as build


def query_row(**changes):
    row = {'example_id': 'mock-id', 'task': 'DM', 'term': 'river',
           'src': 'mock context', 'rag_applicable': '1'}
    row.update(changes)
    return row


def candidate(evidence, entry='entry-b'):
    return {'evidence_id': evidence, 'source_entry_id': entry,
            'source': 'enwiktionary', 'term_key': 'river',
            'candidate_term': 'river', 'candidate_context': f'context {evidence}',
            'candidate_definition': f'definition {evidence}'}


class E6Contracts(unittest.TestCase):
    def test_ranking_rejects_answer_reference_labels_and_predictions(self):
        for forbidden in ('tgt', 'hyp', 'label', 'labels', 'label_bin',
                          'p_hallucination', 'prediction', 'oof_prediction'):
            with self.subTest(column=forbidden):
                def forbidden_backend(_):
                    self.fail('Rejected inputs must not invoke a backend')
                with self.assertRaisesRegex(ValueError, 'query projection'):
                    build.reconstruct([query_row(**{forbidden: 'forbidden'})],
                                      [candidate('evidence-a')], forbidden_backend)

    def test_frozen_query_candidate_representation_and_tie_break(self):
        # Five retained candidates must come from the original score/ID ordering.
        records = [candidate('z', 'entry-z'), candidate('b', 'entry-a'),
                   candidate('a', 'entry-a'), candidate('f', 'entry-b'),
                   candidate('d', 'entry-b'), candidate('c', 'entry-b')]
        seen = []

        def equal_embedding(texts):
            seen.append(texts)
            return np.tile([3.0, 4.0], (len(texts), 1))

        ranked = build.reconstruct([query_row()], records, equal_embedding)[0]
        self.assertEqual(seen, [['river\nmock context'] +
                                [f"river\n{r['candidate_context']}" for r in records]])
        self.assertEqual(ranked['candidate_count'], 6)
        self.assertEqual([r['evidence_id'] for r in ranked['selected']], ['a', 'b', 'c', 'd', 'f'])
        self.assertEqual([r['rank'] for r in ranked['selected']], [1, 2, 3, 4, 5])
        np.testing.assert_allclose([r['score'] for r in ranked['selected']], 1.0,
                                   atol=1e-15, rtol=0)

    def test_first_definition_and_premise_hypothesis_direction(self):
        records = [candidate('second'), candidate('first')]

        def ranking_embedding(texts):
            # Query [1,0], second [0,1], first [1,0].
            return np.asarray([[1., 0.], [0., 1.], [1., 0.]])

        ranked = build.reconstruct([query_row()], records, ranking_embedding)[0]
        definition = ranked['selected'][0]['candidate_definition']
        self.assertEqual(definition, 'definition first')
        embedding_calls, nli_calls = [], []

        def semantic_embedding(texts):
            embedding_calls.append(texts)
            return np.asarray([[0., 2.], [3., 0.]], dtype=np.float32)

        def nli(pairs):
            nli_calls.append(pairs)
            return [{'entailment': .2, 'neutral': .3, 'contradiction': .5}]

        values = build.compare_hyp(definition, 'generated answer', semantic_embedding, nli)
        self.assertEqual(embedding_calls, [['generated answer', 'definition first']])
        self.assertEqual(nli_calls, [[('definition first', 'generated answer')]])
        self.assertEqual(list(values), build.NEW)
        self.assertEqual(list(values.values()), [0., .2, .3, .5])

    def test_fallbacks_do_not_call_backends_and_return_four_zeros(self):
        def forbidden_backend(_):
            self.fail('Fallback must not invoke a backend')

        for row, records in [(query_row(), []),
                             (query_row(task='MT'), [candidate('a')]),
                             (query_row(task='PG'), [candidate('a')]),
                             (query_row(rag_applicable='0'), [candidate('a')])]:
            with self.subTest(task=row['task'], applicable=row['rag_applicable']):
                ranking = build.reconstruct([row], records, forbidden_backend)
                self.assertEqual(ranking[0]['selected'], [])
        self.assertEqual(build.compare_hyp(None, 'unused answer', forbidden_backend,
                                          forbidden_backend), dict.fromkeys(build.NEW, 0.))

    def test_predictors_preserve_e5_order_and_append_exactly_four(self):
        self.assertEqual(len(build.FEATURES), 25)
        self.assertEqual(build.FEATURES[:21], build.evaluator.E3 + build.evaluator.RAG)
        self.assertEqual(build.FEATURES[21:], build.NEW)
        self.assertEqual(len(set(build.FEATURES)), 25)


if __name__ == '__main__':
    unittest.main()
