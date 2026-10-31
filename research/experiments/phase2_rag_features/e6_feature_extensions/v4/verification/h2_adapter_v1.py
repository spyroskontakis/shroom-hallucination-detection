"""Versioned E6-v4 source/IO adapter; raw historical files are never rewritten.

Plan mode verifies source identity only. It never certifies numerical reproduction.
Execution requires a separately approved original-input context and explicit roots.
"""
from __future__ import annotations
import argparse
import ast
import contextlib
import hashlib
import importlib.abc
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import sys
import uuid

VERSION = "shroom-e6-v4-h2-v1"
BASELINE = "11822d92070cd29360445cb4dacd8d110c655248"
BASE_TREE = "81690aef257042354b6886f145919ae794e941ee"
LEGACY = "RAG/results/rag_e6_v4/"
SHARED_SHA256 = "c668cce4282d6865373f50525fc78fb5a87b5be14463cc4fef3e93284b326247"
DEFAULT_CONTRACT = "research/experiments/phase2_rag_features/e6_feature_extensions/v4/configs/current_layout_h2_v1.json"
HISTORICAL_READ_FUNCTIONS = frozenset({"protected", "verify_inputs", "verify_models", "assets"})

class H2Error(ValueError):
    """Unverifiable declaration or an unsafe operation; no fallback is allowed."""

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def repository_root(origin=__file__):
    for parent in Path(origin).resolve().parents:
        if (parent / "research/shared_tools/canonical_execution_context.py").is_file() and (parent / "research/README.md").is_file():
            return parent
    raise H2Error("Reviewed repository root not found")

def shared(root):
    path = root / "research/shared_tools/canonical_execution_context.py"
    raw = path.read_bytes()
    if digest(raw) != SHARED_SHA256:
        raise H2Error("Shared H2 validator identity mismatch")
    name = "_e6_v4_shared_h2_validator"
    if name in sys.modules and Path(sys.modules[name].__file__) != path:
        raise H2Error("Ambiguous preloaded shared validator")
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        exec(compile(raw, str(path), "exec"), module.__dict__)
    return sys.modules[name]

def checked_path(value):
    if not isinstance(value, (str, Path)) or not str(value):
        raise H2Error("Explicit absolute local path required")
    p = Path(value)
    if not p.is_absolute() or ".." in p.parts or p.drive.startswith("\\\\"):
        raise H2Error("Relative, traversal or UNC path rejected")
    for part in p.parts[1:]:
        if ":" in part or part.endswith((".", " ")) or re.fullmatch(r"(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])", part.split(".")[0]):
            raise H2Error("Ambiguous/device path rejected")
    for item in (p, *p.parents):
        try:
            st = item.lstat()
        except FileNotFoundError:
            continue
        if item.is_symlink() or getattr(st, "st_file_attributes", 0) & 1024:
            raise H2Error("Reparse/symlink path rejected")
    return p

def overlap(a, b):
    return a == b or a.is_relative_to(b) or b.is_relative_to(a)

def outside_git(p):
    if any((x / ".git").exists() or ((x / "HEAD").is_file() and (x / "objects").is_dir()) for x in (p, *p.parents)):
        raise H2Error("Writable root is inside Git")

def _canonical_ast(raw):
    # Source hash and canonical AST identity are recorded separately.
    def encode(node):
        if isinstance(node, ast.AST):
            return [type(node).__name__, [[k, encode(v)] for k, v in ast.iter_fields(node) if not (k == "type_params" and not v)]]
        if isinstance(node, list):
            return [encode(v) for v in node]
        if isinstance(node, bytes):
            return ["bytes", node.hex()]
        if isinstance(node, complex) or node is Ellipsis:
            return [type(node).__name__, repr(node)]
        return node
    return json.dumps(encode(ast.parse(raw.decode("utf-8-sig"), feature_version=(3, 11))), ensure_ascii=True, separators=(",", ":"))

def _scientific_nodes(raw):
    tree = ast.parse(raw.decode("utf-8-sig"), feature_version=(3, 11))
    return {n.name: digest(_canonical_ast(ast.unparse(n).encode()).encode()) for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.ClassDef))}

def adapted_source(raw, logical):
    """Apply only declared path, import-path, IO and historical-read operations.

    Uses byte spans rather than ast.unparse so the rendered source identity does
    not silently depend on an AST pretty-printer or alter saved scientific text.
    """
    if not logical.endswith(".py") or "/packages/" in logical or logical.endswith("/scripts/structure.py"):
        return raw
    text = raw.decode("utf-8-sig")
    lines = text.splitlines(True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line.encode("utf-8")))
    payload = text.encode("utf-8")
    tree = ast.parse(text, feature_version=(3, 11))
    edits = []
    def span(n):
        return starts[n.lineno-1] + n.col_offset, starts[n.end_lineno-1] + n.end_col_offset
    def source(n):
        a, b = span(n)
        return payload[a:b].decode("utf-8")
    def replace(n, value):
        a, b = span(n)
        edits.append((a, b, value.encode("utf-8")))
    kind = "execution" if "/execution/" in logical else "compatibility_analysis" if "/compatibility_analysis/" in logical else "scripts"
    roots = {"ROOT", "OUT", "HERE", "V4"}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in roots:
            name = node.targets[0].id
            replace(node.value, "_H2_CTX.binding(" + repr(name) + ", " + repr(kind) + ")")
    root_spans = [(a, b) for a, b, _ in edits]
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        a, b = span(node)
        if any(x <= a and b <= y for x, y in root_spans):
            continue
        fn = node.func
        if isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Attribute) and isinstance(fn.value.value, ast.Name) and fn.value.value.id == "sys" and fn.value.attr == "path" and fn.attr == "insert":
            replace(node, "_H2_CTX.install_code_paths()")
            continue
        if isinstance(fn, ast.Attribute) and fn.attr in ("read_text", "read_bytes", "open"):
            mode = source(node.args[0]) if fn.attr == "open" and node.args else "'r'"
            for kw in node.keywords:
                if kw.arg == "mode":
                    mode = source(kw.value)
            replace(fn.value, "_H2_CTX.io_path(" + source(fn.value) + ", " + mode + ")")
        elif isinstance(fn, ast.Attribute) and fn.attr == "is_relative_to" and node.args:
            replace(node.args[0], "_H2_CTX.asset_base(" + source(node.args[0]) + ")")
        elif isinstance(fn, ast.Attribute) and fn.attr in ("glob", "rglob", "iterdir"):
            pattern = source(node.args[0]) if node.args else "'*'"
            replace(node, "_H2_CTX.inventory(" + source(fn.value) + ", " + pattern + ", " + repr(fn.attr) + ")")
        elif isinstance(fn, ast.Name) and fn.id == "open" and node.args:
            mode = source(node.args[1]) if len(node.args) > 1 else "'r'"
            replace(node.args[0], "_H2_CTX.io_path(" + source(node.args[0]) + ", " + mode + ")")
        elif isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name) and fn.value.id == "subprocess" and fn.attr == "check_output":
            # The legacy diagnosis only requests read-only git state.
            if node.args:
                replace(node, "_H2_CTX.original_git(" + source(node.args[0]) + ", text=" +
                        ("True" if any(k.arg == "text" and isinstance(k.value, ast.Constant) and k.value.value is True for k in node.keywords) else "False") + ")")
    ordered = sorted(edits)
    for left, right in zip(ordered, ordered[1:]):
        if left[1] > right[0]:
            raise H2Error("Overlapping IO transformation; source requires review")
    for a, b, value in reversed(ordered):
        payload = payload[:a] + value + payload[b:]
    result = payload.decode("utf-8")
    # Preserve H0 expected-value checks in a distinct original-evidence domain.
    tree = ast.parse(result, feature_version=(3, 11))
    lines = result.splitlines(True)
    for n in sorted((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in HISTORICAL_READ_FUNCTIONS), key=lambda n: n.lineno, reverse=True):
        first = n.body[0].lineno - 1
        end = n.end_lineno
        indent = " " * n.body[0].col_offset
        body = lines[first:end]
        lines[first:end] = [indent + "with _H2_CTX.historical_reads():\n"] + ["    " + x for x in body]
    result = "".join(lines)
    ast.parse(result, feature_version=(3, 11))
    return result.encode("utf-8")

def scientific_projection(raw):
    """Remove only the explicitly reviewed IO/context differences from an AST.

    This is a change-scope proof, not proof of numerical/runtime equivalence.
    Parameters, formulas, control flow and feature definitions remain visible.
    """
    class Projection(ast.NodeTransformer):
        def visit_Assign(self, node):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in {"ROOT", "OUT", "HERE", "V4"}:
                node.value = ast.Constant("REVIEWED_EXECUTION_ROOT")
            return self.generic_visit(node)

        def visit_Expr(self, node):
            if isinstance(node.value, ast.Call):
                text = ast.unparse(node.value.func)
                if text in ("sys.path.insert", "_H2_CTX.install_code_paths"):
                    return ast.Expr(ast.Constant("REVIEWED_IMPORT_PATH"))
            return self.generic_visit(node)

        def visit_With(self, node):
            if len(node.items) == 1 and ast.unparse(node.items[0].context_expr) == "_H2_CTX.historical_reads()":
                return [self.visit(x) for x in node.body]
            return self.generic_visit(node)

        def visit_Call(self, node):
            name = ast.unparse(node.func)
            if name in ("_H2_CTX.io_path", "_H2_CTX.asset_base"):
                return self.visit(node.args[0])
            if name == "_H2_CTX.inventory":
                method = node.args[2].value
                node = ast.Call(ast.Attribute(node.args[0], method, ast.Load()), [] if method == "iterdir" else [node.args[1]], [])
            elif name in ("subprocess.check_output", "_H2_CTX.original_git"):
                node = ast.Call(ast.Name("REVIEWED_READ_ONLY_GIT_QUERY", ast.Load()), [node.args[0]], [])
            return self.generic_visit(node)
    tree = Projection().visit(ast.parse(raw.decode("utf-8-sig"), feature_version=(3, 11)))
    return _canonical_ast(ast.unparse(ast.fix_missing_locations(tree)).encode())


class Contract:
    def __init__(self, root, path, expected_sha256):
        self.root = checked_path(root)
        self.shared = shared(self.root)
        if re.fullmatch("[0-9a-f]{64}", expected_sha256 or "") is None:
            raise H2Error("Independent contract SHA-256 required")
        p = checked_path(path)
        if not p.resolve().is_relative_to(self.root.resolve()):
            raise H2Error("Contract must be inside the reviewed source repository")
        raw = p.read_bytes()
        if digest(raw) != expected_sha256:
            raise H2Error("Contract pin mismatch")
        try:
            self.data = self.shared.strict_json(raw.decode("utf-8"))
        except ValueError as exc:
            raise H2Error("Invalid/ambiguous contract JSON") from exc
        required = {"version", "baseline", "adapter", "artifacts", "historical_validation", "historical_aliases", "asset_directories", "model_requirement_record", "runtime_status"}
        if set(self.data) != required or self.data["version"] != VERSION or self.data["baseline"] != {"commit": BASELINE, "tree": BASE_TREE} or self.data["runtime_status"] != "NOT_RUNTIME_VERIFIED":
            raise H2Error("Unknown version, baseline or schema")
        self.pin = expected_sha256
        self.artifacts = {}
        current = set()
        for item in self.data["artifacts"]:
            if set(item) != {"historical_path", "h1", "current_path", "current_sha256", "adapted_source_sha256", "identity", "scientific_symbols"}:
                raise H2Error("Unknown artifact schema")
            old = self.shared.logical_path(item["historical_path"])
            target = self.shared.logical_path(item["current_path"])
            if not old.startswith(LEGACY) or old in self.artifacts or target.casefold() in current:
                raise H2Error("Duplicate/out-of-scope source identity")
            self.shared.digest(item["current_sha256"])
            self.shared.digest(item["adapted_source_sha256"])
            if set(item["h1"]) != {"sha256", "git_blob", "size_bytes"}:
                raise H2Error("Invalid H1 identity")
            self.shared.digest(item["h1"]["sha256"])
            self.shared.digest(item["h1"]["git_blob"], 40)
            if type(item["h1"]["size_bytes"]) is not int or item["h1"]["size_bytes"] < 0:
                raise H2Error("Invalid original size")
            if item["identity"] not in ("RELOCATED_BYTE_IDENTICAL", "HISTORICAL_ORIGINAL", "PHASE20_RELOCATED_BYTE_IDENTICAL"):
                raise H2Error("Unknown source role")
            # Transported raw artifacts are never silently presented as H2 source.
            if item["current_sha256"] != item["h1"]["sha256"]:
                raise H2Error("Raw historical byte identity changed")
            self.artifacts[old] = item
            current.add(target.casefold())
        if len(self.artifacts) != 62:
            raise H2Error("Incomplete E6-v4 source/record set")
        adapter = self.data["adapter"]
        if set(adapter) != {"path", "sha256", "shared_validator_sha256"} or adapter["shared_validator_sha256"] != SHARED_SHA256:
            raise H2Error("Invalid adapter lineage")
        ap = self.shared.logical_path(adapter["path"])
        if checked_path(self.root/ap).read_bytes() != Path(__file__).read_bytes() or digest(Path(__file__).read_bytes()) != adapter["sha256"]:
            raise H2Error("Adapter source identity mismatch")
        if self.data["asset_directories"] != ["packages", "compatibility_analysis/env", "compatibility_analysis/wheels"]:
            raise H2Error("Unknown asset directory bindings")
        aliases = self.data["historical_aliases"]
        if not isinstance(aliases, dict):
            raise H2Error("Invalid historical aliases")
        for old, new in aliases.items():
            self.shared.logical_path(old)
            self.shared.logical_path(new)
            if not old.startswith(LEGACY) or not new.startswith(LEGACY):
                raise H2Error("Out-of-scope historical alias")
        if not isinstance(self.data["historical_validation"], list):
            raise H2Error("Invalid historical requirements")
        if self.data["model_requirement_record"] != LEGACY+"provenance/compatibility.json":
            raise H2Error("Unknown model evidence record")
        self.source_paths = frozenset(checked_path(self.root/i["current_path"]) for i in self.artifacts.values())
        self.verify_sources()

    def verify_sources(self):
        for old, item in self.artifacts.items():
            path = checked_path(self.root/item["current_path"])
            raw = path.read_bytes()
            if digest(raw) != item["current_sha256"] or len(raw) != item["h1"]["size_bytes"] or self.shared.git_blob_id(raw) != item["h1"]["git_blob"]:
                raise H2Error("Source/record identity mismatch: " + old)
            derived = adapted_source(raw, old)
            if digest(derived) != item["adapted_source_sha256"]:
                raise H2Error("Adapted source identity mismatch: " + old)
            if old.endswith(".py") and scientific_projection(raw) != scientific_projection(derived):
                raise H2Error("Adaptation exceeds reviewed IO/context scope: " + old)
            if old.endswith(".py") and _scientific_nodes(raw) != item["scientific_symbols"]:
                raise H2Error("Scientific symbol identity mismatch: " + old)
        return {"status": "PASS", "raw_artifacts": len(self.artifacts), "runtime_status": "NOT_RUNTIME_VERIFIED"}

    def source(self, old):
        if old not in self.artifacts:
            raise H2Error("Undeclared source")
        path = checked_path(self.root/self.artifacts[old]["current_path"])
        if digest(path.read_bytes()) != self.artifacts[old]["current_sha256"]:
            raise H2Error("Current source changed: " + old)
        return path

    def expected_originals(self, profile):
        """Derive expected values only from pinned, unchanged historical records."""
        if profile not in ("diagnosis", "amended"):
            raise H2Error("Unknown original execution profile")
        result = {}
        for rule in self.data["historical_validation"]:
            if set(rule) != {"record", "pointer", "base", "profiles", "select"}:
                raise H2Error("Invalid original-evidence rule")
            if (rule["record"] not in self.artifacts or not isinstance(rule["pointer"], list)
                    or not rule["pointer"] or not isinstance(rule["select"], list)
                    or not rule["profiles"] or not set(rule["profiles"]) <= {"diagnosis", "amended"}):
                raise H2Error("Invalid original rule scope")
            if rule["base"]:
                self.shared.logical_path(rule["base"].rstrip("/"))
            if profile not in rule["profiles"]:
                continue
            obj = self.shared.strict_json(self.source(rule["record"]).read_text(encoding="utf-8"))
            for token in rule["pointer"]:
                obj = obj[token]
            if not isinstance(obj, dict):
                raise H2Error("Original hash-map unavailable")
            if rule["select"] and not set(rule["select"]) <= set(obj):
                raise H2Error("Required original identity absent from historical record")
            for name, expected in obj.items():
                if rule["select"] and name not in rule["select"]:
                    continue
                self.shared.digest(expected)
                relative = self.shared.logical_path(name.replace(chr(92), "/"))
                logical = self.shared.logical_path(rule["base"] + relative)
                if logical in result and result[logical] != expected:
                    raise H2Error("Conflicting historical stage identities")
                result[logical] = expected
        if not result:
            raise H2Error("Original execution profile has no authenticated requirements")
        # The public-safe model record declares content identities, not proof that
        # those assets or the original private pathname bindings are available.
        # Check every declared model and revision file before any run is created.
        model = self.shared.strict_json(self.source(self.data["model_requirement_record"]).read_text(encoding="utf-8"))
        required_assets = [(x["path"], x["sha256"]) for x in model["model_files"].values()]
        required_assets.append((model["cache_ref_path"], model["cache_ref_sha256"]))
        for name, pin in required_assets:
            logical = self.shared.logical_path(name)
            self.shared.digest(pin)
            if logical in result and result[logical] != pin:
                raise H2Error("Conflicting original model identity")
            result[logical] = pin
        return result

class SourceRef:
    """A read-only current source with its explicit legacy logical identity."""
    def __init__(self, context, old, actual=None):
        self.context, self.old = context, old
        self.path = checked_path(actual) if actual is not None else context.contract.source(old)
    def __lt__(self, other):
        return self.old < (other.old if isinstance(other, SourceRef) else str(other))
    def __eq__(self, other):
        return isinstance(other, SourceRef) and self.old == other.old and self.path == other.path
    def __hash__(self):
        return hash((self.old, self.path))
    def __fspath__(self):
        return str(self.path)
    @property
    def name(self):
        return self.path.name
    @property
    def parts(self):
        return self.path.parts
    def is_file(self):
        return self.path.is_file()
    def relative_to(self, base):
        base = Path(base)
        if not base.is_relative_to(self.context.run):
            raise H2Error("Source inventory base mismatch")
        relative_base = base.relative_to(self.context.run)
        return Path(self.old[len(LEGACY):]).relative_to(relative_base)
    def __getattr__(self, name):
        return getattr(self.path, name)

class RuntimeContext:
    def __init__(self, contract, original_root, run_dir, temp_dir, *, profile, resume_marker_sha256=None, synthetic=False):
        self.contract = contract
        self.original = checked_path(original_root)
        self.run = checked_path(run_dir)
        self.temp = checked_path(temp_dir)
        if not self.original.is_dir() or not self.temp.is_dir():
            raise H2Error("Explicit original and prepared temporary roots required")
        if overlap(self.run, self.original) or overlap(self.run, contract.root) or overlap(self.temp, self.run) or overlap(self.temp, self.original) or overlap(self.temp, contract.root):
            raise H2Error("Input/source/run/temp overlap")
        outside_git(self.run)
        outside_git(self.temp)
        if not self.run.parent.is_dir():
            raise H2Error("Run parent is missing")
        self.profile = profile
        self.synthetic = synthetic
        self.history = 0
        self.created = set()
        self.approved_git = None
        self.expected = {} if synthetic else contract.expected_originals(profile)
        for name, pin in self.expected.items():
            alias = contract.shared.logical_path(contract.data["historical_aliases"].get(name, name))
            path = checked_path(self.original/alias)
            if not path.is_file() or digest(path.read_bytes()) != pin:
                raise H2Error("Original evidence missing/mismatching: " + name)
        # No run/cache/temporary writes have occurred before all identity checks.
        self.original_paths = frozenset(checked_path(self.original/contract.data["historical_aliases"].get(k, k)) for k in self.expected)
        self.marker = self.run/"H2_RUN_IDENTITY.json"
        if self.run.exists():
            if not resume_marker_sha256 or not self.marker.is_file() or digest(self.marker.read_bytes()) != resume_marker_sha256:
                raise H2Error("Existing run has no independently pinned ownership marker")
            marker = contract.shared.strict_json(self.marker.read_text(encoding="utf-8"))
            info = self.run.stat()
            if marker.get("version") != VERSION or marker.get("source_role") != "H2_DERIVED_FROM_REVIEWED_H1":
                raise H2Error("Unknown run marker")
            if marker["contract_sha256"] != contract.pin or marker["root_identity"] != [info.st_dev, info.st_ino] or marker["profile"] != profile:
                raise H2Error("Run identity changed")
            # Resume requires a separate independently pinned complete output ledger.
            ledger_name = os.environ.get("SHROOM_E6_V4_LEDGER")
            ledger_pin = os.environ.get("SHROOM_E6_V4_LEDGER_SHA256")
            if not ledger_name or Path(ledger_name).name != ledger_name or not ledger_pin:
                raise H2Error("Pinned completed-stage output ledger required")
            lp = checked_path(self.run/ledger_name)
            if digest(lp.read_bytes()) != ledger_pin:
                raise H2Error("Output ledger pin mismatch")
            ledger = contract.shared.strict_json(lp.read_text(encoding="utf-8"))
            if set(ledger) != {"version", "contract_sha256", "runtime_status", "files"} or ledger["version"] != VERSION or ledger["contract_sha256"] != contract.pin or ledger["runtime_status"] != "NOT_RUNTIME_VERIFIED":
                raise H2Error("Unknown output ledger")
            actual = {p.relative_to(self.run).as_posix() for p in self.run.rglob("*") if p.is_file() and p != lp}
            if set(ledger["files"]) != actual:
                raise H2Error("Unowned file in resumed run")
            for name, pin in ledger["files"].items():
                if digest(checked_path(self.run/contract.shared.logical_path(name)).read_bytes()) != pin:
                    raise H2Error("Resumed output changed")
        elif resume_marker_sha256:
            raise H2Error("Declared resumed run is missing")
        self.resumed = self.run.exists()
        self._ready = False

    @contextlib.contextmanager
    def historical_reads(self):
        self.history += 1
        try:
            yield
        finally:
            self.history -= 1

    def binding(self, name, kind):
        if name == "ROOT":
            return self.original
        if name in ("OUT", "V4"):
            return self.run
        if name == "HERE":
            return self.run/kind
        raise H2Error("Unknown execution root")

    def _legacy_of(self, p):
        if p.is_relative_to(self.run):
            return LEGACY + p.relative_to(self.run).as_posix()
        return None

    def io_path(self, value, mode="r"):
        if isinstance(value, SourceRef):
            if any(c in str(mode) for c in "wax+"):
                raise H2Error("Source writes forbidden")
            if self.history:
                return self.original_path(value.old)
            return value.path
        p = checked_path(Path(value))
        writing = any(c in str(mode) for c in "wax+")
        if writing:
            if not (p.is_relative_to(self.run) or p.is_relative_to(self.temp)):
                raise H2Error("Write outside owned run/temp")
            old = self._legacy_of(p)
            if old in self.contract.artifacts and (old.endswith(".py") or "/packages/" in old or Path(old).name.startswith("E6_V4_PROTOCOL")):
                raise H2Error("Historical source/protocol output collision")
            if p.exists() and not ("a" in str(mode) and p in self.created):
                raise H2Error("Existing output must not be overwritten or adopted")
            return p
        old = self._legacy_of(p)
        if not self.history:
            p = self.asset_base(p)
        if self.history:
            if old is not None:
                return self.original_path(old)
            if p.is_relative_to(self.original):
                return self.original_path(p.relative_to(self.original).as_posix())
            raise H2Error("Undeclared original-evidence address")
        if old is not None:
            if old in self.contract.artifacts and (old.endswith(".py") or "/packages/" in old or Path(old).name.startswith("E6_V4_PROTOCOL")):
                return self.contract.source(old)
            # Prior diagnosis/configuration is an explicit H0 input, never H1 fallback.
            evidence = old.startswith(LEGACY+"compatibility_analysis/") or old in {
                LEGACY+"config/blocked_state_manifest.json", LEGACY+"config/run_config.json",
                LEGACY+"config/feature_schema.json", LEGACY+"config/structure_spec.json",
                LEGACY+"provenance/compatibility.json"}
            if evidence and not p.exists():
                return self.original_path(old)
            return p
        if p.is_relative_to(self.original):
            return self.original_path(p.relative_to(self.original).as_posix())
        if p.is_relative_to(self.temp):
            return p
        if p in self.contract.source_paths:
            return p
        raise H2Error("Undeclared input; explicit original binding required")

    def original_path(self, logical):
        logical = self.contract.shared.logical_path(logical)
        if not self.synthetic and logical not in self.expected:
            raise H2Error("Original artifact not declared in selected profile")
        alias = self.contract.data["historical_aliases"].get(logical, logical)
        alias = self.contract.shared.logical_path(alias)
        path = checked_path(self.original/alias)
        if not path.is_file():
            raise H2Error("Original artifact is missing: " + logical)
        if logical in self.expected and digest(path.read_bytes()) != self.expected[logical]:
            raise H2Error("Original artifact changed: " + logical)
        return path

    def inventory(self, base, pattern="*", kind="glob"):
        base = self.asset_base(checked_path(Path(base)))
        method = getattr(base, kind)
        physical = list(method() if kind == "iterdir" else method(pattern))
        result = {p.as_posix(): (SourceRef(self, LEGACY+p.relative_to(self.run).as_posix(), p) if p.is_relative_to(self.run) else p) for p in physical}
        if base.is_relative_to(self.run) and not self.history:
            import fnmatch
            rel = base.relative_to(self.run).as_posix()
            prefix = LEGACY + ("" if rel == "." else rel.rstrip("/")+"/")
            for old in self.contract.artifacts:
                tail = old[len(prefix):] if old.startswith(prefix) else None
                if tail is not None and (kind == "rglob" or "/" not in tail) and fnmatch.fnmatch(tail, pattern) and (old.endswith(".py") or Path(old).name.startswith("E6_V4_PROTOCOL")):
                    result[old] = SourceRef(self, old)
        return list(result.values())

    def asset_base(self, value):
        p = checked_path(Path(value))
        if p.is_relative_to(self.run):
            rel = p.relative_to(self.run).as_posix()
            if any(rel == prefix or rel.startswith(prefix+"/") for prefix in self.contract.data["asset_directories"]):
                return checked_path(self.original/(LEGACY+rel))
        return p

    def install_code_paths(self):
        # The shared scientific implementation is loaded once through the finder.
        # Full pinned third-party packages must come from explicit original inputs.
        package = checked_path(self.original/(LEGACY+"packages"))
        if package.is_dir() and str(package) not in sys.path:
            sys.path.insert(0, str(package))

    def prepare(self):
        if self._ready:
            return
        if self.synthetic:
            raise H2Error("Synthetic contexts cannot launch scientific entry points")
        if not self.resumed:
            self.run.mkdir(exist_ok=False)
            info = self.run.stat()
            marker = {"version": VERSION, "contract_sha256": self.contract.pin, "root_identity": [info.st_dev, info.st_ino],
                      "run_id": uuid.uuid4().hex, "profile": self.profile, "source_role": "H2_DERIVED_FROM_REVIEWED_H1", "runtime_status": "NOT_RUNTIME_VERIFIED"}
            self.marker.write_text(json.dumps(marker, sort_keys=True)+"\n", encoding="utf-8")
            for name in ("config", "inputs", "execution", "features", "evaluation", "provenance", "compatibility_analysis", "runtime_tmp"):
                (self.run/name).mkdir(exist_ok=True)
        for key in ("TEMP", "TMP", "TMPDIR", "XDG_CACHE_HOME", "HF_HOME", "HF_MODULES_CACHE", "MPLCONFIGDIR", "TORCH_HOME", "JOBLIB_TEMP_FOLDER"):
            os.environ[key] = str(self.temp)
        for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY", "PYTHONDONTWRITEBYTECODE"):
            os.environ[key] = "1"
        sys.dont_write_bytecode = True
        self._ready = True

    def policy(self, event, args):
        if event.startswith("socket."):
            raise H2Error("Network forbidden")
        if event in ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn"):
            if event != "subprocess.Popen" or self.approved_git is None or list(args[1]) != self.approved_git:
                raise H2Error("Child process forbidden")
        if event == "open" and not isinstance(args[0], int):
            p = checked_path(Path(os.fsdecode(args[0])))
            mode, flags = args[1:3]
            writing = (isinstance(mode, str) and any(x in mode for x in "wax+")) or (isinstance(flags, int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
            if writing:
                self.io_path(p, "a" if isinstance(flags, int) and flags & os.O_APPEND else "w")
                self.created.add(p)
            else:
                roots = (Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve())
                if not (p.is_relative_to(self.run) or p.is_relative_to(self.temp) or any(p.is_relative_to(x) for x in roots) or p == Path(os.devnull).resolve() or p in self.contract.source_paths or p in self.original_paths):
                    self.io_path(p, "r")
        if event in ("os.mkdir", "os.remove", "os.rmdir", "os.rename", "os.link", "os.symlink", "os.truncate"):
            for x in (args[:2] if event in ("os.rename", "os.link", "os.symlink") else args[:1]):
                if isinstance(x, int):
                    continue
                p = checked_path(Path(os.fsdecode(x)))
                if not (p.is_relative_to(self.run) or p.is_relative_to(self.temp)):
                    raise H2Error("Mutation outside run/temp")
                if event in ("os.link", "os.symlink"):
                    raise H2Error("Link creation forbidden")

    def original_git(self, argv, *, text=False):
        import subprocess
        if not isinstance(argv, list) or argv not in (["git","status","--short"], ["git","branch","--show-current"], ["git","diff","--stat"]):
            raise H2Error("Only declared read-only historical Git queries are supported")
        command = ["git","--no-optional-locks","-c","core.fsmonitor=false","-c","core.untrackedCache=false"] + argv[1:]
        self.approved_git = command
        try:
            return subprocess.check_output(command, cwd=self.original, text=text)
        finally:
            self.approved_git = None

    def load(self, logical, *, entry=False):
        libraries = {LEGACY+"execution/common.py", LEGACY+"scripts/v4_common.py", LEGACY+"scripts/structure.py"}
        if (self.synthetic and logical not in libraries) or (not entry and logical not in libraries):
            raise H2Error("Synthetic/library context cannot authorize an experiment")
        item = self.contract.artifacts.get(logical)
        if item is None:
            raise H2Error("Unknown entry/source")
        raw = self.contract.source(logical).read_bytes()
        derived = adapted_source(raw, logical)
        if digest(raw) != item["current_sha256"]:
            raise H2Error("Raw source changed")
        if digest(derived) != item["adapted_source_sha256"]:
            raise H2Error("Derived source changed")
        import types
        name = "__main__" if entry else "_h2_"+Path(logical).stem
        mod = types.ModuleType(name)
        mod.__file__ = str(self.contract.source(logical))
        mod.__dict__["_H2_CTX"] = self
        exec(compile(derived, "h2://"+VERSION+"/"+logical, "exec"), mod.__dict__)
        return mod

class ModuleFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def __init__(self, context):
        self.context = context
        self.aliases = {"common": LEGACY+"execution/common.py", "v4_common": LEGACY+"scripts/v4_common.py", "structure": LEGACY+"scripts/structure.py"}
    def find_spec(self, fullname, path=None, target=None):
        if fullname in self.aliases:
            return importlib.util.spec_from_loader(fullname, self)
    def create_module(self, spec):
        return None
    def exec_module(self, module):
        logical = self.aliases[module.__name__]
        module.__file__ = str(self.context.contract.source(logical))
        module.__dict__["_H2_CTX"] = self.context
        raw = self.context.contract.source(logical).read_bytes()
        item = self.context.contract.artifacts[logical]
        derived = adapted_source(raw, logical)
        if digest(raw) != item["current_sha256"] or digest(derived) != item["adapted_source_sha256"]:
            raise H2Error("Imported source identity changed")
        exec(compile(derived, "h2://"+VERSION+"/"+logical, "exec"), module.__dict__)

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", default=DEFAULT_CONTRACT)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--entry", help="Exact historical E6-v4 Python source identity")
    parser.add_argument("--execute", action="store_true", help="Requires separate scientific execution approval")
    args = parser.parse_args(argv)
    root = repository_root()
    path = Path(args.contract)
    contract = Contract(root, path if path.is_absolute() else root/path, args.expected_sha256)
    if not args.execute:
        if args.entry and args.entry not in contract.artifacts:
            raise H2Error("Undeclared source")
        print(json.dumps({"version": VERSION, "source_check": contract.verify_sources(), "entry": args.entry,
                          "mode": "PLAN_ONLY", "created_files": 0, "runtime_status": "NOT_RUNTIME_VERIFIED"}))
        return 0
    if not args.entry or not args.entry.endswith(".py") or "/packages/" in args.entry or Path(args.entry).name in ("common.py","v4_common.py","structure.py"):
        raise H2Error("Explicit scientific entry point required")
    original = os.environ.get("SHROOM_E6_V4_ORIGINAL_ROOT")
    run = os.environ.get("SHROOM_E6_V4_RUN_DIR")
    temporary = os.environ.get("SHROOM_E6_V4_TEMP_ROOT")
    if not all((original, run, temporary)):
        raise H2Error("Explicit original/run/temp roots required; no writes performed")
    profile = "diagnosis" if "/compatibility_analysis/" in args.entry or args.entry.endswith(("check_compatibility.py","document_blocker.py")) else "amended"
    context = RuntimeContext(contract, original, run, temporary, profile=profile)
    context.prepare()
    sys.addaudithook(context.policy)
    finder = ModuleFinder(context)
    for name in finder.aliases:
        if name in sys.modules:
            raise H2Error("Ambiguous preloaded project module")
    sys.meta_path.insert(0, finder)
    context.install_code_paths()
    try:
        context.load(args.entry, entry=True)
    finally:
        files = {}
        for p in context.run.rglob("*"):
            checked_path(p)
            if p.is_file():
                files[p.relative_to(context.run).as_posix()] = digest(p.read_bytes())
        ledger = context.run/("H2_STAGE_OUTPUTS_"+uuid.uuid4().hex+".json")
        payload = {"version": VERSION, "contract_sha256": contract.pin, "runtime_status": "NOT_RUNTIME_VERIFIED", "files": files}
        with ledger.open("x", encoding="utf-8") as stream:
            json.dump(payload, stream, sort_keys=True)
        print(json.dumps({"output_ledger": ledger.name, "sha256": digest(ledger.read_bytes()), "runtime_status": "NOT_RUNTIME_VERIFIED"}))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except H2Error as error:
        print("E6-v4 H2 validation failed: "+str(error), file=sys.stderr)
        raise SystemExit(2)
