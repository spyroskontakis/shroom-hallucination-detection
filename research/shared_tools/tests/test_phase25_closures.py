"""Offline path/URL closure tests; never execute notebooks or fit a model."""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch
import uuid

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / "research/shared_tools/canonical_execution_context.py").is_file())
CV = ROOT / "research/data_and_evaluation/canonical/scripts/canonical_development_cv.py"


def cv_namespace(origin=CV):
    """Compile the actual IO bindings/guard, excluding scientific imports/body."""
    tree = ast.parse(CV.read_bytes())
    names = {"REPOSITORY_ROOT", "ROOT", "FEATURE_DIR", "OUTPUT_DIR", "LOG_PATH",
             "HUMAN_FEATURES", "SYNTHETIC_FEATURES", "FOLD_ASSIGNMENTS",
             "HUMAN_MANIFEST", "OLD_TRIAL_FEATURES", "FEATURE_METADATA",
             "UNMATCHED_COMPATIBILITY_ROWS"}
    nodes = [n for n in tree.body if (
        isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
        and n.targets[0].id in names) or (
        isinstance(n, ast.FunctionDef) and n.name in ("_prepare_output_directory", "main"))]
    ns = {"Path": Path, "os": os, "hashlib": hashlib, "sys": sys,
          "importlib": __import__("importlib"), "__file__": str(origin)}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(CV), "exec"), ns)
    return ns


def science_projection(raw):
    tree = ast.parse(raw)
    tree.body = [n for n in tree.body if not (
        isinstance(n, ast.Import) and any(a.name == "importlib.util" for a in n.names))
        and not (isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
                 and n.targets[0].id == "REPOSITORY_ROOT")
        and not (isinstance(n, ast.FunctionDef) and n.name == "_prepare_output_directory")
        and not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
                 and isinstance(n.value.func, ast.Attribute)
                 and isinstance(n.value.func.value, ast.Name)
                 and n.value.func.value.id == "OUTPUT_DIR" and n.value.func.attr == "mkdir")]
    for node in tree.body:
        if (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id in ("ROOT", "OUTPUT_DIR", "LOG_PATH", "UNMATCHED_COMPATIBILITY_ROWS")):
            node.value = ast.Constant("REVIEWED_IO_BINDING")
        if isinstance(node, ast.FunctionDef) and node.name == "main":
            node.body = [n for n in node.body if not (
                isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
                and isinstance(n.value.func, ast.Name)
                and n.value.func.id == "_prepare_output_directory")]
    return hashlib.sha256(ast.dump(tree, include_attributes=False).encode()).hexdigest()


class CanonicalCVPathTests(unittest.TestCase):
    def setUp(self):
        self.work = Path(os.environ["SHROOM_TEST_SCRATCH"]) / ("cv_paths_" + uuid.uuid4().hex)
        self.work.mkdir()
        self.inputs = self.work / "inputs"
        self.temporary = self.work / "temporary"
        self.run = self.work / "run"
        self.inputs.mkdir()
        self.temporary.mkdir()
        self.environment = patch.dict(os.environ, {
            "CANONICAL_CV_INPUT_ROOT": str(self.inputs),
            "CANONICAL_CV_OUTPUT_DIR": str(self.run),
            "CANONICAL_CV_TEMP_DIR": str(self.temporary),
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        import tempfile
        original_temp = tempfile.tempdir
        self.addCleanup(setattr, tempfile, "tempdir", original_temp)
        self.ns = cv_namespace()

    def fixtures(self):
        # Existence/ownership fixtures only, not counterfeit canonical data.
        for name in ("HUMAN_FEATURES", "SYNTHETIC_FEATURES", "FOLD_ASSIGNMENTS",
                     "HUMAN_MANIFEST", "OLD_TRIAL_FEATURES", "FEATURE_METADATA"):
            path = self.ns[name]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"synthetic path-only test fixture\n")

    def prepare(self):
        self.ns["_prepare_output_directory"]()

    def test_original_scientific_ast_is_preserved(self):
        self.assertEqual(science_projection(CV.read_bytes()), "56b01b019f46d467a0f24959d8a64e9889f560a116ce326ecf8e2a48f2cefb9c")

    def test_import_bindings_cannot_open_output_writers(self):
        self.assertIsNone(self.ns["OUTPUT_DIR"])
        self.assertIsNone(self.ns["LOG_PATH"])
        self.assertIsNone(self.ns["UNMATCHED_COMPATIBILITY_ROWS"])
        self.assertFalse(self.run.exists())

    def test_main_guard_precedes_every_original_operation(self):
        main = next(n for n in ast.parse(CV.read_bytes()).body
                    if isinstance(n, ast.FunctionDef) and n.name == "main")
        self.assertEqual(ast.unparse(main.body[0]), "_prepare_output_directory()")

    def test_missing_output_approval_fails_before_main_body(self):
        del os.environ["CANONICAL_CV_OUTPUT_DIR"]
        with self.assertRaises(ValueError):
            self.ns["main"]()
        self.assertFalse(self.run.exists())

    def test_missing_temporary_root_fails_without_writes(self):
        del os.environ["CANONICAL_CV_TEMP_DIR"]
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.run.exists())

    def test_missing_inputs_fail_before_run_creation(self):
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.run.exists())
        self.assertEqual(list(self.temporary.iterdir()), [])

    def test_existing_run_is_never_reused_or_overwritten(self):
        self.fixtures()
        self.run.mkdir()
        marker = self.run / "old_result.csv"
        marker.write_bytes(b"protected result")
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertEqual(marker.read_bytes(), b"protected result")

    def test_repository_output_is_rejected(self):
        self.fixtures()
        os.environ["CANONICAL_CV_OUTPUT_DIR"] = str(ROOT / "__forbidden_cv_output")
        with self.assertRaises(ValueError):
            self.prepare()

    def test_another_git_checkout_is_rejected(self):
        self.fixtures()
        other = self.work / "other_checkout"
        other.mkdir()
        (other / ".git").write_text("synthetic Git marker", encoding="utf-8")
        os.environ["CANONICAL_CV_OUTPUT_DIR"] = str(other / "run")
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse((other / "run").exists())

    def test_temporary_input_overlap_is_rejected(self):
        self.fixtures()
        os.environ["CANONICAL_CV_TEMP_DIR"] = str(self.inputs)
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.run.exists())

    def test_temporary_directory_inside_git_is_rejected(self):
        self.fixtures()
        (self.temporary / ".git").write_text("synthetic Git marker", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.prepare()

    def test_relative_source_input_root_is_rejected(self):
        os.environ["CANONICAL_CV_INPUT_ROOT"] = "."
        self.ns = cv_namespace()
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.run.exists())

    def test_input_directory_cannot_be_an_output(self):
        self.fixtures()
        os.environ["CANONICAL_CV_OUTPUT_DIR"] = str(self.inputs)
        with self.assertRaises(ValueError):
            self.prepare()

    def test_success_uses_explicit_isolated_output_and_temp(self):
        self.fixtures()
        before = {p: p.read_bytes() for p in self.inputs.rglob("*") if p.is_file()}
        self.prepare()
        self.assertEqual(self.ns["OUTPUT_DIR"], self.run)
        self.assertEqual(self.ns["LOG_PATH"], self.run / "canonical_cv_execution.log")
        self.assertEqual(self.ns["UNMATCHED_COMPATIBILITY_ROWS"], self.run / "canonical_feature_compatibility_unmatched_rows.csv")
        self.assertEqual(list(self.run.iterdir()), [])
        for key in ("TEMP", "TMP", "TMPDIR", "JOBLIB_TEMP_FOLDER", "NUMBA_CACHE_DIR"):
            self.assertEqual(os.environ[key], str(self.temporary))
        for path, raw in before.items():
            self.assertEqual(path.read_bytes(), raw)

    def test_modified_shared_validator_is_rejected_before_import(self):
        helper = ROOT / "research/shared_tools/canonical_execution_context.py"
        original = Path.read_bytes
        with patch.object(Path, "read_bytes", lambda p: b"raise AssertionError('must not execute')" if p == helper else original(p)):
            with self.assertRaises(ValueError):
                self.prepare()
        self.assertFalse(self.run.exists())

    def test_working_directory_does_not_change_declared_paths(self):
        previous = Path.cwd()
        try:
            os.chdir(self.work)
            other = cv_namespace()
            for name in ("ROOT", "HUMAN_FEATURES", "FOLD_ASSIGNMENTS", "OLD_TRIAL_FEATURES"):
                self.assertEqual(other[name], self.ns[name])
        finally:
            os.chdir(previous)

    def test_old_and_new_source_locations_resolve_same_repository(self):
        old = cv_namespace(ROOT / "codex/canonical_development_cv.py")
        self.assertEqual(old["REPOSITORY_ROOT"], self.ns["REPOSITORY_ROOT"])
        self.assertEqual(old["ROOT"], self.ns["ROOT"])


class HistoricalDocumentationTests(unittest.TestCase):
    PATTERN = r"(?<!!)\[[^\]\n]*\]\(\s*(?:<([^>\n]+)>|([^\s\)]+))(?:\s+[\x22\x27][^\n]*?[\x22\x27])?\s*\)"

    def projection(self, path):
        text = path.read_bytes().decode("utf-8")
        text = re.sub(self.PATTERN, lambda match: match.group().replace(match.group(1) or match.group(2), "__REVIEWED_URL_DESTINATION__", 1), text)
        return hashlib.sha256(text.encode()).hexdigest()

    def test_execution_matrix_changes_only_url_destinations(self):
        path = ROOT / "project_records/migrations/execution_safety_20261027/EXECUTION_MATRIX.md"
        self.assertEqual(self.projection(path), "32d3f2ab84a8bc4d091dd2e5460fb1ef9fc30566fbfb2227516cb0eefe3f8870")

    def test_output_risk_document_changes_only_url_destinations(self):
        path = ROOT / "project_records/migrations/execution_safety_20261027/OUTPUT_PATH_RISKS.md"
        self.assertEqual(self.projection(path), "e4093dbb9f0c122f3189586b1db186d642640990becf8bfc5ec11af8e7562163")

    def test_hash_locked_e11_document_remains_unchanged(self):
        spec = importlib.util.spec_from_file_location(
            "_closure_current_source_binding", ROOT / "research/shared_tools/repository_compatibility.py")
        api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api)
        raw = api.Catalog(ROOT).current(
            "RAG/results/phase3_e11_task_adaptation/E11_DATA_AUDIT.md").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), "2767b8f0e286deafd6ca6f5467ac393c9bf3ec55c8400c75b2da10643b2c544c")


if __name__ == "__main__":
    unittest.main()
