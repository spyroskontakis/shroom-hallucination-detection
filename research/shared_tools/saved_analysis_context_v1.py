"""Explicit original-input and isolated-output context for saved E6-v3 analysis.

No model, evaluator or metric is implemented here. Source transformations reuse
the reviewed E6-v4 H2 engine. Historical validation always reads original inputs.
"""
from __future__ import annotations
import ast
import importlib.util
import os
from pathlib import Path
import sys
import types

VERSION = "shroom-e6-v3-saved-analysis-h2-v1"
LEGACY = "RAG/results/rag_e6_v3/error_analysis/"
ENGINE = "research/experiments/phase2_rag_features/e6_feature_extensions/v4/verification/h2_adapter_v1.py"
ENGINE_SHA256 = "b96923c93678e1e81d936b0bb43c672fa7d9b7b94561f63e3901a2c8ba86ae2b"
SHARED_SHA256 = "c668cce4282d6865373f50525fc78fb5a87b5be14463cc4fef3e93284b326247"
BASELINE = "11822d92070cd29360445cb4dacd8d110c655248"
BASE_TREE = "81690aef257042354b6886f145919ae794e941ee"
GATE = 'if "_H2_CTX" not in globals():\n    raise RuntimeError("Use the verified saved-analysis context; direct execution is disabled")\n_H2_CTX.source_gate(__file__)\n'


def engine(root):
    path = Path(root) / ENGINE
    # Reject path redirection before importing the already reviewed stdlib engine.
    for p in (path, *path.parents):
        if p.is_symlink() or (p.exists() and getattr(p.lstat(), "st_file_attributes", 0) & 1024):
            raise ValueError("Reparse source rejected")
    raw = path.read_bytes()
    import hashlib
    if hashlib.sha256(raw).hexdigest() != ENGINE_SHA256:
        raise ValueError("Reviewed H2 engine identity mismatch")
    spec = importlib.util.spec_from_file_location("_saved_analysis_h2_engine", path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


def adapt(raw, original, reviewed_engine):
    """Only root/IO bindings plus a fail-closed entry gate; no algorithm edits."""
    result = reviewed_engine.adapted_source(raw, original).decode("utf-8")
    tree = ast.parse(result)
    lines = result.splitlines(True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line.encode("utf-8")))
    edits = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in {"V2", "V3"}:
            n = node.value
            edits.append((starts[n.lineno - 1] + n.col_offset, starts[n.end_lineno - 1] + n.end_col_offset,
                          ("_H2_CTX.binding(" + repr(node.targets[0].id) + ", 'analysis')").encode()))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "write_text":
            n = node.func.value
            text = ast.get_source_segment(result, n)
            edits.append((starts[n.lineno - 1] + n.col_offset, starts[n.end_lineno - 1] + n.end_col_offset,
                          ("_H2_CTX.io_path(" + text + ", 'w')").encode()))
    payload = result.encode()
    for a, b in zip(sorted(edits), sorted(edits)[1:]):
        if a[1] > b[0]:
            raise ValueError("Overlapping analysis adaptation")
    for a, b, replacement in sorted(edits, reverse=True):
        payload = payload[:a] + replacement + payload[b:]
    result = payload.decode()
    tree = ast.parse(result)
    offset = 0
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str):
        offset = tree.body[0].end_lineno
    # These four historical modules have no future import. Reject a new schema.
    if any(isinstance(n, ast.ImportFrom) and n.module == "__future__" for n in tree.body):
        raise ValueError("Unreviewed future-import source")
    lines = result.splitlines(True)
    lines.insert(offset, GATE)
    final = "".join(lines).encode()
    ast.parse(final)
    if projection(raw, reviewed_engine) != projection(final, reviewed_engine):
        raise ValueError("Scientific source differs outside reviewed IO bindings")
    return final


def projection(raw, reviewed_engine):
    text = raw.decode("utf-8")
    if GATE in text:
        if text.count(GATE) != 1:
            raise ValueError("Ambiguous entry gate")
        text = text.replace(GATE, "")
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in {"V2", "V3"}:
            node.value = ast.Constant("REVIEWED_ORIGINAL_INPUT_ROOT")
    return reviewed_engine.scientific_projection(ast.unparse(ast.fix_missing_locations(tree)).encode())


class AnalysisContext:
    def __init__(self, root, contract, *, expected_sha256, original_root, run_dir, cache_dir, temporary_dir):
        root = Path(root)
        if not root.is_absolute() or ".." in root.parts:
            raise ValueError("Explicit source root required")
        self.e = engine(root)
        self.root = self.e.checked_path(root)
        # Reuse the fresh pinned H2-P0 loader. A previously mutated/cached module
        # cannot become the validator for a new current-layout context.
        context_path = self.e.checked_path(self.root / "research/shared_tools/repository_source_context_v1.py")
        context_raw = context_path.read_bytes()
        path = self.e.checked_path(contract)
        if not path.is_relative_to(self.root):
            raise ValueError("Contract outside reviewed source tree")
        raw = path.read_bytes()
        if self.e.digest(raw) != expected_sha256 or not __import__("re").fullmatch("[0-9a-f]{64}", expected_sha256 or ""):
            raise ValueError("Independent analysis contract pin mismatch")
        # Parse with a fresh independently pinned base validator, before trusting
        # any metadata in the new contract. No cached helper object is used.
        shared_path = self.root / "research/shared_tools/canonical_execution_context.py"
        shared_raw = self.e.checked_path(shared_path).read_bytes()
        if self.e.digest(shared_raw) != SHARED_SHA256:
            raise ValueError("Shared H2 validator mismatch")
        temp_name = "_saved_analysis_initial_schema_validator"
        spec = importlib.util.spec_from_file_location(temp_name, shared_path)
        initial = importlib.util.module_from_spec(spec)
        previous = sys.modules.get(temp_name)
        sys.modules[temp_name] = initial
        try:
            exec(compile(shared_raw, str(shared_path), "exec"), initial.__dict__)
        finally:
            if previous is None:
                sys.modules.pop(temp_name, None)
            else:
                sys.modules[temp_name] = previous
        self.h = initial
        data = self.h.strict_json(raw.decode())
        self.h.keys(data, ("version", "baseline", "adapter", "artifacts", "required_inputs", "runtime_status"))
        if data["version"] != VERSION or data["baseline"] != {"commit": BASELINE, "tree": BASE_TREE} or data["runtime_status"] != "NOT VERIFIED":
            raise ValueError("Unrecognized analysis version/context")
        self.h.keys(data["adapter"], ("path", "sha256", "engine_sha256", "shared_sha256", "source_context_sha256"))
        if data["adapter"]["path"] != "research/shared_tools/saved_analysis_context_v1.py" or data["adapter"]["engine_sha256"] != ENGINE_SHA256 or data["adapter"]["shared_sha256"] != SHARED_SHA256:
            raise ValueError("Unknown adapter lineage")
        if self.h.sha256(Path(__file__).read_bytes()) != data["adapter"]["sha256"]:
            raise ValueError("Analysis adapter identity mismatch")
        if self.h.sha256(context_raw) != data["adapter"]["source_context_sha256"]:
            raise ValueError("Shared source-context identity mismatch")
        spec = importlib.util.spec_from_file_location("_saved_analysis_source_context", context_path)
        context_api = importlib.util.module_from_spec(spec)
        exec(compile(context_raw, str(context_path), "exec"), context_api.__dict__)
        self.h = context_api.load_shared_validator(self.root)
        self.artifacts = {}
        targets = set()
        for item in data["artifacts"]:
            self.h.keys(item, ("original_path", "current_path", "original_sha256", "original_git_blob", "current_sha256", "identity"))
            old = self.h.logical_path(item["original_path"])
            target = self.h.logical_path(item["current_path"])
            if not old.startswith(LEGACY) or old in self.artifacts or target.casefold() in targets:
                raise ValueError("Duplicate or out-of-scope analysis source")
            for key in ("original_sha256", "current_sha256"):
                self.h.digest(item[key])
            self.h.digest(item["original_git_blob"], 40)
            if item["identity"] not in {"RELOCATED_BYTE_IDENTICAL", "ADAPTED_IO_AND_ENTRY_GATE"}:
                raise ValueError("Unreviewed source role")
            source = self.h.confined(self.root, target)
            if not source.is_file() or self.h.sha256(source.read_bytes()) != item["current_sha256"]:
                raise ValueError("Current analysis identity mismatch")
            self.artifacts[old] = item
            targets.add(target.casefold())
        if len(self.artifacts) != 9:
            raise ValueError("Incomplete analysis source set")
        self.original = self.e.checked_path(original_root)
        if not self.original.is_dir() or self.e.overlap(self.original, self.root):
            raise ValueError("Original evidence must be separate and read only")
        self.required = {}
        for item in data["required_inputs"]:
            self.h.keys(item, ("path", "sha256", "evidence_owner"))
            key = self.h.logical_path(item["path"])
            want = self.h.digest(item["sha256"])
            if key in self.required and self.required[key] != want:
                raise ValueError("Conflicting historical input identities")
            self.required[key] = want
        if not self.required:
            raise ValueError("Missing historical input contract")
        # Validate all required H0 evidence before output mkdir or module loading.
        inputs = [self.original_path(key) for key in self.required]
        self.run, self.cache, self.temp = [self.e.checked_path(p) for p in (run_dir, cache_dir, temporary_dir)]
        roots = [self.root, self.original, self.run, self.cache, self.temp]
        if any(self.e.overlap(a, b) for i, a in enumerate(roots) for b in roots[i + 1:]):
            raise ValueError("Source/input/output/cache/temporary roots overlap")
        for p in (self.run, self.cache, self.temp):
            self.h.plan_run(p, source_roots=[self.root, self.original], input_paths=inputs, output_names=["owned-output.json"])
        self.created = set()
        self.ready = False

    def original_path(self, key):
        key = self.h.logical_path(key)
        if key not in self.required:
            raise ValueError("Undeclared historical input")
        path = self.h.confined(self.original, key)
        if not path.is_file() or self.h.sha256(path.read_bytes()) != self.required[key]:
            raise ValueError("Missing or changed authentic original input")
        return path

    def binding(self, name, kind):
        if not self.ready:
            raise ValueError("Context not prepared")
        return {"ROOT": self.original, "OUT": self.run,
                "V2": self.original / "RAG/results/rag_e6_v2",
                "V3": self.original / "RAG/results/rag_e6_v3"}[name]

    def source_gate(self, value):
        if not self.ready:
            raise ValueError("Context not prepared")
        path = self.e.checked_path(Path(value))
        matches = [x for x in self.artifacts.values() if self.root / x["current_path"] == path]
        if len(matches) != 1 or self.h.sha256(path.read_bytes()) != matches[0]["current_sha256"]:
            raise ValueError("Unrecognized current source")

    def io_path(self, value, mode="r"):
        path = self.e.checked_path(Path(value))
        if not self.ready:
            raise ValueError("Unprepared I/O context")
        if any(c in str(mode) for c in "wax+"):
            if not path.is_relative_to(self.run) or (path.exists() and path not in self.created):
                raise ValueError("Historical or unowned output overwrite forbidden")
            return path
        if path.is_relative_to(self.run):
            if path in self.created and path.is_file():
                return path
            return self.original_path(LEGACY + path.relative_to(self.run).as_posix())
        if path.is_relative_to(self.original):
            return self.original_path(path.relative_to(self.original).as_posix())
        raise ValueError("Undeclared input address")

    def asset_base(self, value):
        return self.e.checked_path(value)

    def inventory(self, base, pattern, kind):
        if Path(base) != self.run or pattern != "*" or kind != "iterdir":
            raise ValueError("Unreviewed analysis inventory")
        result = {Path(k).name: self.original_path(k) for k in self.required
                  if k.startswith(LEGACY) and "/" not in k[len(LEGACY):]}
        result.update({p.name: p for p in self.created if p.parent == self.run and p.is_file()})
        return list(result.values())

    def prepare(self):
        """Future approved runs only; no experiment is automatically started."""
        if self.ready:
            raise ValueError("Context already prepared")
        # Recheck evidence and ownership immediately before the first mutation.
        for item in self.artifacts.values():
            path = self.h.confined(self.root, item["current_path"])
            if not path.is_file() or self.h.sha256(path.read_bytes()) != item["current_sha256"]:
                raise ValueError("Current source changed after validation")
        for key in self.required:
            self.original_path(key)
        for p in (self.run, self.cache, self.temp):
            self.e.checked_path(p)
            self.e.outside_git(p)
            if p.exists():
                raise ValueError("Output root appeared after validation")
        for p in (self.run, self.cache, self.temp):
            p.mkdir()
        for key in ("TEMP", "TMP", "TMPDIR", "JOBLIB_TEMP_FOLDER"):
            os.environ[key] = str(self.temp)
        for key in ("HF_HOME", "TRANSFORMERS_CACHE", "HF_DATASETS_CACHE", "XDG_CACHE_HOME", "TORCH_HOME", "MPLCONFIGDIR"):
            os.environ[key] = str(self.cache)
        for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE", "PYTHONDONTWRITEBYTECODE"):
            os.environ[key] = "1"
        sys.dont_write_bytecode = True
        self.ready = True
        sys.addaudithook(self._guard)

    def _guard(self, event, args):
        if event.startswith("socket.") or event in {"subprocess.Popen", "os.system", "os.exec", "os.posix_spawn"}:
            raise PermissionError("Saved analysis is offline and has no child processes")
        if event == "import" and args[0].split(".")[0] in {"torch", "transformers", "sklearn", "google", "modal", "openai"}:
            raise PermissionError("No model/training/API imports in saved analysis")
        if event == "open" and not isinstance(args[0], int):
            path = self.e.checked_path(Path(os.fsdecode(args[0])))
            mode, flags = args[1:3]
            writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            if writing:
                if not any(path.is_relative_to(p) for p in (self.run, self.cache, self.temp)):
                    raise PermissionError("Write outside isolated run/cache/temp")
                if path.is_file() and path not in self.created:
                    raise PermissionError("Existing unowned output")
                self.created.add(path)
        if event in {"os.mkdir", "os.remove", "os.rmdir", "os.rename", "os.link", "os.symlink", "os.chmod", "os.utime", "os.truncate"}:
            for value in args[:2] if event in {"os.rename", "os.link", "os.symlink"} else args[:1]:
                if not isinstance(value, int) and not any(self.e.checked_path(Path(os.fsdecode(value))).is_relative_to(p) for p in (self.run, self.cache, self.temp)):
                    raise PermissionError("Mutation outside isolated roots")

    def load(self, original):
        item = self.artifacts.get(original)
        if item is None or not original.endswith(".py") or not self.ready:
            raise ValueError("Unreviewed or unprepared module")
        source = self.root / item["current_path"]
        self.source_gate(source)
        module = types.ModuleType("_current_saved_analysis_" + source.stem)
        module.__file__ = str(source)
        module.__dict__["_H2_CTX"] = self
        exec(compile(source.read_bytes(), str(source), "exec"), module.__dict__)
        return module
