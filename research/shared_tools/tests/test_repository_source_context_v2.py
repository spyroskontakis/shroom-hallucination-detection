"""Offline successor/lineage tests; no experiment module is imported."""
import ast
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
spec = importlib.util.spec_from_file_location("_source_context_v2_test_api", ROOT / "research/shared_tools/repository_source_context_v2.py")
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)
ORIGINAL = "RAG/results/phase3_e11_task_adaptation/E11_FINAL_SUMMARY.md"


class SuccessorTests(unittest.TestCase):
    def setUp(self):
        self.work = Path(os.environ["SHROOM_TEST_SCRATCH"]) / ("successor_" + uuid.uuid4().hex)
        self.work.mkdir()
        self.root = self.work / "source"
        self.root.mkdir()
        for name in (api.CATALOG, api.BASE_ADAPTER, "research/shared_tools/canonical_execution_context.py"):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        self.context = api.context(self.root)
        self.entry = self.context.entries[ORIGINAL]
        self.target = self.root / self.entry["target_path"]
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes((ROOT / self.entry["target_path"]).read_bytes())

    def test_successor_is_independent_version(self):
        self.assertEqual(api.VERSION, "shroom-repository-source-context-v2")
        self.assertEqual(self.context.check(ORIGINAL, mode="H2_CURRENT")["status"], "PASS")

    def test_v1_bytes_unchanged(self):
        self.assertEqual(hashlib.sha256((ROOT / api.BASE_ADAPTER).read_bytes()).hexdigest(), api.BASE_ADAPTER_SHA256)

    def test_wrong_version(self):
        with self.assertRaises(ValueError):
            api.context(self.root, version="shroom-repository-source-context-v1")

    def test_wrong_pin(self):
        with self.assertRaises(ValueError):
            api.context(self.root, catalog_sha256="0" * 64)

    def test_changed_base_source_rejected_before_import(self):
        (self.root / api.BASE_ADAPTER).write_bytes(b"raise RuntimeError('must not execute')")
        with self.assertRaises(ValueError):
            api.context(self.root)

    def test_changed_catalog_rejected(self):
        (self.root / api.CATALOG).write_bytes(b"{}")
        with self.assertRaises(ValueError):
            api.context(self.root)

    def test_missing_current_not_replaced_by_original(self):
        self.target.unlink()
        self.assertEqual(self.context.check(ORIGINAL, mode="H2_CURRENT")["status"], "MISSING")

    def test_changed_current_rejected(self):
        self.target.write_bytes(b"changed")
        self.assertEqual(self.context.check(ORIGINAL, mode="H2_CURRENT")["status"], "FAIL")

    def test_no_scientific_execution_from_plan(self):
        result = self.context.audit_plan([ORIGINAL], run_dir=self.work / "run", cache_dir=self.work / "cache", temporary_dir=self.work / "tmp")
        self.assertFalse(result["execution_permitted"])
        self.assertEqual(result["version"], api.VERSION)
        self.assertFalse((self.work / "run").exists())

    def test_original_finalizer_gate_still_blocks(self):
        source = ROOT / "RAG/results/phase3_e11_task_adaptation/e11_finalization/finalize.py"
        tree = ast.parse(source.read_bytes())
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
        require = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "require")
        guard = ast.FunctionDef(name="guard", args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]), body=main.body[:2], decorator_list=[])
        ns = {"E11": ROOT / "RAG/results/phase3_e11_task_adaptation"}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[require, guard], type_ignores=[])), "exact_original_entry_guard", "exec"), ns)
        with self.assertRaisesRegex(ValueError, "final artifacts already exist"):
            ns["guard"]()

    def test_historical_checksum_list_still_present(self):
        path = ROOT / "RAG/results/phase3_e11_task_adaptation/E11_FINAL_SHA256SUMS.txt"
        self.assertTrue(path.is_file())
        self.assertEqual(len([line for line in path.read_text().splitlines() if line.strip()]), 4)

    def test_synthetic_final_metrics_not_recomputed(self):
        # Verify stored identity only; do not turn this into new metric evaluation.
        entry = self.context.entries["RAG/results/phase3_e11_task_adaptation/E11_FINAL_TABLE.csv"]
        self.assertEqual(entry["h1"]["sha256"], entry["current"]["sha256"])
        self.assertEqual(self.context.catalog["runtime_status"], "NOT VERIFIED")

    def test_e9_variant_guard_rejects_duplicate_before_fits(self):
        source = ROOT / "RAG/results/phase3_e9_claim_verification/scripts/e9_common.py"
        tree = ast.parse(source.read_bytes())
        writer = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "write_json")
        out = self.work / "e9_fixture"
        (out / "evaluation").mkdir(parents=True)
        marker = out / "evaluation/E9-B_started.json"
        marker.write_bytes(b'{"synthetic_guard":true}\n')
        ns = {"OUT": out, "Path": Path, "json": json}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[writer], type_ignores=[])), "original_exclusive_writer", "exec"), ns)
        with self.assertRaises(FileExistsError):
            ns["write_json"](marker, {"must_not_replace": True})
        self.assertEqual(marker.read_bytes(), b'{"synthetic_guard":true}\n')
        self.assertTrue((ROOT / "RAG/results/phase3_e9_claim_verification/evaluation/E9-B_started.json").is_file())

    def test_e10_original_directory_gate_rejects_duplicate(self):
        source = ROOT / "RAG/results/phase3_e9_claim_verification/factcg_gpu/evaluate_e10.py"
        tree = ast.parse(source.read_bytes())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "evaluate")
        assign = next(n for n in fn.body if isinstance(n, ast.Assign) and any(isinstance(z, ast.Name) and z.id == "out" for z in n.targets))
        mkdir = next(n for n in fn.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and ast.unparse(n.value.func) == "out.mkdir")
        fixture = self.work / "e10_fixture"
        (fixture / "factcg_gpu").mkdir(parents=True)
        (fixture / "evaluation/E10").mkdir(parents=True)
        with self.assertRaises(FileExistsError):
            exec(compile(ast.fix_missing_locations(ast.Module(body=[assign, mkdir], type_ignores=[])), "original_e10_directory_gate", "exec"), {"HERE": fixture / "factcg_gpu"})
        self.assertTrue((ROOT / "RAG/results/phase3_e9_claim_verification/evaluation/E10/E10_started.json").is_file())
        self.assertTrue((ROOT / "RAG/results/phase3_e9_claim_verification/evaluation/E10/E10_metrics.json").is_file())

    def test_fold_logs_have_exact_original_byte_identity(self):
        prefix = "RAG/results/phase3_e9_claim_verification/"
        originals = [prefix + f"evaluation/E10/fit_{f}_{state}.json" for f in range(1, 6) for state in ("started", "completed")]
        originals += [prefix + f"evaluation/fit_E9-B_{f}_started.json" for f in range(1, 6)]
        current = api.context(ROOT)
        for original in originals:
            item = current.entries[original]
            self.assertEqual(item["h1"]["sha256"], item["current"]["sha256"])
            self.assertEqual(current.check(original, mode="H2_CURRENT")["status"], "PASS")
            self.assertFalse((ROOT / original).exists())


if __name__ == "__main__":
    unittest.main()
