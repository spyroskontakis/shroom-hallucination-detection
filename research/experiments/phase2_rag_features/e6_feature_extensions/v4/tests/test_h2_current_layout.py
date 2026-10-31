"""Current-layout tests over the unchanged v1 safety engine, entirely offline.

The original v1 suite also runs separately against its authentic prior source
snapshot. That historical result does not claim v1 accepts this new layout.
"""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
import uuid

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / "research/shared_tools/canonical_execution_context.py").is_file())
BASE = ROOT / "research/experiments/phase2_rag_features/e6_feature_extensions/v4"
spec = importlib.util.spec_from_file_location("_e6_current_layout_api", BASE / "verification/h2_adapter_v2.py")
API = importlib.util.module_from_spec(spec)
spec.loader.exec_module(API)

# Reuse the 49 existing tests without editing their source or duplicating their
# validator. Their explicit engine binding now tests the current v2 contract.
spec = importlib.util.spec_from_file_location("_e6_current_reused_tests", BASE / "tests/test_h2_context.py")
_prior_tests = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_prior_tests)
_prior_tests.A = API.implementation(ROOT)


class CurrentEngineTests(_prior_tests.H2Tests):
    pass


class CurrentLayoutTests(unittest.TestCase):
    def setUp(self):
        self.work = Path(os.environ["SHROOM_TEST_SCRATCH"]) / ("e6_current_" + uuid.uuid4().hex)
        self.work.mkdir()

    def test_complete_group_uses_only_final_destinations(self):
        contract = API.contract(ROOT)
        self.assertEqual(len(contract.artifacts), 62)
        for old, item in contract.artifacts.items():
            self.assertTrue(item["current_path"].startswith("research/experiments/phase2_rag_features/e6_feature_extensions/v4/"))
            self.assertFalse((ROOT / old).is_file(), old)
            self.assertEqual(contract.source(old), ROOT / item["current_path"])

    def test_engine_source_is_the_unchanged_original(self):
        raw = (ROOT / API.ENGINE).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), API.ENGINE_SHA256)
        contract = API.contract(ROOT)
        self.assertEqual(contract.data["adapter"]["path"], API.ENGINE)
        self.assertEqual(contract.data["adapter"]["sha256"], API.ENGINE_SHA256)

    def test_old_contract_original_hashes_are_not_refreshed(self):
        before = json.loads((BASE / "configs/current_layout_h2_v1.json").read_bytes())
        after = API.contract(ROOT).data
        self.assertEqual(before["baseline"], after["baseline"])
        self.assertNotEqual(before["version"], after["version"])
        for old, new in zip(before["artifacts"], after["artifacts"]):
            for key in ("historical_path", "h1", "current_sha256", "adapted_source_sha256", "scientific_symbols"):
                self.assertEqual(old[key], new[key], (old["historical_path"], key))

    def test_missing_historical_inputs_fail_before_run_creation(self):
        engine = API.implementation(ROOT)
        original = self.work / "original"
        temporary = self.work / "temporary"
        original.mkdir()
        temporary.mkdir()
        run = self.work / "run"
        with self.assertRaises((ValueError, FileNotFoundError)):
            engine.RuntimeContext(API.contract(ROOT), original, run, temporary, profile="amended")
        self.assertFalse(run.exists())
        self.assertEqual(list(temporary.iterdir()), [])

    def test_current_plan_is_read_only_and_uses_v2(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            result = API.main(["--expected-sha256", API.CONTRACT_SHA256,
                               "--entry", "RAG/results/rag_e6_v4/execution/extract.py"])
        self.assertEqual(result, 0)
        data = json.loads(buffer.getvalue())
        self.assertEqual(data["version"], "shroom-e6-v4-h2-v2")
        self.assertEqual(data["created_files"], 0)
        self.assertEqual(data["source_check"]["raw_artifacts"], 62)
        self.assertEqual(data["mode"], "PLAN_ONLY")

    def test_unknown_entry_is_not_replaced_by_another_source(self):
        with self.assertRaises(ValueError):
            API.main(["--expected-sha256", API.CONTRACT_SHA256, "--entry", "unknown.py"])

    def test_wrong_external_pin_is_rejected(self):
        with self.assertRaises(ValueError):
            API.contract(ROOT, expected_sha256="0" * 64)

    def test_wrong_cli_pin_is_rejected_before_engine(self):
        with patch.object(API, "implementation", side_effect=AssertionError("must not load")):
            with self.assertRaises(ValueError):
                API.main(["--expected-sha256", "0" * 64])

    def test_changed_engine_is_rejected_before_execution(self):
        path = self.work / API.ENGINE
        path.parent.mkdir(parents=True)
        path.write_text("raise AssertionError('must not execute')", encoding="utf-8")
        with self.assertRaises(ValueError):
            API.implementation(self.work)

    def test_relative_and_traversal_source_roots_rejected(self):
        for root in (Path("."), self.work / ".." / "other"):
            with self.assertRaises(ValueError):
                API.implementation(root)

    def test_tampered_current_contract_cannot_fall_back_to_v1(self):
        path = ROOT / API.DEFAULT_CONTRACT
        raw = path.read_bytes()
        obj = json.loads(raw)
        obj["version"] = "shroom-e6-v4-h2-v1"
        altered = json.dumps(obj).encode()
        old_read = Path.read_bytes
        with patch.object(Path, "read_bytes", lambda p: altered if p == path else old_read(p)):
            with self.assertRaises(ValueError):
                API.contract(ROOT)

    def test_execution_requires_separate_original_run_and_temp_roots(self):
        env = {key: value for key, value in os.environ.items()
               if key not in ("SHROOM_E6_V4_ORIGINAL_ROOT", "SHROOM_E6_V4_RUN_DIR", "SHROOM_E6_V4_TEMP_ROOT")}
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(ValueError):
                API.main(["--expected-sha256", API.CONTRACT_SHA256, "--execute",
                          "--entry", "RAG/results/rag_e6_v4/execution/extract.py"])

    def test_historical_v1_stays_fail_closed_on_a_new_layout(self):
        spec = importlib.util.spec_from_file_location("_e6_explicit_historical_v1", ROOT / API.ENGINE)
        old = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(old)
        path = ROOT / old.DEFAULT_CONTRACT
        with self.assertRaises((ValueError, FileNotFoundError)):
            old.Contract(ROOT, path, hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
