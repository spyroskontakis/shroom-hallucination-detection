"""Synthetic source/cache attacks; no scientific notebook cells are executed.

Run through verify_repository.py --tests, which provides external scratch and
a real reparse fixture. All adversarial source and bytecode stay in scratch.
"""
import ast
from contextlib import redirect_stdout
import hashlib
import importlib._bootstrap_external
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
import uuid


ROOT = Path(__file__).resolve().parents[3]
VERIFIER = ROOT / "research/shared_tools/verify_repository.py"
V = types.ModuleType("authenticated_execution_verifier_tests")
V.__file__ = str(VERIFIER)
exec(compile(VERIFIER.read_bytes(), str(VERIFIER), "exec"), V.__dict__)
NOTEBOOKS = ROOT / "research/experiments/phase2_rag_features/e5_rag/modules/module2/notebooks"
AUTHENTIC = b'''EXECUTED = "AUTHENTICATED_SOURCE"
def selected():
    return EXECUTED
class Catalog:
    def __init__(self, root):
        self.root = root
'''
SUBSTITUTE = AUTHENTIC.replace(b"AUTHENTICATED_SOURCE", b"CACHED_FALSE_PASS")
ABSENT = object()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def bootstrap(path):
    nb = json.loads(path.read_bytes())
    cell = next("".join(c["source"]) for c in nb["cells"]
                if "_module2_raw =" in "".join(c.get("source", [])))
    # Exact production setup boundary; never execute CTX or scientific code.
    start = cell.index("import importlib.util as _module2_import")
    end = cell.index("CTX = _module2.context_from_environment", start)
    return compile(cell[start:end], str(path), "exec")


class Fixture(unittest.TestCase):
    def setUp(self):
        self.work = Path(os.environ["SHROOM_TEST_SCRATCH"])
        self.fixture = self.work / ("authenticated_" + uuid.uuid4().hex)
        self.path = self.fixture / "scripts/module2_dense_cache.py"
        self.path.parent.mkdir(parents=True)
        self.path.write_bytes(AUTHENTIC)
        self.old = sys.modules.pop(self.name, ABSENT)

    def tearDown(self):
        sys.modules.pop(self.name, None)
        if self.old is not ABSENT:
            sys.modules[self.name] = self.old

    def cache(self, raw, *, corrupt=False):
        path = Path(importlib.util.cache_from_source(str(self.path)))
        path.parent.mkdir(parents=True, exist_ok=True)
        stat = self.path.stat()
        code = compile(raw, str(self.path), "exec")
        data = importlib._bootstrap_external._code_to_timestamp_pyc(
            code, int(stat.st_mtime), stat.st_size)
        path.write_bytes(b"invalid cache" if corrupt else data)
        return path


class SourceCases:
    def test_valid_source_without_cache(self):
        self.assertEqual(self.load().selected(), "AUTHENTICATED_SOURCE")

    def test_matching_cache(self):
        self.cache(AUTHENTIC)
        self.assertEqual(self.load().selected(), "AUTHENTICATED_SOURCE")

    def test_different_timestamp_valid_cache(self):
        self.cache(SUBSTITUTE)
        self.assertEqual(self.load().selected(), "AUTHENTICATED_SOURCE")

    def test_cached_false_pass_cannot_hide_source_failure(self):
        raw = b'raise RuntimeError("AUTHENTIC_SOURCE_FAILURE")\n'
        self.path.write_bytes(raw)
        self.cache(SUBSTITUTE)
        with self.assertRaisesRegex(RuntimeError, "AUTHENTIC_SOURCE_FAILURE"):
            self.load(digest(raw))
        self.assertNotIn(self.name, sys.modules)

    def test_wrong_digest_fails_before_execution(self):
        with self.assertRaises(ValueError):
            self.load("0" * 64)
        self.assertNotIn(self.name, sys.modules)

    def test_source_changed_after_prior_authentication(self):
        first = self.load()
        self.path.write_bytes(SUBSTITUTE)
        with self.assertRaises(ValueError):
            self.load(digest(AUTHENTIC))
        self.assertIs(sys.modules[self.name], first)
        self.assertEqual(first.selected(), "AUTHENTICATED_SOURCE")

    def test_corrupt_cache_ignored(self):
        self.cache(AUTHENTIC, corrupt=True)
        self.assertEqual(self.load().selected(), "AUTHENTICATED_SOURCE")

    def test_authenticated_buffer_survives_source_replacement(self):
        original = Path.read_bytes
        reads = []

        def read_once(path):
            raw = original(path)
            if path == self.path:
                reads.append(raw)
                path.write_bytes(SUBSTITUTE)
            return raw

        with patch.object(Path, "read_bytes", read_once):
            mod = self.load(digest(AUTHENTIC))
        self.assertEqual(reads, [AUTHENTIC])
        self.assertEqual(mod.selected(), "AUTHENTICATED_SOURCE")
        self.assertEqual(self.path.read_bytes(), SUBSTITUTE)

    def test_partial_execution_is_removed(self):
        raw = b'PARTIAL = True\nraise RuntimeError("init failed")\n'
        self.path.write_bytes(raw)
        with self.assertRaisesRegex(RuntimeError, "init failed"):
            self.load(digest(raw))
        self.assertNotIn(self.name, sys.modules)

    def test_compilation_failure_is_removed(self):
        raw = b"this is invalid Python!\n"
        self.path.write_bytes(raw)
        with self.assertRaises(SyntaxError):
            self.load(digest(raw))
        self.assertNotIn(self.name, sys.modules)

    def test_base_exception_is_removed(self):
        raw = b"raise SystemExit(17)\n"
        self.path.write_bytes(raw)
        with self.assertRaises(SystemExit):
            self.load(digest(raw))
        self.assertNotIn(self.name, sys.modules)

    def test_module_substitution_rejected(self):
        raw = b'import sys, types\nsys.modules[__name__] = types.ModuleType("forged")\n'
        self.path.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, "identity changed"):
            self.load(digest(raw))
        self.assertNotIn(self.name, sys.modules)

    def test_module_metadata_and_later_import_identity(self):
        mod = self.load()
        self.assertEqual(Path(mod.__file__), self.path)
        self.assertEqual(mod.__spec__.name, self.name)
        self.assertIsNotNone(mod.__loader__)
        self.assertEqual(mod.__package__, "")
        ns = {}
        exec("from " + self.name + " import selected", ns)
        self.assertIs(ns["selected"], mod.selected)
        self.assertIs(sys.modules[self.name], mod)

    def test_reparse_path_rejected_before_source_read(self):
        link = Path(os.environ["SHROOM_H2_REPARSE_FIXTURE"])
        self.assertNotEqual(link.absolute(), link.resolve())
        code_root = link / ("code_" + uuid.uuid4().hex)
        real_path = link.resolve() / code_root.name / "scripts/module2_dense_cache.py"
        real_path.parent.mkdir(parents=True)
        real_path.write_bytes(AUTHENTIC)
        self.path = code_root / "scripts/module2_dense_cache.py"
        original = Path.read_bytes

        def guarded_read(path):
            if path == self.path:
                raise AssertionError("unsafe source read through reparse point")
            return original(path)

        with patch.object(Path, "read_bytes", guarded_read):
            with self.assertRaises(ValueError):
                self.load(digest(AUTHENTIC))
        self.assertNotIn(self.name, sys.modules)


class CompatibilitySourceTests(SourceCases, Fixture):
    name = "_shroom_repository_verification"

    def load(self, pin=None):
        module, catalog = V.load_compatibility(self.work, {"compatibility": {
            "path": self.path.relative_to(self.work).as_posix(),
            "sha256": pin or digest(AUTHENTIC)}})
        self.assertEqual(catalog.root, self.work)
        return module

    def test_previous_module_restored_on_execution_failure(self):
        previous = types.ModuleType(self.name)
        sys.modules[self.name] = previous
        raw = b'raise RuntimeError("failed replacement")\n'
        self.path.write_bytes(raw)
        with self.assertRaises(RuntimeError):
            self.load(digest(raw))
        self.assertIs(sys.modules[self.name], previous)

    def test_catalog_initialization_failure_restores_registration(self):
        raw = b'class Catalog:\n def __init__(self, root): raise ValueError("catalog failed")\n'
        self.path.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, "catalog failed"):
            self.load(digest(raw))
        self.assertNotIn(self.name, sys.modules)

    def test_original_loader_reproduces_the_cache_attack(self):
        self.cache(SUBSTITUTE)
        self.assertEqual(digest(self.path.read_bytes()), digest(AUTHENTIC))
        spec = importlib.util.spec_from_file_location("old_cache_control", self.path)
        old = importlib.util.module_from_spec(spec)
        # Reproduce the former policy only on this harmless scratch fixture.
        with patch.object(importlib.machinery.SourceFileLoader, "get_code",
                          importlib._bootstrap_external.SourceLoader.get_code):
            spec.loader.exec_module(old)
        self.assertEqual(old.selected(), "CACHED_FALSE_PASS")
        self.assertEqual(self.load().selected(), "AUTHENTICATED_SOURCE")


class WorkerSourceTests(SourceCases, Fixture):
    name = "_authenticated_worker_fixture"

    def load(self, pin=None):
        tree = ast.parse(V.WORKER)
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                        and n.name == "authenticated_module")
        ns = {"Path": Path, "sys": sys, "hashlib": hashlib, "importlib": importlib}
        exec(compile(ast.Module(body=[function], type_ignores=[]), "<actual worker>", "exec"), ns)
        return ns["authenticated_module"](self.name, self.path, pin or digest(AUTHENTIC))


class NotebookSourceCases(SourceCases):
    name = "module2_dense_cache"

    def load(self, pin=None):
        ns = {"hashlib": hashlib, "os": os}
        env = {"SHROOM_MODULE2_CODE_ROOT": str(self.path.parent.parent),
               "SHROOM_MODULE2_HELPER_SHA256": pin or digest(AUTHENTIC)}
        with patch.dict(os.environ, env):
            exec(bootstrap(NOTEBOOKS / self.notebook), ns)
        return ns["_module2"]

    def test_forged_matching_notebook_pin_rejected(self):
        forged = types.ModuleType(self.name)
        forged.__file__ = str(self.path)
        forged._notebook_pin = digest(AUTHENTIC)
        forged.EXECUTED = "FORGED_PRELOADED_MODULE"
        sys.modules[self.name] = forged
        with self.assertRaisesRegex(ValueError, "restart the kernel"):
            self.load()
        self.assertIs(sys.modules[self.name], forged)

    def test_repeated_setup_requires_fresh_kernel(self):
        first = self.load()
        with self.assertRaisesRegex(ValueError, "restart the kernel"):
            self.load()
        self.assertIs(sys.modules[self.name], first)
        self.assertEqual(first.selected(), "AUTHENTICATED_SOURCE")

    def test_unmarked_preloaded_module_also_rejected(self):
        sys.modules[self.name] = types.ModuleType(self.name)
        with self.assertRaisesRegex(ValueError, "restart the kernel"):
            self.load()


class HoldoutSourceTests(NotebookSourceCases, Fixture):
    notebook = "shroom_rag_e5_module2_holdout_evaluation.ipynb"


class PhaseBSourceTests(NotebookSourceCases, Fixture):
    notebook = "shroom_rag_e5_module2_phase_b_evaluation.ipynb"


class RetrievalSourceTests(NotebookSourceCases, Fixture):
    notebook = "shroom_rag_e5_module2_retrieval.ipynb"


class WorkerIntegrationTests(Fixture):
    name = "phase25_resume_test"

    def worker(self, raw, *, cache=None, pin=None, cli=False, script=False):
        self.path.write_bytes(raw)
        if cache is not None:
            self.cache(cache)
        run = self.fixture / ("run_" + uuid.uuid4().hex)
        run.mkdir()
        env = {"SHROOM_TEST_SOURCE_SHA256": pin or digest(raw)}
        args = [str(run / "worker.py"), str(ROOT), str(run), str(self.path), "1"]
        if cli:
            env.update(SHROOM_TEST_CLI=str(self.path), SHROOM_TEST_CLI_PIN=pin or digest(raw))
            args.extend(["--cli", "--fixture"])
        elif script:
            args.extend(["--script", "--fixture"])
        stream = io.StringIO()
        old_get_code = importlib.machinery.SourceFileLoader.get_code
        old_main = sys.modules.get("__main__", ABSENT)
        try:
            # The outer real verifier worker's audit hook remains installed.
            # Avoid accumulating process-global hooks during in-process tests.
            with patch.dict(os.environ, env), patch.object(sys, "argv", args), \
                 patch.object(sys, "addaudithook"), redirect_stdout(stream):
                with self.assertRaises(SystemExit) as exit_info:
                    exec(compile(V.WORKER, args[0], "exec"), {"__file__": args[0]})
            return exit_info.exception.code, stream.getvalue()
        finally:
            importlib.machinery.SourceFileLoader.get_code = old_get_code
            if old_main is ABSENT:
                sys.modules.pop("__main__", None)
            else:
                sys.modules["__main__"] = old_main

    def test_full_worker_cached_pass_cannot_hide_failing_test(self):
        failing = b'import unittest\nclass T(unittest.TestCase):\n def test_real(self): self.fail("AUTHENTIC_TEST_FAILURE")\n'
        passing = failing.replace(b'self.fail("AUTHENTIC_TEST_FAILURE")', b"self.assertTrue(True)")
        code, text = self.worker(failing, cache=passing)
        detail = json.loads(text.strip().splitlines()[-1])
        self.assertEqual(code, 1)
        self.assertEqual(detail["tests"], 1)
        self.assertEqual(detail["failures"], 1)
        self.assertIn("AUTHENTIC_TEST_FAILURE", detail["output"])

    def test_full_worker_valid_source_passes(self):
        raw = b'import unittest\nclass T(unittest.TestCase):\n def test_real(self): self.assertTrue(True)\n'
        code, text = self.worker(raw, cache=SUBSTITUTE)
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(text)["pass"])

    def test_full_worker_wrong_pin_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            self.worker(AUTHENTIC, pin="0" * 64)
        self.assertNotIn(self.name, sys.modules)

    def test_cli_executes_authenticated_source_and_preserves_metadata(self):
        raw = b'import sys\nassert __name__ == "__main__"\nassert __spec__.name == "__main__"\nassert sys.modules[__name__].__file__ == __file__\nassert sys.argv[1:] == ["--fixture"]\nprint("AUTHENTIC_CLI")\n'
        code, text = self.worker(raw, cache=b'print("CACHED_FALSE_PASS")\n', cli=True)
        self.assertEqual(code, 0)
        self.assertEqual(text.strip(), "AUTHENTIC_CLI")

    def test_cli_wrong_pin_does_not_execute(self):
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            self.worker(b'print("MUST_NOT_EXECUTE")\n', pin="0" * 64, cli=True)

    def test_script_suites_execute_the_authenticated_main_buffer(self):
        raw = b'import sys\nassert __name__ == "__main__"\nassert sys.argv[1:] == ["--fixture"]\nprint("AUTHENTIC_SCRIPT")\n'
        code, text = self.worker(raw, cache=b'print("CACHED_FALSE_PASS")\n', script=True)
        self.assertEqual(code, 0)
        self.assertEqual(text.strip(), "AUTHENTIC_SCRIPT")

    def test_nested_source_import_cannot_use_a_cached_substitute(self):
        nested = self.fixture / "nested.py"
        nested.write_bytes(AUTHENTIC)
        saved = self.path
        self.path = nested
        self.cache(SUBSTITUTE)
        self.path = saved
        raw = ("import unittest, importlib.util\n"
               "spec = importlib.util.spec_from_file_location('nested_fixture', " + repr(str(nested)) + ")\n"
               "mod = importlib.util.module_from_spec(spec)\n"
               "spec.loader.exec_module(mod)\n"
               "class T(unittest.TestCase):\n"
               " def test_source(self): self.assertEqual(mod.selected(), 'AUTHENTICATED_SOURCE')\n").encode()
        code, text = self.worker(raw)
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(text)["pass"])

    def test_worker_keeps_offline_and_write_guards(self):
        tree = ast.parse(V.WORKER)
        functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("local", "audit")]
        events = dict(writes=0, network_attempts=0, subprocess_attempts=0, outside_writes=0, ml_import_attempts=0)
        ns = {"Path": Path, "os": os, "ROOT": ROOT, "WORK": self.fixture,
              "events": events, "_permitted_cli": [None]}
        exec(compile(ast.Module(body=functions, type_ignores=[]), "<actual worker audit>", "exec"), ns)
        for event, args in [
            ("socket.connect", ()),
            ("open", (str(self.fixture.parent / "forbidden"), "w", os.O_CREAT)),
            ("subprocess.Popen", ("unreviewed", ["unreviewed"], str(self.fixture), {})),
            ("import", ("torch",)),
        ]:
            with self.subTest(event=event), self.assertRaises((PermissionError, ImportError)):
                ns["audit"](event, args)
        self.assertEqual(events["network_attempts"], 1)
        self.assertEqual(events["outside_writes"], 1)
        self.assertEqual(events["subprocess_attempts"], 1)
        self.assertEqual(events["ml_import_attempts"], 1)

    def test_runner_passes_pinned_test_digest_to_worker(self):
        tree = ast.parse(VERIFIER.read_bytes())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run_tests")
        values = [k.value for n in ast.walk(fn) if isinstance(n, ast.Call)
                  for k in n.keywords if k.arg == "SHROOM_TEST_SOURCE_SHA256"]
        self.assertEqual(len(values), 1)
        self.assertEqual(ast.unparse(values[0]), "suite['sha256']")
