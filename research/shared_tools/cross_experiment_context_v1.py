"""Strict E6-v2/v3 current binding; historical E9/E10/E11 readers are unchanged.

Plan is read-only. Historical expected values always address an explicit original
input tree, never an adapted source. No numerical reproduction is certified.
"""
from __future__ import annotations
import argparse
import ast
import importlib.util
import json
import os
from pathlib import Path
import sys

VERSION = "shroom-e6-cross-experiment-h2-v1"
CATALOG = "project_records/current_layout/e6_cross_experiment_h2_v1.json"
CATALOG_SHA256 = "d8660a9e9757d9fe2cf30a4e3222fca1355a9b7f11e08085b085abf84781fac7"
ENGINE = "research/experiments/phase2_rag_features/e6_feature_extensions/v4/verification/h2_adapter_v1.py"
ENGINE_SHA256 = "b96923c93678e1e81d936b0bb43c672fa7d9b7b94561f63e3901a2c8ba86ae2b"
BASELINE = {"commit": "11822d92070cd29360445cb4dacd8d110c655248", "tree": "81690aef257042354b6886f145919ae794e941ee"}
GROUPS = {name: "RAG/results/rag_e6_" + name + "/" for name in ("v2", "v3")}
GATE = ('if "_H2_CTX" not in globals():\n'
        '    raise RuntimeError("Historical source: use the pinned cross-experiment context; direct execution/import is disabled")\n')
FORBIDDEN = {"acquire_model.py", "bootstrap_sources.py", "freeze_run.py"}


def root_of(origin=__file__):
    return next(p for p in Path(origin).resolve().parents
                if (p / "research/shared_tools/canonical_execution_context.py").is_file())


def engine(root, group):
    if group not in GROUPS:
        raise ValueError("Unknown experiment group")
    path = Path(root) / ENGINE
    raw = path.read_bytes()
    import hashlib
    if hashlib.sha256(raw).hexdigest() != ENGINE_SHA256:
        raise ValueError("Pinned reused safety engine changed")
    spec = importlib.util.spec_from_file_location("_cross_h2_" + group, path)
    base = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), "exec"), base.__dict__)
    base.checked_path(root)
    base.VERSION, base.LEGACY = VERSION, GROUPS[group]
    base.HISTORICAL_READ_FUNCTIONS = frozenset({"verify_inputs", "verify_models", "verify_freeze", "versions"})
    return base


def gated(raw):
    """Add only an import/entry guard; preserve the remaining bytes exactly."""
    text = raw.decode("utf-8-sig")
    if GATE in text:
        return raw
    tree = ast.parse(text)
    line = 0
    for node in tree.body:
        if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)) or (
                isinstance(node, ast.ImportFrom) and node.module == "__future__"):
            line = node.end_lineno
        else:
            break
    lines = text.splitlines(keepends=True)
    lines.insert(line, GATE)
    return "".join(lines).encode("utf-8")


def ungated(raw):
    return raw.replace(GATE.encode(), b"", 1)


def derived(base, raw, logical):
    """Reuse the measured v4 IO transformer, adding CSV and local-model paths."""
    result = base.adapted_source(raw, logical)
    tree = ast.parse(result)
    lines = result.splitlines(keepends=True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line))
    edits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in ("read_csv", "from_pretrained"):
            continue
        arg = node.args[0]
        lo, hi = starts[arg.lineno-1]+arg.col_offset, starts[arg.end_lineno-1]+arg.end_col_offset
        operation = "asset_base" if node.func.attr == "from_pretrained" else "io_path"
        # from_pretrained takes str(Path); route the actual Path before str().
        if operation == "asset_base" and isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name) and arg.func.id == "str":
            arg = arg.args[0]
            lo, hi = starts[arg.lineno-1]+arg.col_offset, starts[arg.end_lineno-1]+arg.end_col_offset
        edits.append((lo, hi, ("_H2_CTX."+operation+"(").encode()+result[lo:hi]+b")"))
    for lo, hi, value in sorted(edits, reverse=True):
        result = result[:lo]+value+result[hi:]
    ast.parse(result)
    return result


def projection(base, raw):
    return base.scientific_projection(ungated(raw))


class Contract:
    def __init__(self, root, path=None, pin=CATALOG_SHA256):
        self.base = engine(root, "v2")
        self.engines = {"v2": self.base, "v3": engine(root, "v3")}
        self.root = self.base.checked_path(root)
        self.shared = self.base.shared(self.root)
        path = self.base.checked_path(path or self.root / CATALOG)
        if not path.is_relative_to(self.root):
            raise ValueError("Contract outside reviewed source root")
        raw = path.read_bytes()
        self.shared.digest(pin)
        if self.base.digest(raw) != pin:
            raise ValueError("Contract pin mismatch")
        self.pin = pin
        self.data = self.shared.strict_json(raw.decode("utf-8"))
        self.shared.keys(self.data, ("version", "baseline", "artifacts", "groups", "historical_aliases", "asset_directories", "runtime_status"))
        if self.data["version"] != VERSION or self.data["baseline"] != BASELINE or self.data["runtime_status"] != "NOT VERIFIED":
            raise ValueError("Unknown version, baseline or runtime claim")
        if self.data["historical_aliases"] != {} or self.data["asset_directories"] != ["model"] or set(self.data["groups"]) != set(GROUPS):
            raise ValueError("Unknown cross-experiment scope")
        self.artifacts = {}
        targets = set()
        for item in self.data["artifacts"]:
            self.shared.keys(item, ("historical_path", "current_path", "h1", "current_sha256", "derived_sha256", "scientific_projection", "role"))
            old = self.shared.logical_path(item["historical_path"])
            current = self.shared.logical_path(item["current_path"])
            if not any(old.startswith(x) for x in GROUPS.values()) or old in self.artifacts or current.casefold() in targets:
                raise ValueError("Duplicate/out-of-scope source")
            self.shared.keys(item["h1"], ("sha256", "git_blob", "size"))
            self.shared.digest(item["h1"]["sha256"])
            self.shared.digest(item["h1"]["git_blob"], 40)
            for key in ("current_sha256", "derived_sha256"):
                self.shared.digest(item[key])
            if item["role"] not in ("HISTORICAL_ORIGINAL", "CURRENT_ADAPTED"):
                raise ValueError("Unknown source identity role")
            self.artifacts[old] = item
            targets.add(current.casefold())
        for group, prefix in GROUPS.items():
            spec = self.data["groups"][group]
            self.shared.keys(spec, ("input_manifest", "run_config", "acquisition", "feature_count", "features"))
            if spec["feature_count"] != {"v2": 34, "v3": 36}[group] or len(spec["features"]) != spec["feature_count"] or len(set(spec["features"])) != spec["feature_count"]:
                raise ValueError("Feature schema identity mismatch")
            for field, suffix in (("input_manifest", "config/input_manifest.json"), ("run_config", "config/run_config.json"), ("acquisition", "provenance/acquisition.json")):
                if spec[field] != prefix+suffix or spec[field] not in self.artifacts:
                    raise ValueError("Missing required historical record")
            if prefix+"scripts/"+group+"_common.py" not in self.artifacts:
                raise ValueError("Missing required consumer")
        self.source_paths = frozenset(self.base.checked_path(self.root/i["current_path"]) for i in self.artifacts.values())
        self.verify_sources()
        for group in GROUPS:
            self.expected_originals(group)

    def source(self, logical):
        item = self.artifacts.get(logical)
        if item is None:
            raise ValueError("Undeclared current source")
        path = self.base.checked_path(self.root/item["current_path"])
        if self.base.digest(path.read_bytes()) != item["current_sha256"]:
            raise ValueError("Current source identity mismatch: "+logical)
        return path

    def historical_source(self, logical, original):
        item = self.artifacts.get(logical)
        if item is None:
            raise ValueError("Undeclared historical source")
        path = self.base.checked_path(Path(original)/self.shared.logical_path(logical))
        raw = path.read_bytes()
        if (self.base.digest(raw) != item["h1"]["sha256"] or self.shared.git_blob_id(raw) != item["h1"]["git_blob"] or len(raw) != item["h1"]["size"]):
            raise ValueError("Historical original identity mismatch; no current substitution")
        return path

    def verify_sources(self):
        for logical, item in self.artifacts.items():
            raw = self.source(logical).read_bytes()
            group = next(g for g, prefix in GROUPS.items() if logical.startswith(prefix))
            base = self.engines[group]
            if logical.endswith(".py"):
                adapted = derived(base, raw, logical)
                if base.digest(adapted) != item["derived_sha256"] or base.digest(projection(base, adapted).encode()) != item["scientific_projection"]:
                    raise ValueError("Derived/scientific identity mismatch")
            elif base.digest(raw) != item["derived_sha256"]:
                raise ValueError("Historical record identity mismatch")
            if item["role"] == "HISTORICAL_ORIGINAL" and (base.digest(raw) != item["h1"]["sha256"] or self.shared.git_blob_id(raw) != item["h1"]["git_blob"]):
                raise ValueError("Original record changed")
        return {"artifacts": len(self.artifacts), "status": "PASS", "runtime": "NOT VERIFIED"}

    def expected_originals(self, group):
        if group not in GROUPS:
            raise ValueError("Unknown original evidence profile")
        spec = self.data["groups"][group]
        result = {}
        def add(logical, pin):
            logical = self.shared.logical_path(logical.replace(chr(92), "/"))
            self.shared.digest(pin)
            if logical in result and result[logical] != pin:
                raise ValueError("Conflicting original identity")
            result[logical] = pin
        def record(name):
            return self.shared.strict_json(self.source(name).read_text(encoding="utf-8"))
        manifest, lock, model = (record(spec[k]) for k in ("input_manifest", "run_config", "acquisition"))
        if lock["features"] != spec["features"]:
            raise ValueError("Historical feature schema mismatch")
        tree = ast.parse(self.source(GROUPS[group]+"scripts/"+group+"_common.py").read_bytes())
        constants = {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body
                     if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
                     and n.targets[0].id in ("MODEL_ID", "REVISION")}
        if (lock["model_id"] != model["model_id"] or model["model_id"] != constants["MODEL_ID"]
                or lock["revision"] != model["revision"] or model["revision"] != constants["REVISION"]):
            raise ValueError("Historical model/revision schema mismatch")
        for name, pin in manifest["protected_sha256"].items():
            add(name, pin)
        for name, pin in lock["frozen_files"].items():
            add(GROUPS[group]+name, pin)
        for meta in model["files"].values():
            add(GROUPS[group]+meta["path"], meta["sha256"])
        if not result:
            raise ValueError("No authenticated original inputs")
        return result


def runtime(contract, group, original, run, temporary, cache, *, synthetic=False):
    """Bind one group's IO using the unchanged measured safety engine."""
    base = engine(contract.root, group)
    class Context(base.RuntimeContext):
        def __init__(self):
            checked_run = base.checked_path(run)
            if checked_run.exists():
                raise ValueError("Existing run/marker cannot be adopted")
            self.cache = base.checked_path(cache)
            temp = base.checked_path(temporary)
            if not self.cache.is_dir() or self.cache == temp or not self.cache.is_relative_to(temp):
                raise ValueError("Prepared explicit cache below temporary root required")
            base.outside_git(base.checked_path(original))
            super().__init__(contract, original, run, temporary, profile=group, synthetic=synthetic)

        def io_path(self, value, mode="r"):
            if isinstance(value, base.SourceRef):
                return super().io_path(value, mode)
            p = base.checked_path(Path(value))
            if any(c in str(mode) for c in "wax+") or self.history:
                return super().io_path(p, mode)
            old = self._legacy_of(p)
            if old is not None:
                if old.endswith(".py") or Path(old).name in ("E6_V2_PROTOCOL.md", "E6_V3_PROTOCOL.md"):
                    return contract.source(old)
                if p.exists() and p in self.created:
                    return p
                # This is an explicit original input, not a current-source fallback.
                return self.original_path(old)
            return super().io_path(p, mode)

        def prepare(self):
            super().prepare()
            for key in ("HF_HOME", "HF_HUB_CACHE", "TRANSFORMERS_CACHE", "TORCH_HOME", "XDG_CACHE_HOME"):
                os.environ[key] = str(self.cache)
            for key in ("TMP", "TMPDIR", "NUMBA_CACHE_DIR"):
                os.environ[key] = str(self.temp)
            import tempfile
            tempfile.tempdir = str(self.temp)

        def policy(self, event, args):
            if event in ("os.chmod", "os.utime", "os.chown", "os.replace"):
                for value in (args[:2] if event == "os.replace" else args[:1]):
                    if isinstance(value, int):
                        raise ValueError("Unverifiable descriptor mutation")
                    path = base.checked_path(os.fsdecode(value))
                    if not (path.is_relative_to(self.run) or path.is_relative_to(self.temp)):
                        raise ValueError("Mutation outside isolated roots")
            return super().policy(event, args)

        def load_library(self, logical):
            # Only stdlib common helpers are eligible for synthetic execution.
            if logical != GROUPS[group]+"scripts/"+group+"_common.py":
                raise ValueError("Not a side-effect-free common library")
            import types
            mod = types.ModuleType("_cross_common_"+group)
            mod.__file__ = str(contract.source(logical))
            mod.__dict__["_H2_CTX"] = self
            raw = contract.source(logical).read_bytes()
            payload = derived(base, raw, logical)
            if base.digest(payload) != contract.artifacts[logical]["derived_sha256"]:
                raise ValueError("Derived source changed before import")
            exec(compile(payload, "h2://"+VERSION+"/"+logical, "exec"), mod.__dict__)
            return mod

        def validate_entry(self, logical):
            if not logical.startswith(GROUPS[group]) or logical not in contract.artifacts or not logical.endswith(".py"):
                raise ValueError("Unknown/out-of-group entry")
            if Path(logical).name in FORBIDDEN:
                raise ValueError("Historical download/source-authoring/freeze entry is static-only")
            markers = (["evaluation/evaluation_started.json"] if Path(logical).name.startswith("evaluate")
                       else ["config/final_integrity.json"] if Path(logical).name.startswith("report") else [])
            for name in markers:
                old = GROUPS[group]+name
                marker = base.checked_path(self.original/old)
                # Omitting a completed marker from a supplied input tree cannot
                # bypass the independently authenticated public historical gate.
                public_marker = contract.source(old) if old in contract.artifacts else None
                if marker.exists() or (public_marker is not None and public_marker.is_file()):
                    raise ValueError("Historical completion/run marker exists; no replay bypass")
            return {"entry": logical, "current_path": str(contract.source(logical)), "mode": "CURRENT_ADAPTED", "runtime": "NOT VERIFIED"}

        def execute(self, logical):
            self.validate_entry(logical)
            if self.synthetic:
                raise ValueError("Synthetic contexts cannot launch experiments")
            finder = Finder(self, base, group)
            if any(name in sys.modules for name in finder.aliases):
                raise ValueError("Ambiguous project module already loaded")
            sys.addaudithook(self.policy)
            self.prepare()
            sys.meta_path.insert(0, finder)
            try:
                finder.load(logical, "__main__")
            finally:
                sys.meta_path.remove(finder)
    return Context()


class Finder:
    """Actual single-namespace import binding; no duplicated scientific module."""
    def __init__(self, context, base, group):
        self.context, self.base = context, base
        prefix = GROUPS[group]+"scripts/"
        self.aliases = {Path(old).stem: old for old in context.contract.artifacts if old.startswith(prefix) and old.endswith(".py") and Path(old).name not in FORBIDDEN}

    def find_spec(self, fullname, path=None, target=None):
        if fullname in self.aliases:
            return importlib.util.spec_from_loader(fullname, self)

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        self.load(self.aliases[module.__name__], module.__name__, module)

    def load(self, logical, name, module=None):
        if Path(logical).name in FORBIDDEN:
            raise ValueError("Historical source-authoring/download/freeze entry is static-only")
        if self.context.synthetic and not logical.endswith(("/v2_common.py", "/v3_common.py")):
            raise ValueError("Synthetic contexts cannot import scientific entries")
        import types
        module = module or types.ModuleType(name)
        source = self.context.contract.source(logical)
        module.__file__ = str(source)
        module.__dict__["_H2_CTX"] = self.context
        payload = derived(self.base, source.read_bytes(), logical)
        if self.base.digest(payload) != self.context.contract.artifacts[logical]["derived_sha256"]:
            raise ValueError("Imported current source identity mismatch")
        exec(compile(payload, "h2://"+VERSION+"/"+logical, "exec"), module.__dict__)
        return module


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--group", choices=GROUPS, required=True)
    parser.add_argument("--entry")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    if args.expected_sha256 != CATALOG_SHA256:
        raise ValueError("Unknown execution contract pin")
    contract = Contract(root_of())
    if args.entry and (args.entry not in contract.artifacts or not args.entry.startswith(GROUPS[args.group])):
        raise ValueError("Unknown/out-of-group entry")
    if not args.preflight and not args.execute:
        print(json.dumps({"version": VERSION, "sources": contract.verify_sources(), "mode": "PLAN_ONLY", "writes": 0}))
        return 0
    roots = [os.environ.get("SHROOM_CROSS_"+name) for name in ("ORIGINAL_ROOT", "RUN_ROOT", "TEMP_ROOT", "CACHE_ROOT")]
    if not all(roots):
        raise ValueError("Explicit original/run/temp/cache roots required")
    context = runtime(contract, args.group, *roots)
    if not args.entry:
        raise ValueError("Explicit entry required")
    result = context.validate_entry(args.entry)
    if args.execute:
        context.execute(args.entry)
    else:
        print(json.dumps({**result, "mode": "PREFLIGHT_ONLY", "writes": 0}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as error:
        print("Cross-experiment validation failed: "+str(error), file=sys.stderr)
        raise SystemExit(2)
