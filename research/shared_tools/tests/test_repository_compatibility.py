"""Offline source-mode and actual library/AccessGuard tests.

Toy inputs are confined to scratch and never stand in for production originals.
Historical snapshots are inspected read-only; no scientific entry is launched.
"""
import ast
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import uuid

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "research/shared_tools/canonical_execution_context.py").is_file())
spec = importlib.util.spec_from_file_location("_compat_test_api", ROOT / "research/shared_tools/repository_compatibility.py")
API = importlib.util.module_from_spec(spec)
spec.loader.exec_module(API)
_catalog = None
_snapshots = {}
_active = [None]


def audit(event, args):
    if _active[0] is not None:
        _active[0].policy(event, args)


sys.addaudithook(audit)


def catalog():
    global _catalog
    if _catalog is None: _catalog = API.Catalog(ROOT)
    return _catalog


def snapshot(name="H1"):
    if name not in _snapshots:
        _snapshots[name] = catalog().snapshot(name, Path(os.environ["SHROOM_SNAPSHOT_"+name]))
    return _snapshots[name]


def digest(raw): return hashlib.sha256(raw).hexdigest()


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.c = catalog()
        self.work = Path(os.environ["SHROOM_TEST_SCRATCH"]) / ("identity_"+uuid.uuid4().hex)
        self.work.mkdir()

    def mutation(self, fn):
        value = copy.deepcopy(self.c.data)
        fn(value)
        raw = json.dumps(value).encode()
        path = ROOT / API.CATALOG
        original = Path.read_bytes
        with patch.object(Path, "read_bytes", lambda p: raw if p == path else original(p)):
            with self.assertRaises((ValueError, KeyError, OSError)):
                API.Catalog(ROOT, pin=digest(raw))

    def test_all_790_current_source_identities(self):
        self.assertEqual(self.c.verify_current()["sources"], 790)

    def test_unknown_version(self): self.mutation(lambda d: d.update(version="unknown"))

    def test_missing_current_source(self):
        self.mutation(lambda d: d["artifacts"][0].update(current="research/no_such_source.py"))

    def test_wrong_current_hash(self):
        self.mutation(lambda d: d["artifacts"][0].update(sha256="0"*64))

    def test_wrong_original_hash(self):
        self.mutation(lambda d: d["artifacts"][0].update(h1_sha256="0"*64))

    def test_wrong_original_blob(self):
        self.mutation(lambda d: d["artifacts"][0].update(h1_blob="0"*40))

    def test_duplicate_mapping(self):
        self.mutation(lambda d: d["artifacts"][1].update(current=d["artifacts"][0]["current"]))

    def test_traversal(self):
        self.mutation(lambda d: d["artifacts"][0].update(current="../private/source.py"))

    def test_wrong_snapshot_tree(self):
        self.mutation(lambda d: d["snapshots"]["H1"].update(tree="0"*40))

    def test_wrong_snapshot_blob(self):
        self.mutation(lambda d: d["snapshots"]["H1"]["files"][0].update(git_blob="0"*40))

    def test_wrong_library_counterpart(self):
        self.mutation(lambda d: d["libraries"]["factcg"].update(derived_sha256="0"*64))

    def test_wrong_scientific_projection(self):
        self.mutation(lambda d: d["libraries"]["e7"].update(scientific_projection="0"*64))

    def test_unknown_current_logical_source(self):
        with self.assertRaises(ValueError): self.c.current("not/registered.py")

    def test_historical_tree_recomputed(self):
        for name, spec in self.c.data["snapshots"].items():
            self.assertEqual(API.tree_identity(spec["files"]), spec["tree"], name)

    def test_h1_snapshot_exact_944_files(self): self.assertEqual(len(snapshot().files), 944)

    def test_previous_context_snapshot_exact_971_files(self): self.assertEqual(len(snapshot("P26").files), 971)

    def test_snapshot_old_paths_are_real_original_files(self):
        name = API.LIBRARIES["e7"]
        self.assertEqual(snapshot().source(name).read_bytes(), self.c.current(name).read_bytes())

    def test_missing_historical_source_no_current_fallback(self):
        with self.assertRaises(ValueError): snapshot().source("not/registered.py")

    def test_h1_is_not_automatically_h0(self):
        rows = {x["path"]: x for x in snapshot().spec["files"]}
        candidates = [(p, pin) for spec in self.c.data["libraries"].values() for p, pin in spec["original_requirements"].items()
                      if p in rows and rows[p]["sha256"] != pin]
        self.assertTrue(candidates)
        old, pin = candidates[0]
        with self.assertRaises(ValueError): snapshot().check_original_requirement(old, pin)

    def test_wrong_historical_source_rejected_without_writes(self):
        view = snapshot(); path = view.source(API.LIBRARIES["e7"])
        original = Path.read_bytes
        with patch.object(Path, "read_bytes", lambda p: b"changed" if p == path else original(p)):
            with self.assertRaises(ValueError): view.source(API.LIBRARIES["e7"])

    def test_current_corruption_does_not_change_historical_mode(self):
        old = API.LIBRARIES["e7"]; current = self.c.current(old)
        original = Path.read_bytes
        with patch.object(Path, "read_bytes", lambda p: b"changed" if p == current else original(p)):
            with self.assertRaises(ValueError): self.c.current(old)
            historical_catalog = API.Catalog(ROOT, verify_current=False)
            self.assertEqual(historical_catalog.data["snapshots"]["H1"]["tree"], snapshot().spec["tree"])

    def test_snapshot_never_becomes_current_execution_root(self):
        with self.assertRaises(ValueError): self.c.snapshot("H1", ROOT)

    def test_invalid_snapshot_file_set(self):
        with self.assertRaises(ValueError): self.c.snapshot("H1", self.work)

    def test_unknown_snapshot(self):
        with self.assertRaises(ValueError): self.c.snapshot("unknown", self.work)

    def test_exact_accessguard_ast_preserved(self):
        for name in ("e7", "e8"):
            raw = self.c.current(API.LIBRARIES[name]).read_bytes()
            a = next(n for n in ast.parse(raw).body if isinstance(n, ast.ClassDef) and n.name == "AccessGuard")
            b = next(n for n in ast.parse(API.counterpart(raw)).body if isinstance(n, ast.ClassDef) and n.name == "AccessGuard")
            self.assertEqual(ast.dump(a, include_attributes=False), ast.dump(b, include_attributes=False))

    def test_cross_binding_uses_current_master_paths(self):
        api, bound = self.c.cross()
        self.assertEqual(len(bound.artifacts), 53)
        for old, item in bound.artifacts.items():
            self.assertEqual(bound.source(old), self.c.current(old))
        self.assertNotEqual(api.VERSION, "shroom-e6-cross-experiment-h2-v1")

    def test_original_cross_contract_never_rewritten(self):
        spec = self.c.data["cross_contract"]
        self.assertEqual(digest((ROOT/spec["path"]).read_bytes()), spec["sha256"])

    def test_unknown_cli_pin_before_loading(self):
        with patch.object(API, "Catalog", side_effect=AssertionError("must not load")):
            with self.assertRaises(ValueError): API.main(["--expected-sha256", "0"*64, "--mode", "CURRENT"])


class LibraryCases:
    def setUp(self):
        self.c = catalog()
        self.work = Path(os.environ["SHROOM_TEST_SCRATCH"]) / (self.PROFILE+"_"+uuid.uuid4().hex)
        self.work.mkdir()
        self.original = self.work/"original"; self.original.mkdir()
        self.run = self.work/"run"
        self.cache, self.temp = self.run/"cache", self.run/"temporary"
        self.expected = {}
        self.owner = API.OWNERS[self.PROFILE]

    def put(self, logical, raw):
        path = self.original/logical
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        self.expected[logical] = digest(raw)
        return path

    def context(self, **kw):
        args = dict(catalog=self.c, profile=self.PROFILE, original=self.original, run=self.run,
                    cache=self.cache, temporary=self.temp, fixture=True, fixture_requirements=self.expected)
        args.update(kw)
        return API.CurrentLibrary(**args)

    def loaded(self):
        ctx = self.context()
        ctx.prepare()
        return ctx, ctx.load()

    def test_source_preflight_has_no_writes(self):
        ctx = self.context()
        self.assertFalse(self.run.exists())
        self.assertFalse(ctx.ready)

    def test_real_missing_originals_fail_before_run(self):
        with self.assertRaises(ValueError): self.context(fixture=False)
        self.assertFalse(self.run.exists())

    def test_existing_run_or_marker_rejected(self):
        self.run.mkdir()
        (self.run/"CURRENT_RUN_IDENTITY.json").write_text("existing")
        with self.assertRaises(ValueError): self.context()

    def test_git_output_rejected(self):
        with self.assertRaises(ValueError):
            self.context(run=ROOT/"must_not_be_created", cache=ROOT/"must_not_be_created/cache", temporary=ROOT/"must_not_be_created/tmp")

    def test_readonly_output_overlap_rejected(self):
        with self.assertRaises(ValueError): self.context(run=self.original/"run")

    def test_cache_outside_owned_run_rejected(self):
        with self.assertRaises(ValueError): self.context(cache=self.work/"cache")

    def test_temp_cache_overlap_rejected(self):
        with self.assertRaises(ValueError): self.context(temporary=self.cache)

    def test_relative_run_rejected(self):
        with self.assertRaises(ValueError): self.context(run=Path("relative"))

    def test_load_without_preparation_rejected(self):
        with self.assertRaises(ValueError): self.context().load()

    def test_missing_input_identity_rejected(self):
        self.expected["toy/missing.txt"] = "0"*64
        with self.assertRaises(ValueError): self.context()
        self.assertFalse(self.run.exists())

    def test_wrong_input_identity_rejected(self):
        path = self.put("toy/input.txt", b"toy")
        path.write_bytes(b"changed")
        with self.assertRaises(ValueError): self.context()

    def test_input_revalidated_before_first_write(self):
        path = self.put("toy/input.txt", b"toy")
        ctx = self.context(); path.write_bytes(b"changed")
        with self.assertRaises(ValueError): ctx.prepare()
        self.assertFalse(self.run.exists())

    def test_prepared_roots_and_no_model_imports(self):
        before = set(sys.modules)
        ctx, module = self.loaded()
        self.assertEqual(module.ROOT, self.original)
        self.assertTrue(self.cache.is_dir() and self.temp.is_dir())
        self.assertFalse({"torch", "transformers", "modal", "vertexai", "numpy", "pandas"} & (set(sys.modules)-before))

    def test_network_and_process_policy_rejected(self):
        ctx = self.context()
        for event,args in [("socket.connect",()),("subprocess.Popen",("python",["python"],None,{}))]:
            with self.assertRaises(ValueError): ctx.policy(event,args)

    def test_snapshot_or_input_mutation_rejected(self):
        ctx = self.context()
        for path in (self.original/"outside.txt", snapshot().root/"outside.txt"):
            with self.assertRaises(ValueError): ctx.policy("open",(str(path),"w",os.O_WRONLY))

    def test_undeclared_original_never_uses_current_file(self):
        ctx = self.context()
        with self.assertRaises(ValueError): ctx.io_path(self.run/"undeclared.py")


class GuardCases(LibraryCases):
    def fixtures(self):
        self.put("toy/allowed.csv",b"id,value\nSYNTHETIC,1\n")
        self.put(self.owner+"/"+self.PROFILE.upper()+"_PROTOCOL.md",b"toy protocol")
        self.put("RAG/results/rag_e6_v1/toy.csv",b"toy baseline")
        freeze={"protected_sha256":{"toy/allowed.csv":self.expected["toy/allowed.csv"]},
                "protocol_sha256":self.expected[self.owner+"/"+self.PROFILE.upper()+"_PROTOCOL.md"]}
        self.put(self.owner+"/config/protocol_freeze.json",json.dumps(freeze).encode())
        self.put("RAG/results/rag_e6_v1/config/completion_manifest.json",json.dumps({"files":{"toy.csv":self.expected["RAG/results/rag_e6_v1/toy.csv"]}}).encode())

    def test_actual_verify_integrity_body(self):
        self.fixtures();ctx,module=self.loaded()
        self.assertEqual(len(module.verify_integrity()["protected_sha256"]),1)

    def test_actual_guard_allowlisted_read(self):
        self.fixtures();ctx,module=self.loaded();guard=module.AccessGuard("toy")
        guard.policy("open",(str(self.original/"toy/allowed.csv"),"r",0))

    def test_actual_guard_unlisted_read_rejected(self):
        self.fixtures();ctx,module=self.loaded();guard=module.AccessGuard("toy")
        with self.assertRaises(PermissionError):guard.policy("open",(str(self.original/"toy/unlisted.csv"),"r",0))

    def test_actual_guard_outside_write_rejected(self):
        self.fixtures();ctx,module=self.loaded();guard=module.AccessGuard("toy")
        with self.assertRaises(PermissionError):guard.policy("open",(str(self.original/"toy/no.txt"),"w",os.O_WRONLY))

    def test_actual_guard_network_rejected(self):
        self.fixtures();ctx,module=self.loaded();guard=module.AccessGuard("toy")
        with self.assertRaises(PermissionError):guard.policy("socket.connect",())

    def test_actual_writer_exclusive_and_isolated(self):
        self.fixtures();ctx,module=self.loaded()
        path=self.run/"toy/result.json"
        _active[0]=ctx
        try:
            module.write_json(path,{"toy":True})
            with self.assertRaises((ValueError,FileExistsError)):module.write_json(path,{"toy":False})
            with self.assertRaises(ValueError):module.write_json(self.original/"escaped/result.json",{})
        finally:_active[0]=None
        self.assertEqual(json.loads(path.read_text()),{"toy":True})
        self.assertFalse((self.original/"escaped").exists())


class E7Tests(GuardCases,unittest.TestCase): PROFILE="e7"
class E8Tests(GuardCases,unittest.TestCase): PROFILE="e8"


class FactCGTests(LibraryCases,unittest.TestCase):
    PROFILE="factcg"

    def fixtures(self):
        ctx,module=self.loaded()
        rows=[{"canonical_id":"SYNTHETIC_"+str(i),"task":"DM","whole_hypothesis":"toy hypothesis","reference_text":"toy reference"} for i in range(561)]
        raw=("\n".join(json.dumps(x) for x in rows)+"\n").encode()
        inputs=self.put(self.owner+"/factcg_inputs.jsonl",raw)
        manifest={"model_id":module.MODEL,"model_revision":module.REVISION,"source_commit":module.SOURCE_COMMIT,
                  "settings":module.SETTINGS,"reference_policy":module.POLICY,"sample_count":561,"feature_count":37,
                  "package_sha256":{"factcg_inputs.jsonl":digest(raw)},"input_content_sha256":module.digest(rows)}
        self.put(self.owner+"/GPU_RUN_MANIFEST.json",json.dumps(manifest).encode())
        ctx.expected.update(self.expected)
        return ctx,module,inputs

    def test_actual_frozen_schema_validator_with_toy_rows(self):
        ctx,module,path=self.fixtures()
        self.assertEqual(len(module.validate_inputs()[1]),561)

    def test_wrong_actual_input_hash_rejected(self):
        ctx,module,path=self.fixtures();path.write_bytes(b"changed")
        with self.assertRaises(ValueError):module.validate_inputs()


class E11Tests(LibraryCases,unittest.TestCase):
    PROFILE="e11_scoring"

    def test_real_public_protocol_identity(self):
        old=self.owner+"/E11_TEACHER_PROTOCOL.json"
        raw=snapshot().source(old).read_bytes()
        self.put(old,raw)
        ctx,module=self.loaded()
        self.assertEqual(module.protocol()["reference_policy"],module.POLICY)

    def test_wrong_protocol_cannot_be_substituted(self):
        self.put(self.owner+"/E11_TEACHER_PROTOCOL.json",b"{}")
        ctx,module=self.loaded()
        with self.assertRaises(ValueError):module.protocol()


class CrossCases:
    def setUp(self):
        self.c=catalog();self.api,self.bound=self.c.cross()
        self.work=Path(os.environ["SHROOM_TEST_SCRATCH"])/("cross_"+self.GROUP+"_"+uuid.uuid4().hex)
        self.work.mkdir();self.original=self.work/"original";self.original.mkdir()
        self.temp=self.work/"temporary";self.temp.mkdir();self.cache=self.temp/"cache";self.cache.mkdir()
        self.run=self.work/"run"

    def ctx(self,synthetic=True):
        return self.api.runtime(self.bound,self.GROUP,self.original,self.run,self.temp,self.cache,synthetic=synthetic)

    def test_actual_common_current_import(self):
        module=self.ctx().load_library(self.api.GROUPS[self.GROUP]+"scripts/"+self.GROUP+"_common.py")
        self.assertEqual(module.ROOT,self.original)
        self.assertEqual(module.OUT,self.run)
        self.assertFalse(self.run.exists())

    def test_missing_real_originals_before_run(self):
        with self.assertRaises(ValueError):self.ctx(False)
        self.assertFalse(self.run.exists())

    def test_moved_public_marker_still_blocks_replay(self):
        ctx=self.ctx()
        with self.assertRaises(ValueError):ctx.validate_entry(self.api.GROUPS[self.GROUP]+"scripts/evaluate_"+self.GROUP+".py")

    def test_historical_original_never_current_fallback(self):
        ctx=self.ctx()
        with self.assertRaises(ValueError):
            with ctx.historical_reads():ctx.io_path(self.run/("scripts/"+self.GROUP+"_common.py"))

    def test_synthetic_context_cannot_launch_science(self):
        with self.assertRaises(ValueError):self.ctx().execute(self.api.GROUPS[self.GROUP]+"scripts/extract_features.py")
        self.assertFalse(self.run.exists())


class CurrentV2Tests(CrossCases,unittest.TestCase):GROUP="v2"
class CurrentV3Tests(CrossCases,unittest.TestCase):GROUP="v3"


if __name__=="__main__":unittest.main()
