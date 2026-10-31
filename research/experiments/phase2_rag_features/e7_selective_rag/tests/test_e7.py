"""Synthetic router and real label-free alignment contracts; no model fitting."""
import math
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import e7_common as common


class RouterContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Import scientific libraries only after the main entry point installs
        # the process-local offline/access guard and Windows import repair.
        import pandas as pd
        import router
        cls.pd = pd
        cls.router = router

    @staticmethod
    def observation(evidence=True, score=0.4):
        return {'evidence_available': evidence, 'top1_cosine': score}

    def fixture(self):
        metadata, signals = [], []
        for fold in range(1, 6):
            for evidence in (True, False):
                cid = f'synthetic_f{fold}_{"evidence" if evidence else "empty"}'
                metadata.append({'canonical_id': cid, 'fold_id': fold,
                                 'task': 'DM' if evidence else ('MT' if fold % 2 else 'PG')})
                signals.append({
                    'canonical_id': cid, 'evidence_available': int(evidence),
                    'candidate_count': 1 if evidence else 0,
                    'selected_sense_count': 1 if evidence else 0,
                    'top1_cosine': fold / 8 if evidence else None,
                    'top2_cosine': None, 'top1_minus_top2': None,
                })
        return self.pd.DataFrame(metadata), self.pd.DataFrame(signals)

    def assert_rejected(self, function, *args):
        with self.assertRaises((ValueError, TypeError, AssertionError, KeyError)):
            function(*args)

    def test_frozen_observation_names_and_route_names(self):
        self.assertEqual(tuple(self.router.OBSERVATIONS),
                         ('evidence_available', 'top1_cosine'))
        self.assertEqual(self.router.USE, 'USE_EXTERNAL_EVIDENCE')
        self.assertEqual(self.router.FALLBACK, 'FALLBACK_TO_BASE')

    def test_observation_schema_rejects_forbidden_extra_keys(self):
        forbidden = ('label', 'labels', 'label_bin', 'gold_label',
                     'p_hallucination', 'hyp', 'tgt', 'prediction', 'predictions',
                     'E3_correctness', 'E6_correctness', 'validation_performance',
                     'canonical_id', 'fold_id', 'task', 'candidate_count',
                     'top2_cosine', 'top1_minus_top2')
        for key in forbidden:
            with self.subTest(key=key):
                observation = dict(self.observation(), **{key: 0})
                self.assert_rejected(self.router.fit_threshold, [observation])
                self.assert_rejected(self.router.choose_route, observation, 0.3)

    def test_observation_schema_rejects_missing_keys(self):
        for key in self.router.OBSERVATIONS:
            with self.subTest(key=key):
                observation = self.observation()
                del observation[key]
                self.assert_rejected(self.router.fit_threshold, [observation])
                self.assert_rejected(self.router.choose_route, observation, 0.3)

    def test_evidence_scores_must_be_finite_and_cosine_range(self):
        for score in (None, math.nan, math.inf, -math.inf, 1.1, -1.1):
            with self.subTest(score=score):
                observation = self.observation(score=score)
                self.assert_rejected(self.router.fit_threshold, [observation])
                self.assert_rejected(self.router.choose_route, observation, 0.3)

    def test_valid_cosine_endpoints_and_negative_values(self):
        observations = [self.observation(score=s) for s in (-1.0, -0.5, 1.0)]
        self.assertEqual(self.router.fit_threshold(observations), -0.5)
        self.assertEqual(self.router.choose_route(observations[0], -0.5),
                         self.router.FALLBACK)
        self.assertEqual(self.router.choose_route(observations[-1], -0.5),
                         self.router.USE)

    def test_threshold_is_linear_median_not_nearest_observation(self):
        observations = [self.observation(score=s) for s in (0.1, 0.8)]
        self.assertAlmostEqual(self.router.fit_threshold(observations), 0.45)

    def test_no_evidence_returns_missing_threshold(self):
        self.assertIsNone(self.router.fit_threshold([]))
        self.assertIsNone(self.router.fit_threshold([self.observation(False, None)]))

    def test_no_evidence_rows_do_not_contribute_to_median(self):
        observations = [self.observation(score=0.2), self.observation(False, None),
                        self.observation(score=0.8), self.observation(False, None)]
        self.assertEqual(self.router.fit_threshold(observations), 0.5)

    def test_missing_evidence_always_falls_back(self):
        for threshold in (None, -1.0, 0.0, 1.0):
            with self.subTest(threshold=threshold):
                self.assertEqual(self.router.choose_route(self.observation(False, None), threshold),
                                 self.router.FALLBACK)

    def test_missing_training_threshold_falls_back_even_with_evidence(self):
        self.assertEqual(self.router.choose_route(self.observation(score=1.0), None),
                         self.router.FALLBACK)

    def test_inconsistent_absent_evidence_score_rejected(self):
        observation = self.observation(False, 0.4)
        self.assert_rejected(self.router.fit_threshold, [observation])
        self.assert_rejected(self.router.choose_route, observation, 0.3)

    def test_equality_is_inclusive_without_epsilon(self):
        threshold = 0.4
        self.assertEqual(self.router.choose_route(self.observation(score=threshold), threshold),
                         self.router.USE)
        self.assertEqual(self.router.choose_route(
            self.observation(score=math.nextafter(threshold, -math.inf)), threshold),
            self.router.FALLBACK)
        self.assertEqual(self.router.choose_route(
            self.observation(score=math.nextafter(threshold, math.inf)), threshold),
            self.router.USE)

    def test_invalid_threshold_rejected(self):
        for threshold in (math.nan, math.inf, -math.inf, -1.1, 1.1):
            with self.subTest(threshold=threshold):
                self.assert_rejected(self.router.choose_route, self.observation(), threshold)

    def test_five_fold_medians_use_only_training_evidence(self):
        metadata, signals = self.fixture()
        routes, details = self.router.plan_routes(metadata, signals)
        expected_medians = (0.4375, 0.4375, 0.375, 0.3125, 0.3125)
        self.assertEqual(set(details), set(map(str, range(1, 6))))
        for fold, expected in enumerate(expected_medians, 1):
            with self.subTest(fold=fold):
                detail = details[str(fold)]
                train_ids = set(metadata.loc[metadata.fold_id != fold, 'canonical_id'])
                validation_ids = set(metadata.loc[metadata.fold_id == fold, 'canonical_id'])
                train_evidence_ids = {f'synthetic_f{f}_evidence' for f in range(1, 6) if f != fold}
                self.assertAlmostEqual(detail['threshold'], expected)
                self.assertEqual(set(detail['train_ids']), train_ids)
                self.assertEqual(set(detail['validation_ids']), validation_ids)
                self.assertEqual(set(detail['train_evidence_ids']), train_evidence_ids)
                self.assertFalse(set(detail['train_ids']) & set(detail['validation_ids']))
                self.assertTrue((routes.loc[routes.fold_id == fold, 'threshold']
                                 .sub(expected).abs() < 1e-15).all())

    def test_validation_score_cannot_change_its_fold_threshold(self):
        metadata, signals = self.fixture()
        _, before = self.router.plan_routes(metadata, signals)
        changed = signals.copy()
        changed.loc[changed.canonical_id == 'synthetic_f1_evidence', 'top1_cosine'] = 0.99
        _, after = self.router.plan_routes(metadata, changed)
        self.assertEqual(before['1']['threshold'], after['1']['threshold'])
        self.assertEqual(before['1']['train_evidence_ids'], after['1']['train_evidence_ids'])

    def test_all_rows_have_one_route_and_terminate_in_end(self):
        metadata, signals = self.fixture()
        routes, _ = self.router.plan_routes(metadata, signals)
        self.assertEqual(len(routes), len(metadata))
        self.assertEqual(routes.canonical_id.nunique(), len(metadata))
        self.assertEqual(routes.canonical_id.tolist(), metadata.canonical_id.tolist())
        self.assertEqual(routes.fold_id.tolist(), metadata.fold_id.tolist())
        self.assertEqual(routes.task.tolist(), metadata.task.tolist())
        self.assertTrue((routes.decision_count == 1).all())
        self.assertEqual(set(routes.route), {self.router.USE, self.router.FALLBACK})
        self.assertEqual(int((routes.route == self.router.USE).sum()), 3)
        self.assertTrue((routes.loc[routes.evidence_available == 0, 'route'] ==
                         self.router.FALLBACK).all())
        for row in routes.itertuples(index=False):
            outcome = self.router.finish_prediction(row.route, {'E3': 0.25, 'E6': 0.75})
            self.assertEqual(outcome['decision_count'], 1)
            self.assertEqual(outcome['states'], ['START', 'RETRIEVE', 'ASSESS_EVIDENCE',
                                                row.route, 'PREDICT', 'END'])
            self.assertEqual(outcome['states'][-1], 'END')

    def test_bookkeeping_schema_excludes_labels(self):
        metadata, signals = self.fixture()
        for key in ('label', 'p_hallucination', 'hyp', 'prediction'):
            with self.subTest(frame='metadata', key=key):
                self.assert_rejected(self.router.plan_routes, metadata.assign(**{key: 0}), signals)
            with self.subTest(frame='signals', key=key):
                self.assert_rejected(self.router.plan_routes, metadata, signals.assign(**{key: 0}))

    def test_missing_bookkeeping_fields_rejected(self):
        metadata, signals = self.fixture()
        for key in metadata.columns:
            with self.subTest(frame='metadata', key=key):
                self.assert_rejected(self.router.plan_routes, metadata.drop(columns=key), signals)
        for key in signals.columns:
            with self.subTest(frame='signals', key=key):
                self.assert_rejected(self.router.plan_routes, metadata, signals.drop(columns=key))

    def test_duplicate_or_mismatched_ids_rejected(self):
        metadata, signals = self.fixture()
        duplicated_metadata = metadata.copy()
        duplicated_metadata.loc[1, 'canonical_id'] = duplicated_metadata.loc[0, 'canonical_id']
        self.assert_rejected(self.router.plan_routes, duplicated_metadata, signals)
        duplicated_signals = signals.copy()
        duplicated_signals.loc[1, 'canonical_id'] = duplicated_signals.loc[0, 'canonical_id']
        self.assert_rejected(self.router.plan_routes, metadata, duplicated_signals)
        mismatched_signals = signals.copy()
        mismatched_signals.loc[0, 'canonical_id'] = 'synthetic_unknown_id'
        self.assert_rejected(self.router.plan_routes, metadata, mismatched_signals)

    def test_prediction_selects_only_the_fixed_route_path(self):
        paths = {'E3': 0.2, 'E6': 0.8}
        self.assertEqual(self.router.finish_prediction(self.router.USE, paths)['prediction'], 0.8)
        self.assertEqual(self.router.finish_prediction(self.router.FALLBACK, paths)['prediction'], 0.2)
        self.assert_rejected(self.router.finish_prediction, 'RETRY', paths)

    def test_path_predictions_are_finite_and_in_closed_unit_interval(self):
        for path in ('E3', 'E6'):
            for value in (math.nan, math.inf, -math.inf, -0.01, 1.01, None):
                for route in (self.router.USE, self.router.FALLBACK):
                    with self.subTest(path=path, value=value, route=route):
                        paths = {'E3': 0.2, 'E6': 0.8}
                        paths[path] = value
                        self.assert_rejected(self.router.finish_prediction, route, paths)
        for value in (0.0, 1.0):
            for route in (self.router.USE, self.router.FALLBACK):
                outcome = self.router.finish_prediction(route, {'E3': value, 'E6': value})
                self.assertEqual(outcome['prediction'], value)


class GuardContracts(unittest.TestCase):
    def test_threading_runtime_without_estimator_fitting(self):
        from joblib import Parallel, delayed
        self.assertEqual(Parallel(n_jobs=-1, prefer='threads')(
            delayed(abs)(x) for x in [-3, 2, -1]), [3, 2, 1])

    def test_real_data_preflight_and_all_routes_label_free(self):
        import numpy as np
        import router
        preflight = common.initial_preflight()
        self.assertEqual(preflight['status'], 'PASS')
        features, metadata, predictors, evaluator = common.aligned_label_free()
        signals = common.retrieval_metadata(metadata.canonical_id.tolist())
        routes, details = router.plan_routes(metadata, signals)
        self.assertEqual(len(routes), 561)
        self.assertEqual(routes.canonical_id.nunique(), 561)
        self.assertEqual(set(routes.route), {router.USE, router.FALLBACK})
        for fold in range(1, 6):
            train = (metadata.fold_id != fold) & (signals.evidence_available == 1)
            self.assertEqual(details[str(fold)]['threshold'],
                             float(np.quantile(signals.loc[train, 'top1_cosine'], .5, method='linear')))
            self.assertEqual(details[str(fold)]['train_evidence_ids'],
                             metadata.loc[train, 'canonical_id'].tolist())
        self.assertTrue((routes.decision_count == 1).all())

    def test_network_is_denied_without_an_actual_network_call(self):
        for event in ('socket.connect', 'socket.connect_ex', 'socket.getaddrinfo',
                      'socket.bind', 'socket.sendto', 'socket.sendmsg'):
            with self.subTest(event=event):
                self.assertTrue(common.GUARD.probe(event, ()))

    def test_child_processes_are_denied_without_launching_one(self):
        for event in ('subprocess.Popen', 'os.system', 'os.exec', 'os.posix_spawn'):
            with self.subTest(event=event):
                self.assertTrue(common.GUARD.probe(event, ()))

    def test_frozen_write_is_denied_without_touching_artifacts(self):
        for path in (common.E6 / 'E6_PROTOCOL.md', common.MIXED, common.FOLDS,
                     common.ROOT / '.gitignore'):
            with self.subTest(path=str(path)):
                self.assertTrue(common.GUARD.probe('open', (str(path), 'w', os.O_WRONLY)))

    def test_official_test_read_is_denied_without_loading_data(self):
        path = common.ROOT / 'Labeled test' / 'synthetic-e7-denial-probe.json'
        self.assertTrue(common.GUARD.probe('open', (str(path), 'r', 0)))

    def test_protocol_and_protected_artifact_integrity(self):
        freeze = common.verify_integrity()
        self.assertEqual(freeze['protocol_sha256'],
                         '0491505c0f98a2a4d2a0896370adbbc3674c6fdf873b96a8a31833e587923002')


if __name__ == '__main__':
    guard = common.offline('e7_contracts_v1')
    try:
        suite = unittest.TestSuite([
            unittest.defaultTestLoader.loadTestsFromTestCase(RouterContracts),
            unittest.defaultTestLoader.loadTestsFromTestCase(GuardContracts),
        ])
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        successful = result.wasSuccessful() and not guard.events
        common.write_json(common.OUT / 'config/e7_contracts.json', {
            'status': 'PASS' if successful else 'FAIL', 'finished_utc': common.now(),
            'tests_run': result.testsRun, 'failures': len(result.failures),
            'errors': len(result.errors), 'skipped': len(result.skipped),
            'failure_details': [{'test': test.id(), 'traceback': detail}
                                for test, detail in result.failures + result.errors],
            'operational_violations': len(guard.events),
            'synthetic_guard_probes': len(guard.probes),
            'scope': 'Synthetic router/state-machine/access contracts, real label-free '
                     'data alignment and zero-fit joblib threading smoke; no scoring',
            'rf_fits': 0, 'e7_evaluations': 0, 'e7_scores_observed': 0,
            'implementation_sha256': {
                p.relative_to(common.OUT).as_posix(): common.sha(p)
                for folder in ('scripts', 'tests')
                for p in sorted((common.OUT / folder).glob('*.py'))},
        })
        if not successful:
            raise SystemExit(1)
    finally:
        guard.save()
