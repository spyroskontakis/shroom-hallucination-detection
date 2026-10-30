"""Phase24 root/identity/guard tests; no Modal import or experiment execution."""
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
spec = importlib.util.spec_from_file_location("_context_v3_tests_api", ROOT / "research/shared_tools/repository_source_context_v3.py")
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)
MODAL_ORIGINAL = "RAG/results/phase3_e9_claim_verification/modal_gpu/modal_phase3_gpu.py"
MODAL_CURRENT = "research/experiments/phase3_advanced_methods/e9_claim_verification/modal_gpu/modal_phase3_gpu.py"
MODAL_AST = "20c6489375bfe38c3f59e2d59712ab9a2dbb61c8e0a55eb9df0c4c3c1f31e8ad"


def here_node():
    return next(n for n in ast.parse((ROOT / MODAL_CURRENT).read_bytes()).body
                if isinstance(n, ast.Assign) and len(n.targets) == 1
                and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "HERE")


def binding(origin):
    ns = {"Path": Path, "__file__": str(origin)}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[here_node()], type_ignores=[])), "isolated_here", "exec"), ns)
    return ns["HERE"]


class Phase24Tests(unittest.TestCase):
    SMOKES = {
        "run_local_smoke.py": "0f9380fad4677817ff6a516767263c6eb69b84433259ca7f0f6d18743b81b848",
        "run_cpu_sun12.py": "7486cf3dedb2a5bee69a08c1bc4965ec6d3a3716f99eca6de129947b1f34dd18",
    }
    SMOKE_OLD = "RAG/results/phase3_e9_claim_verification/factcg_local_smoke"
    SMOKE_NEW = "research/experiments/phase3_advanced_methods/e10_factcg/development/local_smoke"

    def smoke_tree(self, filename):
        return ast.parse((ROOT / self.SMOKE_NEW / filename).read_bytes())

    def smoke_binding(self, filename, origin):
        node = next(n for n in self.smoke_tree(filename).body
                    if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
                    and n.targets[0].id == "HERE")
        ns = {"Path": Path, "__file__": str(origin)}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), "isolated_smoke_here", "exec"), ns)
        return ns["HERE"]

    def test_smokes_only_reviewed_path_bindings_changed(self):
        for filename, expected in self.SMOKES.items():
            tree = self.smoke_tree(filename)
            tree.body = [n for n in tree.body if not (
                isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
                and n.targets[0].id == "RECORDS")]
            for node in tree.body:
                if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "HERE":
                    node.value = ast.Constant("REVIEWED_HERE_BINDING")
            for node in ast.walk(tree):
                if (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)
                        and isinstance(node.left, ast.Name) and node.left.id == "RECORDS"
                        and isinstance(node.right, ast.Constant)
                        and node.right.value in ("SELECTION_MANIFEST.json", "CHECKPOINT_RELEASE_METADATA.json")):
                    node.left.id = "HERE"
            self.assertEqual(hashlib.sha256(ast.dump(tree, include_attributes=False).encode()).hexdigest(), expected)

    def test_smokes_keep_original_inputs_and_run_gates(self):
        for filename in self.SMOKES:
            self.assertEqual(self.smoke_binding(filename, ROOT / self.SMOKE_NEW / filename), ROOT / self.SMOKE_OLD)

    def test_smokes_binding_independent_of_cwd(self):
        previous = Path.cwd()
        try:
            os.chdir(self.work)
            for filename in self.SMOKES:
                self.assertEqual(self.smoke_binding(filename, ROOT / self.SMOKE_NEW / filename), ROOT / self.SMOKE_OLD)
        finally:
            os.chdir(previous)

    def test_smokes_unknown_checkout_fails_before_package_import(self):
        for filename in self.SMOKES:
            with self.assertRaises(StopIteration):
                self.smoke_binding(filename, self.work / "unknown" / filename)

    def test_smokes_current_sources_preserve_function_identities(self):
        c = api.context(ROOT)
        for filename in self.SMOKES:
            original = self.SMOKE_OLD + "/" + filename
            if filename == "run_local_smoke.py":
                self.assertTrue(c.entries[original]["symbols"])
            else:
                # main() has three reviewed path-only substitutions; claiming
                # its complete original function text hash would be incorrect.
                self.assertEqual(c.entries[original]["symbols"], {})
            self.assertEqual(c.check(original, mode="H2_CURRENT")["status"], "PASS")

    def test_smoke_first_writer_preserves_exclusive_gate(self):
        # Execute only the two statements preceding any model/data access, with
        # the actual frozen package writer against an existing scratch marker.
        import time
        code = (ROOT / "RAG/results/phase3_e9_claim_verification/factcg_gpu/factcg_common.py").read_text()
        writer = next(n for n in ast.parse(code).body if isinstance(n, ast.FunctionDef) and n.name == "write")
        ns = {"Path": Path, "json": json, "time": time, "HERE": self.work,
              "MODEL": "synthetic", "REVISION": "synthetic"}
        exec(compile(ast.Module(body=[writer], type_ignores=[]), "isolated_frozen_writer", "exec"), ns)
        marker = self.work / "SMOKE_STARTED.json"
        marker.write_bytes(b"existing historical run")
        main = next(n for n in self.smoke_tree("run_local_smoke.py").body if isinstance(n, ast.FunctionDef) and n.name == "main")
        with self.assertRaises(FileExistsError):
            exec(compile(ast.Module(body=main.body[:2], type_ignores=[]), "isolated_smoke_gate", "exec"), ns)
        self.assertEqual(marker.read_bytes(), b"existing historical run")

    def test_cpu_first_statement_preserves_existing_directory_gate(self):
        main = next(n for n in self.smoke_tree("run_cpu_sun12.py").body if isinstance(n, ast.FunctionDef) and n.name == "main")
        with self.assertRaises(FileExistsError):
            exec(compile(ast.Module(body=main.body[:1], type_ignores=[]), "isolated_cpu_gate", "exec"), {"OUT": self.work})

    def test_smokes_safe_runtime_imports_without_main(self):
        # Imports only the unchanged stdlib FactCG helper/backend; no ML import,
        # main(), model loading, cache preparation or download is invoked.
        import sys
        previous = sys.path[:]
        try:
            for filename in self.SMOKES:
                path = ROOT / self.SMOKE_NEW / filename
                spec = importlib.util.spec_from_file_location("_phase24_import_" + path.stem, path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.assertEqual(module.HERE, ROOT / self.SMOKE_OLD)
                self.assertEqual(module.GPU, (ROOT / self.SMOKE_OLD).parent / "factcg_gpu")
                self.assertTrue(callable(module.main))
        finally:
            sys.path[:] = previous

    def test_smoke_read_only_records_match_historical_bytes(self):
        c = api.context(ROOT)
        for filename in ("SELECTION_MANIFEST.json", "CHECKPOINT_RELEASE_METADATA.json"):
            original = self.SMOKE_OLD + "/" + filename
            item = c.entries[original]
            self.assertEqual(item["h1"]["sha256"], item["current"]["sha256"])
            self.assertEqual(c.check(original, mode="H2_CURRENT")["status"], "PASS")
            self.assertFalse((ROOT / original).exists())

    def test_cpu_read_paths_use_relocated_records_and_cache_stays_original(self):
        import sys
        previous = sys.path[:]
        try:
            path = ROOT / self.SMOKE_NEW / "run_cpu_sun12.py"
            spec = importlib.util.spec_from_file_location("_phase24_cpu_paths", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.assertEqual(module.RECORDS, path.parent)
            self.assertEqual(module.OUT, ROOT / self.SMOKE_OLD / "cpu_sun12")
            for filename in ("SELECTION_MANIFEST.json", "CHECKPOINT_RELEASE_METADATA.json"):
                self.assertTrue((module.RECORDS / filename).is_file())
            main = next(n for n in self.smoke_tree(path.name).body if isinstance(n, ast.FunctionDef) and n.name == "main")
            read_paths = [n for n in ast.walk(main) if isinstance(n, ast.BinOp)
                          and isinstance(n.op, ast.Div) and isinstance(n.left, ast.Name)
                          and n.left.id == "RECORDS"]
            self.assertEqual(len(read_paths), 3)
            cache = next(n for n in ast.walk(main) if isinstance(n, ast.Assign)
                         and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "cache")
            self.assertEqual(ast.unparse(cache.value), "HERE / 'model_cache'")
        finally:
            sys.path[:] = previous

    def test_v3_checks_every_reviewed_current_artifact(self):
        c = api.context(ROOT)
        reviewed = [name for name, item in c.entries.items()
                    if item["current"]["status"] == "REVIEWED"]
        self.assertEqual(len(reviewed), 222)
        for name in reviewed:
            self.assertEqual(c.check(name, mode="H2_CURRENT")["status"], "PASS", name)

    def test_older_guide_pin_remains_a_distinct_snapshot(self):
        name = "RAG/E6_V3_REPRODUCIBILITY.md"
        original = json.loads((ROOT / "project_records/current_layout/repository_sources_v2.json").read_text())
        prior = next(x for x in original["artifacts"] if x["historical_path"] == name)
        self.assertEqual(prior["current"]["sha256"], "9115298e60711bfcb5392f51d226e363c8cf1ac3b3f931f5ab3a3f50d306f269")
        current = api.context(ROOT)
        self.assertNotEqual(prior["current"]["sha256"], current.entries[name]["current"]["sha256"])
        self.assertEqual(prior["h1"], current.entries[name]["h1"])
        self.assertEqual(current.check(name, mode="H2_CURRENT")["status"], "PASS")

    def setUp(self):
        self.work = Path(os.environ["SHROOM_TEST_SCRATCH"]) / ("v3_" + uuid.uuid4().hex)
        self.work.mkdir()

    def test_modal_only_here_changes(self):
        tree = ast.parse((ROOT / MODAL_CURRENT).read_bytes())
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "HERE":
                node.value = ast.Constant("REVIEWED_HERE_BINDING")
        self.assertEqual(hashlib.sha256(ast.dump(tree, include_attributes=False).encode()).hexdigest(), MODAL_AST)

    def test_relocated_modal_resolves_original_assets(self):
        self.assertEqual(binding(ROOT / MODAL_CURRENT), ROOT / "RAG/results/phase3_e9_claim_verification/modal_gpu")

    def test_modal_binding_independent_of_working_directory(self):
        previous = Path.cwd()
        try:
            os.chdir(self.work)
            self.assertEqual(binding(ROOT / MODAL_CURRENT), ROOT / "RAG/results/phase3_e9_claim_verification/modal_gpu")
        finally:
            os.chdir(previous)

    def test_noncheckout_cloud_fallback_unchanged(self):
        origin = self.work / "standalone" / "modal_phase3_gpu.py"
        self.assertEqual(binding(origin), origin.parent)

    def test_current_modal_identity_and_symbols(self):
        c = api.context(ROOT)
        item = c.entries[MODAL_ORIGINAL]
        self.assertNotEqual(item["h1"]["sha256"], item["current"]["sha256"])
        self.assertTrue(item["symbols"])
        self.assertEqual(c.check(MODAL_ORIGINAL, mode="H2_CURRENT")["status"], "PASS")

    def test_terminal_records_exact_historical_bytes(self):
        c = api.context(ROOT)
        for path in ("RAG/results/rag_e6_v3/E6_V3_RESULTS.md", "RAG/results/rag_e6_v3/config/completion_manifest.json", "RAG/results/rag_e8_rf_tuning_v1/.gitattributes"):
            item = c.entries[path]
            self.assertEqual(item["h1"]["sha256"], item["current"]["sha256"])
            self.assertEqual(c.check(path, mode="H2_CURRENT")["status"], "PASS")

    def test_existing_version_and_independent_pin_required(self):
        for kwargs in ({"version": "shroom-repository-source-context-v2"}, {"catalog_sha256": "0" * 64}):
            with self.assertRaises(ValueError):
                api.context(ROOT, **kwargs)

    def test_changed_delegate_rejected_before_import(self):
        root = self.work / "source"
        path = root / api.BASE_ADAPTER
        path.parent.mkdir(parents=True)
        path.write_bytes(b"raise RuntimeError('must not import')")
        with self.assertRaises(ValueError):
            api.context(root)

    def test_missing_catalog_does_not_adopt_previous_version(self):
        root = self.work / "source"
        for name in (api.BASE_ADAPTER, "research/shared_tools/repository_source_context_v1.py", "research/shared_tools/canonical_execution_context.py"):
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        with self.assertRaises((ValueError, OSError)):
            api.context(root)

    def test_original_final_integrity_writer_still_exclusive(self):
        source = ROOT / "RAG/results/rag_e6_v3/scripts/v3_common.py"
        fn = next(n for n in ast.parse(source.read_bytes()).body if isinstance(n, ast.FunctionDef) and n.name == "write_json")
        marker = self.work / "final_integrity.json"
        marker.write_bytes(b'{"SYNTHETIC":true}\n')
        ns = {"Path": Path, "OUT": self.work, "json": json}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])), "original_write_json", "exec"), ns)
        with self.assertRaises(FileExistsError):
            ns["write_json"](marker, {"must_not_replace": True})
        self.assertEqual(marker.read_bytes(), b'{"SYNTHETIC":true}\n')
        self.assertTrue((ROOT / "RAG/results/rag_e6_v3/config/final_integrity.json").is_file())

    def test_report_guard_precedes_transported_outputs(self):
        source = ROOT / "RAG/results/rag_e6_v3/scripts/report_v3.py"
        tree = ast.parse(source.read_bytes())
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
        guarded = [n for n in main.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and ast.unparse(n.value.func) == "c.write_json"]
        first = next(n for n in guarded if "final_integrity.json" in ast.unparse(n))
        last = next(n for n in guarded if "completion_manifest.json" in ast.unparse(n))
        result = next(n for n in main.body if isinstance(n, ast.With) and "E6_V3_RESULTS.md" in ast.unparse(n))
        self.assertLess(first.lineno, result.lineno)
        self.assertLess(first.lineno, last.lineno)


if __name__ == "__main__":
    unittest.main()
