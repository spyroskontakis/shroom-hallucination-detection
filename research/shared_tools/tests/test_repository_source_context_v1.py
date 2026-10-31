"""Offline context tests: no historical experiment module is imported."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import unittest
import uuid

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / "research/shared_tools/canonical_execution_context.py").is_file())
SOURCE = ROOT / "research/shared_tools/repository_source_context_v1.py"
spec = importlib.util.spec_from_file_location("_source_context_under_test", SOURCE)
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)
LOG = "RAG/results/phase3_e11_task_adaptation/e11c_training/FINAL_TEST_e11.txt"


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.scratch = Path(os.environ["SHROOM_TEST_SCRATCH"]) / ("source_" + uuid.uuid4().hex)
        self.scratch.mkdir()
        self.root = self.scratch / "fixture"
        self.root.mkdir()
        for relative in (api.SHARED, api.CATALOG):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        self.context = api.SourceContext(self.root)
        self.entry = self.context.entries[LOG]
        self.target = self.root / self.entry["target_path"]
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes((ROOT / self.entry["target_path"]).read_bytes())

    def test_exact_catalog_and_context_version(self):
        self.assertEqual(api.VERSION, "shroom-repository-source-context-v1")
        self.assertEqual(len(self.context.catalog["artifacts"]), 796)

    def test_current_bytes_positive(self):
        self.assertEqual(self.context.check(LOG, mode="H2_CURRENT")["status"], "PASS")

    def test_missing_current_does_not_use_historical(self):
        self.target.unlink()
        old = self.root / LOG
        old.parent.mkdir(parents=True)
        old.write_bytes((ROOT / self.entry["target_path"]).read_bytes())
        self.assertEqual(self.context.check(LOG, mode="H2_CURRENT")["status"], "MISSING")

    def test_corrupt_current_rejected(self):
        self.target.write_bytes(b"changed")
        self.assertEqual(self.context.check(LOG, mode="H2_CURRENT")["status"], "FAIL")

    def test_unimplemented_source_not_certified(self):
        result = self.context.check("codex/canonical_evaluation_data_prep.py", mode="H2_CURRENT")
        self.assertEqual(result["status"], "NOT VERIFIED")

    def test_h0_requires_a_named_original_contract(self):
        with self.assertRaises(ValueError):
            self.context.check(LOG, mode="H0_REPLAY")

    def test_historical_fixture_sha_blob_and_size(self):
        old = self.root / LOG
        old.parent.mkdir(parents=True)
        old.write_bytes(self.target.read_bytes())
        evidence = self.context.h.FileEvidence(self.root, mode="H1_SNAPSHOT",
                                               baseline_commit=api.BASELINE, baseline_tree=api.BASE_TREE)
        self.assertEqual(self.context.check(LOG, mode="H1_SNAPSHOT", evidence=evidence)["status"], "PASS")

    def test_wrong_baseline_fails_closed(self):
        evidence = self.context.h.FileEvidence(self.root, mode="H1_SNAPSHOT",
                                               baseline_commit="0" * 40, baseline_tree=api.BASE_TREE)
        self.assertEqual(self.context.check(LOG, mode="H1_SNAPSHOT", evidence=evidence)["status"], "FAIL")

    def test_mode_substitution_rejected(self):
        evidence = self.context.h.FileEvidence(self.root, mode="H1_SNAPSHOT",
                                               baseline_commit=api.BASELINE, baseline_tree=api.BASE_TREE)
        self.assertEqual(self.context.check(LOG, mode="H2_CURRENT", evidence=evidence)["status"], "FAIL")

    def test_unrecognized_version(self):
        with self.assertRaises(ValueError):
            api.SourceContext(self.root, version="other-v1")

    def test_unrecognized_independent_pin(self):
        with self.assertRaises(ValueError):
            api.SourceContext(self.root, catalog_sha256="0" * 64)

    def test_catalog_corruption(self):
        (self.root / api.CATALOG).write_bytes(b"{}")
        with self.assertRaises(ValueError):
            api.SourceContext(self.root)

    def test_shared_validator_corruption(self):
        (self.root / api.SHARED).write_bytes(b"raise RuntimeError('must not execute')")
        with self.assertRaises(ValueError):
            api.SourceContext(self.root)

    def test_relative_source_root_rejected(self):
        with self.assertRaises(ValueError):
            api.SourceContext(Path("relative"))

    def test_unknown_original_rejected(self):
        with self.assertRaises(ValueError):
            self.context.check("unknown.py", mode="H2_CURRENT")

    def test_original_traversal_rejected(self):
        with self.assertRaises(ValueError):
            self.context.check("../escape", mode="H2_CURRENT")

    def test_original_ads_rejected(self):
        with self.assertRaises(ValueError):
            self.context.check("file:stream", mode="H2_CURRENT")

    def test_original_backslash_rejected(self):
        with self.assertRaises(ValueError):
            self.context.check("folder\\file", mode="H2_CURRENT")

    def test_original_device_rejected(self):
        with self.assertRaises(ValueError):
            self.context.check("folder/CON.txt", mode="H2_CURRENT")

    def test_missing_h0_inputs_remain_missing(self):
        result = self.context.frozen_inputs("E11_NORMALIZATION", self.scratch)
        self.assertNotEqual(result["status"], "PASS")
        self.assertFalse(result["execution_permitted"])

    def test_unknown_h0_contract_rejected(self):
        result = self.context.frozen_inputs("INVENTED", self.scratch)
        self.assertEqual(result["status"], "FAIL")

    def plan(self, **overrides):
        args = dict(run_dir=self.scratch / "run", cache_dir=self.scratch / "cache",
                    temporary_dir=self.scratch / "tmp")
        args.update(overrides)
        return self.context.audit_plan([LOG], **args)

    def test_audit_plan_no_writes_or_execution(self):
        before = sorted(p.relative_to(self.scratch).as_posix() for p in self.scratch.rglob("*"))
        result = self.plan()
        self.assertFalse(result["created"])
        self.assertFalse(result["execution_permitted"])
        self.assertEqual(before, sorted(p.relative_to(self.scratch).as_posix() for p in self.scratch.rglob("*")))

    def test_existing_run_rejected(self):
        run = self.scratch / "run"
        run.mkdir()
        with self.assertRaises(ValueError):
            self.plan(run_dir=run)

    def test_git_run_rejected(self):
        (self.scratch / ".git").mkdir()
        with self.assertRaises(ValueError):
            self.plan()

    def test_cache_overlap_rejected(self):
        with self.assertRaises(ValueError):
            self.plan(cache_dir=self.scratch / "run" / "cache")

    def test_source_overlap_rejected(self):
        with self.assertRaises(ValueError):
            self.plan(run_dir=self.root / "output")

    def test_missing_evidence_before_output_planning(self):
        self.target.unlink()
        with self.assertRaises(ValueError):
            self.plan()
        self.assertFalse((self.scratch / "run").exists())

    def test_empty_and_duplicate_input_ownership_rejected(self):
        for inputs in ([], [LOG, LOG]):
            with self.assertRaises(ValueError):
                self.context.audit_plan(inputs, run_dir=self.scratch / "run",
                                        cache_dir=self.scratch / "cache", temporary_dir=self.scratch / "tmp")


if __name__ == "__main__":
    unittest.main()
