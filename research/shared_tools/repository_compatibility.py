"""Explicit historical snapshots and independently identified current views.

No training or scientific entry is launched by this CLI. Source validation and
the supported library integrations do not certify historical runtime replay.
"""
from __future__ import annotations
import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import types

VERSION = "shroom-repository-compatibility-v1"
CATALOG = "project_records/current_layout/repository_compatibility_v1.json"
CATALOG_SHA256 = "615e13463172f6898696d2c29dea271bd53fd38049250e2245de25bb6f17c092"
SHARED = "research/shared_tools/canonical_execution_context.py"
SHARED_SHA256 = "c668cce4282d6865373f50525fc78fb5a87b5be14463cc4fef3e93284b326247"
CROSS = "research/shared_tools/cross_experiment_context_v1.py"
CROSS_SHA256 = "7a4c3ce4ca1cb6a849632d63acf4ce57a2be5a1b6806567fbdd8703adb93580d"
LIBRARIES = {
    "e7": "RAG/results/rag_e7_agentic_v1/scripts/e7_common.py",
    "e8": "RAG/results/rag_e8_rf_tuning_v1/scripts/e8_common.py",
    "factcg": "RAG/results/phase3_e9_claim_verification/factcg_gpu/factcg_common.py",
    "e11_scoring": "RAG/results/phase3_e11_task_adaptation/scoring_common.py",
}
OWNERS = {
    "e7": "RAG/results/rag_e7_agentic_v1",
    "e8": "RAG/results/rag_e8_rf_tuning_v1",
    "factcg": "RAG/results/phase3_e9_claim_verification/factcg_gpu",
    "e11_scoring": "RAG/results/phase3_e11_task_adaptation",
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


NODE_AUTHOR = "RAG/results/rag_e6_v3/error_analysis/build_csv.mjs"
NODE_H1_SHA256 = "e2063e11e3fcf8fe798fe1609a647bf83c45e25488c1436f62f3bedd38b22080"
NODE_RENDER_SHA256 = "b40a38439cbedb7a98f693397153c791c0f4700aafa26b1e8503ce2c8ba7bb53"


def validate_node_counterpart(raw):
    text = raw.decode("utf-8").replace("\r\n", "\n")
    begin = "const {columns,rows}=data;"
    end = " return {csv,columns:columns.length};"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("NODE_RENDER_BOUNDARY_MISMATCH")
    fragment = text[text.index(begin):text.index(end)]
    if digest(fragment.encode()) != NODE_RENDER_SHA256:
        raise ValueError("NODE_SCIENTIFIC_RENDER_CHANGED")
    if "export const MODE='CURRENT_ADAPTED';" not in text or (
            "export const HISTORICAL_SOURCE_SHA256='"+NODE_H1_SHA256+"';") not in text:
        raise ValueError("NODE_CURRENT_IDENTITY_REQUIRED")
    if "export const ORIGINAL_INPUT_SHA256='7004fe8a1bc070d8a6508bba9f1eaa5241a7d6fbee150c9f1fb30773448bf472';" not in text:
        raise ValueError("NODE_ORIGINAL_INPUT_PIN_CHANGED")
    return True


def root_of(origin=__file__):
    return next(p for p in Path(origin).resolve().parents if (p / SHARED).is_file())


def load_pinned(root, relative, pin, name):
    path = Path(root) / relative
    raw = path.read_bytes()
    if digest(raw) != pin:
        raise ValueError("DEPENDENCY_IDENTITY_MISMATCH")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


def tree_identity(rows):
    """Recompute the Git tree identity without Git subprocesses or metadata."""
    root = {}
    for row in rows:
        cursor = root
        parts = row["path"].split("/")
        for name in parts[:-1]:
            cursor = cursor.setdefault(name, {})
            if not isinstance(cursor, dict):
                raise ValueError("INVALID_TREE_PREFIX")
        if parts[-1] in cursor:
            raise ValueError("DUPLICATE_TREE_PATH")
        cursor[parts[-1]] = (row["mode"], row["git_blob"])
    def encode(node):
        data = b""
        for name in sorted(node, key=lambda n: (n + "/" if isinstance(node[n], dict) else n).encode()):
            item = node[name]
            mode, oid = ("40000", encode(item)) if isinstance(item, dict) else item
            data += mode.encode() + b" " + name.encode() + b"\0" + bytes.fromhex(oid)
        return hashlib.sha1(b"tree " + str(len(data)).encode() + b"\0" + data).hexdigest()
    return encode(root)


def counterpart(raw):
    """Current local library view: only roots and IO routing are changed.

    AccessGuard class bodies are deliberately not traversed or rewritten.
    Original files remain immutable; the returned bytes have their own identity.
    """
    original_tree = ast.parse(raw)
    module_assignments = {id(n) for n in original_tree.body if isinstance(n, ast.Assign)}
    class Adapt(ast.NodeTransformer):
        def visit_ClassDef(self, node):
            return node if node.name == "AccessGuard" else self.generic_visit(node)
        def visit_Assign(self, node):
            if (id(node) in module_assignments and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id in {"ROOT", "HERE", "OUT"}):
                node.value = ast.Call(ast.Attribute(ast.Name("_REPO_CTX", ast.Load()), "binding", ast.Load()), [ast.Constant(node.targets[0].id)], [])
                return node
            return self.generic_visit(node)
        def visit_Call(self, node):
            node = self.generic_visit(node)
            if isinstance(node.func, ast.Attribute) and node.func.attr in ("open", "read_text", "read_bytes"):
                mode = node.args[0] if node.func.attr == "open" and node.args else ast.Constant("r")
                for kw in node.keywords:
                    if kw.arg == "mode": mode = kw.value
                purpose = ast.Constant("configuration" if node.func.attr == "read_text" else "original")
                node.func.value = ast.Call(ast.Attribute(ast.Name("_REPO_CTX", ast.Load()), "io_path", ast.Load()), [node.func.value, mode, purpose], [])
            elif isinstance(node.func, ast.Name) and node.func.id == "open" and node.args:
                mode = node.args[1] if len(node.args) > 1 else ast.Constant("r")
                node.args[0] = ast.Call(ast.Attribute(ast.Name("_REPO_CTX", ast.Load()), "io_path", ast.Load()), [node.args[0], mode], [])
            return node
    tree = Adapt().visit(original_tree)
    return (ast.unparse(ast.fix_missing_locations(tree)) + "\n").encode()


def scientific_projection(raw):
    original_tree = ast.parse(raw)
    module_assignments = {id(n) for n in original_tree.body if isinstance(n, ast.Assign)}
    class Project(ast.NodeTransformer):
        def visit_ClassDef(self, node):
            return node if node.name == "AccessGuard" else self.generic_visit(node)
        def visit_Assign(self, node):
            if (id(node) in module_assignments and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id in {"ROOT", "HERE", "OUT"}):
                node.value = ast.Constant("DECLARED_LOCAL_ROOT")
                return node
            return self.generic_visit(node)
        def visit_Call(self, node):
            if ast.unparse(node.func) == "_REPO_CTX.io_path":
                return self.visit(node.args[0])
            return self.generic_visit(node)
    return ast.dump(Project().visit(original_tree), include_attributes=False)


class Catalog:
    def __init__(self, root, *, pin=CATALOG_SHA256, path=None, verify_current=True):
        self.root = Path(root)
        self.shared = load_pinned(self.root, SHARED, SHARED_SHA256, "_repo_compat_shared")
        self.root = self.shared.reject_links(self.root)
        path = self.shared.reject_links(Path(path) if path else self.root / CATALOG)
        if not self.root.is_absolute() or not path.is_relative_to(self.root):
            raise ValueError("INVALID_SOURCE_ROOT")
        raw = path.read_bytes()
        self.shared.digest(pin)
        if digest(raw) != pin:
            raise ValueError("CATALOG_PIN_MISMATCH")
        self.pin = pin
        self.data = self.shared.strict_json(raw.decode())
        self.shared.keys(self.data, ("version", "snapshots", "artifacts", "libraries", "cross_contract", "runtime_status"))
        if self.data["version"] != VERSION or self.data["runtime_status"] != "NOT VERIFIED":
            raise ValueError("UNKNOWN_COMPATIBILITY_VERSION")
        self.entries = {}
        destinations = set()
        for row in self.data["artifacts"]:
            self.shared.keys(row, ("original", "current", "h1_sha256", "h1_blob", "sha256", "bytes", "status"))
            old = self.shared.logical_path(row["original"])
            current = self.shared.logical_path(row["current"])
            for key in ("h1_sha256", "sha256"): self.shared.digest(row[key])
            self.shared.digest(row["h1_blob"], 40)
            if old in self.entries or current.casefold() in destinations:
                raise ValueError("DUPLICATE_SOURCE_MAPPING")
            self.entries[old] = row
            destinations.add(current.casefold())
        if len(self.entries) != 790:
            raise ValueError("INCOMPLETE_ORIGINAL_MIGRATION_SCOPE")
        for name, snapshot in self.data["snapshots"].items():
            self.shared.keys(snapshot, ("commit", "tree", "files"))
            self.shared.digest(snapshot["commit"], 40); self.shared.digest(snapshot["tree"], 40)
            for row in snapshot["files"]:
                self.shared.logical_path(row["path"])
                self.shared.digest(row["sha256"]); self.shared.digest(row["git_blob"], 40)
                if row["mode"] not in ("100644", "100755"):
                    raise ValueError("UNSUPPORTED_SNAPSHOT_FILE_MODE")
            if tree_identity(snapshot["files"]) != snapshot["tree"]:
                raise ValueError("SNAPSHOT_TREE_IDENTITY_MISMATCH")
        h1 = self.data["snapshots"]["H1"]
        if h1["commit"] != "11822d92070cd29360445cb4dacd8d110c655248" or h1["tree"] != "81690aef257042354b6886f145919ae794e941ee":
            raise ValueError("UNKNOWN_HISTORICAL_REVISION")
        originals = {x["path"]: x for x in h1["files"]}
        for old, row in self.entries.items():
            if old not in originals or originals[old]["sha256"] != row["h1_sha256"] or originals[old]["git_blob"] != row["h1_blob"]:
                raise ValueError("ORIGINAL_NOT_BOUND_TO_IMMUTABLE_GIT_TREE")
        if set(self.data["libraries"]) != set(LIBRARIES):
            raise ValueError("UNKNOWN_CURRENT_LIBRARY_SCOPE")
        if verify_current:
            self.verify_current()

    def current(self, old):
        if old not in self.entries:
            raise ValueError("UNDECLARED_CURRENT_SOURCE")
        row = self.entries[old]
        path = self.shared.reject_links(self.root / row["current"])
        raw = path.read_bytes()
        if len(raw) != row["bytes"] or digest(raw) != row["sha256"]:
            raise ValueError("CURRENT_SOURCE_IDENTITY_MISMATCH")
        return path

    def verify_current(self):
        for old in self.entries: self.current(old)
        for profile, source in LIBRARIES.items():
            spec = self.data["libraries"][profile]
            self.shared.keys(spec, ("derived_sha256", "scientific_projection", "original_requirements", "configuration_views"))
            for name, pin in spec["original_requirements"].items():
                self.shared.logical_path(name); self.shared.digest(pin)
            for name in spec["configuration_views"]:
                if name not in self.entries: raise ValueError("UNKNOWN_CURRENT_CONFIGURATION")
            raw = self.current(source).read_bytes()
            view = counterpart(raw)
            if digest(view) != spec["derived_sha256"] or digest(scientific_projection(view).encode()) != spec["scientific_projection"] or scientific_projection(raw) != scientific_projection(view):
                raise ValueError("CURRENT_LIBRARY_SCIENTIFIC_IDENTITY_MISMATCH")
            original = ast.parse(raw)
            adapted = ast.parse(view)
            guards = lambda tree: [ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "AccessGuard"]
            if guards(original) != guards(adapted):
                raise ValueError("ACCESS_GUARD_CHANGED")
        return {"status": "PASS", "sources": len(self.entries), "runtime": "NOT VERIFIED"}

    def snapshot(self, name, root):
        if name not in self.data["snapshots"]: raise ValueError("UNKNOWN_HISTORICAL_MODE")
        return Snapshot(self, name, root)

    def cross(self):
        """Compose the unchanged cross API with explicitly current master bindings."""
        api = load_pinned(self.root, CROSS, CROSS_SHA256, "_repo_compat_cross")
        api.VERSION = VERSION + "::E6_CURRENT"
        source = self.data["cross_contract"]
        raw = (self.root/source["path"]).read_bytes()
        if digest(raw) != source["sha256"]: raise ValueError("HISTORICAL_CROSS_CONTRACT_CHANGED")
        value = self.shared.strict_json(raw.decode())
        class Bound(api.Contract):
            def __init__(bound):
                bound.root, bound.shared, bound.pin = self.root, self.shared, self.pin
                bound.base = api.engine(self.root, "v2")
                bound.engines = {"v2": bound.base, "v3": api.engine(self.root, "v3")}
                bound.data = copy.deepcopy(value)
                bound.data["version"] = api.VERSION
                bound.artifacts = {}
                for item in bound.data["artifacts"]:
                    old = item["historical_path"]
                    current = self.entries[old]
                    if current["sha256"] != item["current_sha256"]:
                        # A single reviewed non-Python IO-envelope adaptation.
                        # The original contract/h1 identities are never updated.
                        if old != NODE_AUTHOR or item["h1"]["sha256"] != NODE_H1_SHA256:
                            raise ValueError("CROSS_SCIENTIFIC_SOURCE_CHANGED")
                        validate_node_counterpart(self.current(old).read_bytes())
                        item["current_sha256"] = current["sha256"]
                        item["derived_sha256"] = current["sha256"]
                        item["role"] = "CURRENT_ADAPTED"
                    item["current_path"] = current["current"]
                    bound.artifacts[old] = item
                bound.source_paths = frozenset(self.root/i["current_path"] for i in bound.artifacts.values())
                bound.verify_sources()
                for group in api.GROUPS: bound.expected_originals(group)
        return api, Bound()


    def checksum_evidence(self, logical, *, historical):
        """Read authenticated PUBLIC-H1 checksum evidence, never an H0 replay.

        The exact raw lists are current-location artifacts, not active validators.
        Required private ledgers and original inputs are not manufactured here.
        Failed original checks remain explicit failures, with no current fallback.
        """
        allowed = {
            "RAG/results/phase3_e11_task_adaptation/e11d_training/SHA256SUMS.txt":
                "e340ee9154880d7191fa373bb3e69a453f0b3f7f4007bca5a99b54a3201ba027",
            "RAG/results/phase3_e11_task_adaptation/e11e_training/SHA256SUMS.txt":
                "8bbafb4bc099625c87469a0cab97bf5ec2bbd21ca2ec2a101e26ff42105b1a75",
        }
        if logical not in allowed:
            raise ValueError("UNDECLARED_CHECKSUM_EVIDENCE")
        if not isinstance(historical, Snapshot) or historical.catalog is not self or historical.name != "H1":
            raise ValueError("EXPLICIT_AUTHENTICATED_H1_CONTEXT_REQUIRED")
        raw = self.current(logical).read_bytes()
        original = historical.source(logical).read_bytes()
        if digest(raw) != allowed[logical] or raw != original:
            raise ValueError("CHECKSUM_SOURCE_NOT_BYTE_IDENTICAL")
        rows = []
        names = set()
        for line in raw.decode("utf-8").splitlines():
            expected, name = line.split(None, 1)
            self.shared.digest(expected)
            name = self.shared.logical_path(name.strip())
            if name in names:
                raise ValueError("DUPLICATE_CHECKSUM_ENTRY")
            names.add(name)
            target = logical.rsplit("/", 1)[0] + "/" + name
            # Never use a relocated/sanitized file as a missing H0 original.
            path = historical.source(target)
            actual = digest(path.read_bytes())
            rows.append({"historical_target": target, "expected_h0_sha256": expected,
                         "observed_public_h1_sha256": actual,
                         "status": "PASS" if actual == expected else "FAIL"})
        if not rows:
            raise ValueError("EMPTY_CHECKSUM_EVIDENCE")
        return {"mode": "CURRENT_EVIDENCE_FROM_AUTHENTICATED_H1",
                "source_identity": "PASS", "current_path": self.entries[logical]["current"],
                "historical_path": logical, "record_sha256": allowed[logical],
                "historical_input_checks": "FAIL" if any(x["status"] != "PASS" for x in rows) else "PASS",
                "checks": rows, "required_private_preservation_ledger": "NOT PROVIDED",
                "runtime": "NOT VERIFIED", "scientific_execution": False}


class Snapshot:
    def __init__(self, catalog, name, root):
        self.catalog, self.name = catalog, name
        self.root = catalog.shared.reject_links(Path(root))
        if not self.root.is_absolute() or not self.root.is_dir() or self.root.is_relative_to(catalog.root):
            raise ValueError("EXPLICIT_EXTERNAL_SNAPSHOT_REQUIRED")
        self.spec = catalog.data["snapshots"][name]
        self.files = {x["path"]: x for x in self.spec["files"]}
        actual = set()
        for path in self.root.rglob("*"):
            catalog.shared.reject_links(path)
            if path.is_file(): actual.add(path.relative_to(self.root).as_posix())
        if actual != set(self.files): raise ValueError("SNAPSHOT_FILE_SET_MISMATCH")
        for path in self.files: self.source(path)

    def source(self, logical):
        logical = self.catalog.shared.logical_path(logical)
        if logical not in self.files: raise ValueError("UNDECLARED_HISTORICAL_SOURCE")
        path = self.catalog.shared.reject_links(self.root/logical)
        raw = path.read_bytes(); row = self.files[logical]
        if digest(raw) != row["sha256"] or self.catalog.shared.git_blob_id(raw) != row["git_blob"] or len(raw) != row["bytes"]:
            raise ValueError("HISTORICAL_SOURCE_IDENTITY_MISMATCH")
        if path.stat().st_mode & stat.S_IWRITE: raise ValueError("SNAPSHOT_NOT_READ_ONLY")
        return path

    def check_original_requirement(self, logical, expected):
        self.catalog.shared.digest(expected)
        path = self.source(logical)
        if digest(path.read_bytes()) != expected:
            raise ValueError("H1_IS_NOT_REQUIRED_H0_ORIGINAL")
        return path


class CurrentLibrary:
    """Current local counterpart with separately authenticated original inputs.

    fixture=True is library-only testing: it cannot launch a scientific entry or
    certify production original-input coverage. CLI construction never sets it.
    """
    def __init__(self, catalog, profile, original, run, cache, temporary, *, fixture=False, fixture_requirements=None):
        if profile not in LIBRARIES: raise ValueError("UNKNOWN_LIBRARY_PROFILE")
        self.catalog, self.profile = catalog, profile
        self.api = load_pinned(catalog.root, CROSS, CROSS_SHA256, "_repo_compat_path_tools")
        self.base = self.api.engine(catalog.root, "v2")
        self.original, self.run, self.cache, self.temp = map(self.base.checked_path, (original, run, cache, temporary))
        if not self.original.is_dir() or self.run.exists() or not self.run.parent.is_dir():
            raise ValueError("INVALID_INPUT_OR_EXISTING_RUN")
        for p in (self.run, self.cache, self.temp): self.base.outside_git(p)
        if self.base.overlap(self.run, self.original) or self.base.overlap(self.run, catalog.root):
            raise ValueError("WRITABLE_READONLY_ROOT_OVERLAP")
        if self.cache == self.temp or not self.cache.is_relative_to(self.run) or not self.temp.is_relative_to(self.run) or self.base.overlap(self.cache, self.temp):
            raise ValueError("EXPLICIT_DISJOINT_CACHE_TEMP_CHILDREN_REQUIRED")
        self.fixture = fixture
        self.created = set()
        self.owner = OWNERS[profile]
        spec = catalog.data["libraries"][profile]
        if fixture:
            if fixture_requirements is None: raise ValueError("EXPLICIT_TOY_REQUIREMENTS_REQUIRED")
            self.expected = dict(fixture_requirements)
            self.views = set()
        else:
            self.expected = dict(spec["original_requirements"])
            self.views = set(spec["configuration_views"])
        for old, pin in self.expected.items():
            catalog.shared.logical_path(old); catalog.shared.digest(pin)
            path = self.base.checked_path(self.original/old)
            if not path.is_file() or digest(path.read_bytes()) != pin:
                raise ValueError("ORIGINAL_INPUT_MISSING_OR_WRONG")
        self.ready = False

    def binding(self, name):
        if name == "ROOT": return self.original
        if name in ("HERE", "OUT"): return self.run
        raise ValueError("UNKNOWN_ROOT_BINDING")

    def io_path(self, value, mode="r", purpose="original"):
        p = self.base.checked_path(Path(value))
        writing = any(x in str(mode) for x in "wax+")
        if writing:
            if not p.is_relative_to(self.run): raise ValueError("WRITE_OUTSIDE_OWNED_RUN")
            if p.exists() and not ("a" in str(mode) and p in self.created):
                raise ValueError("OUTPUT_OVERWRITE_OR_ADOPTION_REJECTED")
            self.created.add(p)
            return p
        if p.is_relative_to(self.run):
            if p.is_file() and p in self.created: return p
            logical = self.owner+"/"+p.relative_to(self.run).as_posix()
            p = self.base.checked_path(self.original/logical)
        elif p.is_relative_to(self.original): logical = p.relative_to(self.original).as_posix()
        else: raise ValueError("UNDECLARED_READ_DOMAIN")
        if purpose == "configuration" and logical in self.views:
            return self.catalog.current(logical)
        if logical not in self.expected or not p.is_file() or digest(p.read_bytes()) != self.expected[logical]:
            raise ValueError("ORIGINAL_READ_NOT_AUTHENTICATED")
        return p

    def prepare(self):
        if self.ready: return
        # Revalidate before the first write; do not rely on an earlier preflight.
        self.catalog.current(LIBRARIES[self.profile])
        for p, pin in self.expected.items():
            if digest(self.base.checked_path(self.original/p).read_bytes()) != pin: raise ValueError("INPUT_CHANGED_BEFORE_PREPARE")
        sys.dont_write_bytecode = True
        if not self.fixture:
            sys.addaudithook(self.policy)
        self.run.mkdir(exist_ok=False)
        for p in (self.run/"config", self.cache, self.temp): p.mkdir(parents=True, exist_ok=False)
        marker = self.run/"CURRENT_RUN_IDENTITY.json"
        marker.write_text(json.dumps({"version": VERSION, "catalog": self.catalog.pin, "profile": self.profile, "mode": "CURRENT", "fixture_only": self.fixture, "runtime": "NOT VERIFIED"}), encoding="utf-8")
        self.created.add(marker)
        for key in ("TEMP", "TMP", "TMPDIR", "JOBLIB_TEMP_FOLDER", "NUMBA_CACHE_DIR"): os.environ[key] = str(self.temp)
        for key in ("HF_HOME", "HF_HUB_CACHE", "TRANSFORMERS_CACHE", "TORCH_HOME", "XDG_CACHE_HOME", "MPLCONFIGDIR"): os.environ[key] = str(self.cache)
        for key in ("PYTHONDONTWRITEBYTECODE", "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE"): os.environ[key] = "1"
        import tempfile
        tempfile.tempdir = str(self.temp)
        self.ready = True

    def load(self):
        if not self.ready: raise ValueError("CONTEXT_NOT_PREPARED")
        old = LIBRARIES[self.profile]
        path = self.catalog.current(old)
        raw = counterpart(path.read_bytes())
        if digest(raw) != self.catalog.data["libraries"][self.profile]["derived_sha256"]:
            raise ValueError("DERIVED_SOURCE_CHANGED")
        module = types.ModuleType("_current_"+self.profile)
        module.__file__ = str(path)
        module.__dict__["_REPO_CTX"] = self
        exec(compile(raw, "current://"+VERSION+"/"+old, "exec"), module.__dict__)
        return module

    def policy(self, event, args):
        if event.startswith("socket.") or event in ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn"):
            raise ValueError("NETWORK_OR_CHILD_PROCESS_FORBIDDEN")
        if event == "open" and not isinstance(args[0], int):
            mode, flags = args[1:3]
            if (isinstance(mode, str) and any(x in mode for x in "wax+")) or (isinstance(flags, int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):
                self.io_path(os.fsdecode(args[0]), "a" if isinstance(flags, int) and flags & os.O_APPEND else "w")
        if event in ("os.mkdir", "os.remove", "os.rmdir", "os.rename", "os.chmod", "os.utime", "os.truncate", "os.link", "os.symlink"):
            if event in ("os.link", "os.symlink"): raise ValueError("LINK_CREATION_FORBIDDEN")
            for value in (args[:2] if event == "os.rename" else args[:1]):
                if isinstance(value, int) or not self.base.checked_path(os.fsdecode(value)).is_relative_to(self.run):
                    raise ValueError("MUTATION_OUTSIDE_OWNED_RUN")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--mode", choices=("HISTORICAL", "CURRENT"), required=True)
    parser.add_argument("--snapshot-root", type=Path)
    parser.add_argument("--snapshot", choices=("H1", "P26"), default="H1")
    args = parser.parse_args(argv)
    if args.expected_sha256 != CATALOG_SHA256: raise ValueError("UNKNOWN_CATALOG_PIN")
    catalog = Catalog(root_of(), verify_current=args.mode == "CURRENT")
    if args.mode == "HISTORICAL":
        if args.snapshot_root is None: raise ValueError("EXPLICIT_SNAPSHOT_REQUIRED")
        view = catalog.snapshot(args.snapshot, args.snapshot_root)
        result = {"mode": "HISTORICAL", "snapshot_role": "H1_PUBLIC_ORIGINAL" if args.snapshot == "H1" else "P26_PRIOR_CURRENT_CONTEXT",
                  "commit": view.spec["commit"], "files": len(view.files), "source_identity": "PASS", "H0_runtime_compatibility": "NOT VERIFIED"}
    else:
        result = {"mode": "CURRENT", **catalog.verify_current(), "H0_runtime_compatibility": "NOT VERIFIED"}
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as error:
        print("Compatibility validation failed: "+str(error), file=sys.stderr)
        raise SystemExit(2)
