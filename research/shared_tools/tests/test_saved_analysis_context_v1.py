"""Synthetic evidence/IO fixtures; never run the 561-row diagnostic analysis."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import unittest
import uuid

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / "research/shared_tools/canonical_execution_context.py").is_file())
API = ROOT / "research/shared_tools/saved_analysis_context_v1.py"
spec = importlib.util.spec_from_file_location("_saved_analysis_under_test", API)
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
CATALOG = "project_records/current_layout/e6_v3_saved_analysis_h2_v1.json"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class SavedContextTests(unittest.TestCase):
    def setUp(self):
        # Each fixture is an independent source root. Preserve the engine's
        # production rejection of modules cached from a different root.
        sys.modules.pop("_e6_v4_shared_h2_validator", None)
        self.addCleanup(sys.modules.pop, "_e6_v4_shared_h2_validator", None)
        self.work = Path(os.environ["SHROOM_TEST_SCRATCH"]) / ("analysis_" + uuid.uuid4().hex)
        self.work.mkdir()
        self.root = self.work / "source"
        self.root.mkdir()
        self.data = json.loads((ROOT / CATALOG).read_bytes())
        self.original = self.work / "original"
        self.original.mkdir()
        self.input = self.original / "synthetic.json"
        self.input.write_bytes(b'{"synthetic":true}\n')
        # The production contract is untouched. An explicit independently pinned
        # scratch contract supplies synthetic evidence, never fake frozen inputs.
        self.data["required_inputs"] = [{"path": "synthetic.json", "sha256": sha(self.input.read_bytes()),
                                         "evidence_owner": "UNIT_TEST_ONLY"}]
        paths = [a.ENGINE, "research/shared_tools/canonical_execution_context.py",
                 "research/shared_tools/repository_source_context_v1.py"]
        paths += [x["current_path"] for x in self.data["artifacts"]]
        for name in paths:
            dst = self.root / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, dst)
        self.contract = self.root / CATALOG
        self.contract.parent.mkdir(parents=True)
        self.write_contract()

    def write_contract(self):
        self.contract.write_text(json.dumps(self.data), encoding="utf-8")
        self.pin = sha(self.contract.read_bytes())

    def context(self, **overrides):
        kwargs = dict(expected_sha256=self.pin, original_root=self.original,
                      run_dir=self.work / "run", cache_dir=self.work / "cache", temporary_dir=self.work / "tmp")
        kwargs.update(overrides)
        return a.AnalysisContext(self.root, self.contract, **kwargs)

    def test_01_authentic_synthetic_context_has_no_writes(self):
        before = sorted(str(p) for p in self.work.rglob("*"))
        c = self.context()
        self.assertFalse(c.ready)
        self.assertEqual(before, sorted(str(p) for p in self.work.rglob("*")))

    def test_02_wrong_contract_pin(self):
        with self.assertRaises(ValueError):
            self.context(expected_sha256="0" * 64)

    def test_03_contract_version(self):
        self.data["version"] = "unknown"
        self.write_contract()
        with self.assertRaises(ValueError):
            self.context()

    def test_04_baseline_tree(self):
        self.data["baseline"]["tree"] = "0" * 40
        self.write_contract()
        with self.assertRaises(ValueError):
            self.context()

    def test_05_missing_original_before_outputs(self):
        self.input.unlink()
        with self.assertRaises(ValueError):
            self.context()
        self.assertFalse((self.work / "run").exists())
        self.assertFalse((self.work / "cache").exists())

    def test_06_changed_original(self):
        self.input.write_bytes(b"changed")
        with self.assertRaises(ValueError):
            self.context()

    def test_07_conflicting_historical_claims(self):
        self.data["required_inputs"].append({"path": "synthetic.json", "sha256": "0" * 64, "evidence_owner": "DIFFERENT_STAGE"})
        self.write_contract()
        with self.assertRaises(ValueError):
            self.context()

    def test_08_unknown_schema_field(self):
        self.data["allow_missing"] = True
        self.write_contract()
        with self.assertRaises(ValueError):
            self.context()

    def test_09_duplicate_source(self):
        self.data["artifacts"].append(self.data["artifacts"][0])
        self.write_contract()
        with self.assertRaises(ValueError):
            self.context()

    def test_10_missing_current_source(self):
        (self.root / self.data["artifacts"][0]["current_path"]).unlink()
        with self.assertRaises(ValueError):
            self.context()

    def test_11_changed_current_source(self):
        (self.root / self.data["artifacts"][0]["current_path"]).write_bytes(b"changed")
        with self.assertRaises(ValueError):
            self.context()

    def test_12_input_traversal(self):
        self.data["required_inputs"][0]["path"] = "../escape"
        self.write_contract()
        with self.assertRaises(ValueError):
            self.context()

    def test_13_source_and_original_overlap(self):
        with self.assertRaises(ValueError):
            self.context(original_root=self.root)

    def test_14_run_and_cache_overlap(self):
        with self.assertRaises(ValueError):
            self.context(cache_dir=self.work / "run" / "cache")

    def test_15_existing_run(self):
        run = self.work / "run"
        run.mkdir()
        with self.assertRaises(ValueError):
            self.context()

    def test_16_run_in_git(self):
        (self.work / ".git").mkdir()
        with self.assertRaises(ValueError):
            self.context()

    def test_17_unprepared_module(self):
        c = self.context()
        with self.assertRaises(ValueError):
            c.load(a.LEGACY + "build_report.py")

    def test_18_direct_source_gate_precedes_side_effects(self):
        for item in self.data["artifacts"]:
            if item["original_path"].endswith(".py"):
                raw = (self.root / item["current_path"]).read_bytes()
                with self.assertRaises(RuntimeError):
                    exec(compile(raw, "synthetic_direct_entry", "exec"), {"__name__": "__main__"})
        self.assertFalse((self.work / "run").exists())

    def test_19_output_appears_after_validation(self):
        c = self.context()
        c.run.mkdir()
        with self.assertRaises(ValueError):
            c.prepare()
        self.assertFalse(c.cache.exists())

    def test_20_original_changes_after_validation(self):
        c = self.context()
        self.input.write_bytes(b"changed")
        with self.assertRaises(ValueError):
            c.prepare()
        self.assertFalse(c.run.exists())

    def test_21_undeclared_original(self):
        with self.assertRaises(ValueError):
            self.context().original_path("not-declared.json")

    def test_22_engine_identity(self):
        (self.root / a.ENGINE).write_bytes(b"raise RuntimeError('never import')")
        with self.assertRaises(ValueError):
            self.context()

    def test_23_adapter_identity(self):
        self.data["adapter"]["sha256"] = "0" * 64
        self.write_contract()
        with self.assertRaises(ValueError):
            self.context()

    def test_24_no_empty_original_contract(self):
        self.data["required_inputs"] = []
        self.write_contract()
        with self.assertRaises(ValueError):
            self.context()

    def test_25_current_source_changes_after_validation(self):
        c = self.context()
        (self.root / self.data["artifacts"][0]["current_path"]).write_bytes(b"changed")
        with self.assertRaises(ValueError):
            c.prepare()
        self.assertFalse(c.run.exists())

    def test_26_mutated_cached_validator_is_not_used(self):
        import types
        fake = types.ModuleType("_e6_v4_shared_h2_validator")
        fake.__file__ = str(self.root / "research/shared_tools/canonical_execution_context.py")
        fake.strict_json = lambda text: {"unsafe": True}
        sys.modules[fake.__name__] = fake
        c = self.context()
        self.assertEqual(len(c.artifacts), 9)
        self.assertIsNot(c.h, fake)

    def test_zzz_prepared_real_source_pure_function_and_guard(self):
        # Last in this isolated process: the installed audit hook is irreversible.
        c = self.context()
        c.prepare()
        module = c.load(a.LEGACY + "build_report.py")
        self.assertEqual(module.esc("a|b\nc"), "a\\|b c")
        self.assertEqual(module.OUT, c.run)
        out = c.io_path(c.run / "synthetic.txt", "x")
        out.write_text("synthetic", encoding="utf-8")
        self.assertEqual(c.io_path(out).read_text(), "synthetic")
        self.assertEqual(self.input.read_bytes(), b'{"synthetic":true}\n')
        with self.assertRaises(ValueError):
            c.io_path(self.input, "w")
        with self.assertRaises(PermissionError):
            c._guard("socket.connect", ())
        with self.assertRaises(PermissionError):
            c._guard("subprocess.Popen", ())
        with self.assertRaises(PermissionError):
            c._guard("import", ("torch",))
        self.assertNotIn("torch", sys.modules)


if __name__ == "__main__":
    unittest.main()
