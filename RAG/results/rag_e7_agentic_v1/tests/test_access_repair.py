"""Access-control contracts only; no router evaluation or estimator fitting."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import e7_common as common


class AccessRepairContracts(unittest.TestCase):
    def test_optional_shell_probe_uses_defaults(self):
        import platform
        self.assertEqual(platform._syscmd_ver('system', 'release', 'version'),
                         ('system', 'release', 'version'))

    def test_native_windows_version_and_machine(self):
        import platform
        expected = sys.getwindowsversion().platform_version or sys.getwindowsversion()[:3]
        self.assertEqual(platform.win32_ver()[1], '.'.join(map(str, expected)))
        self.assertEqual(platform.machine(), platform._get_machine_win32())
        self.assertNotEqual(platform.machine(), '')

    def test_network_and_subprocess_still_blocked(self):
        for event in ('socket.connect', 'socket.getaddrinfo', 'subprocess.Popen', 'os.system'):
            self.assertTrue(common.GUARD.probe(event, ()))

    def test_frozen_and_external_writes_still_blocked(self):
        import os
        for path in (common.E6 / 'E6_PROTOCOL.md', common.MIXED, common.FOLDS,
                     common.ROOT / 'RAG/module4_release_v1/README.md',
                     common.ROOT / '.gitignore', Path(os.environ['TEMP']) / 'probe.tmp',
                     Path(os.devnull)):
            self.assertTrue(common.GUARD.probe('open', (str(path), 'w', os.O_WRONLY)))

    def test_official_test_read_still_blocked(self):
        # Synthetic path only; never open or enumerate an official-test dataset.
        path = common.ROOT / 'Labeled test' / 'synthetic-denial-probe.json'
        self.assertTrue(common.GUARD.probe('open', (str(path), 'r', 0)))

    def test_e7_local_write_allowed(self):
        import os
        path = common.OUT / 'tmp' / 'synthetic-policy-probe.tmp'
        common.GUARD.policy('open', (str(path), 'w', os.O_WRONLY))

    def test_integrity_and_no_evaluation_artifacts(self):
        common.verify_integrity()
        self.assertFalse((common.OUT / 'evaluation/evaluation_started.json').exists())
        self.assertFalse(list((common.OUT / 'evaluation').glob('*')))


if __name__ == '__main__':
    guard = common.offline('access_contracts_repaired_v1')
    try:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(AccessRepairContracts)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        common.write_json(common.OUT / 'config/access_contracts_repaired_v1.json', {
            'status': 'PASS' if result.wasSuccessful() and not guard.events else 'FAIL',
            'tests_run': result.testsRun, 'failures': len(result.failures),
            'errors': len(result.errors), 'operational_violations': len(guard.events),
            'scope': 'Diagnostic/access-control contracts; not full E7 router contract suite',
            'rf_fits': 0, 'e7_evaluations': 0, 'e7_scores_observed': 0,
        })
        if not result.wasSuccessful() or guard.events:
            raise SystemExit(1)
    finally:
        guard.save()
