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


    def test_node_current_role_keeps_historical_hash(self):
        api, bound = self.c.cross()
        item = bound.artifacts[API.NODE_AUTHOR]
        self.assertEqual(item["h1"]["sha256"], API.NODE_H1_SHA256)
        self.assertEqual(item["role"], "CURRENT_ADAPTED")
        self.assertNotEqual(item["current_sha256"], item["h1"]["sha256"])
        self.assertEqual(bound.source(API.NODE_AUTHOR), self.c.current(API.NODE_AUTHOR))

    def test_node_render_algorithm_mutation_rejected(self):
        raw = self.c.current(API.NODE_AUTHOR).read_bytes()
        with self.assertRaisesRegex(ValueError, "NODE_SCIENTIFIC_RENDER_CHANGED"):
            API.validate_node_counterpart(raw.replace(b"Number(r[k])", b"Number(r[k])+1"))

    def test_node_current_identity_cannot_masquerade_as_original(self):
        raw = self.c.current(API.NODE_AUTHOR).read_bytes()
        with self.assertRaisesRegex(ValueError, "NODE_CURRENT_IDENTITY_REQUIRED"):
            API.validate_node_counterpart(raw.replace(b"MODE='CURRENT_ADAPTED'", b"MODE='HISTORICAL_ORIGINAL'"))

    def test_adapted_node_cannot_satisfy_historical_original(self):
        api, bound = self.c.cross()
        old = API.NODE_AUTHOR
        dest = self.work / old
        dest.parent.mkdir(parents=True)
        dest.write_bytes(self.c.current(old).read_bytes())
        with self.assertRaisesRegex(ValueError, "Historical original identity mismatch"):
            bound.historical_source(old, self.work)


    def test_node_original_input_pin_not_refreshed(self):
        raw = self.c.current(API.NODE_AUTHOR).read_bytes()
        with self.assertRaisesRegex(ValueError, "NODE_ORIGINAL_INPUT_PIN_CHANGED"):
            API.validate_node_counterpart(raw.replace(b"7004fe8a1bc070d8a6508bba9f1eaa5241a7d6fbee150c9f1fb30773448bf472", b"0"*64))

    def test_unrelated_cross_record_hash_change_remains_rejected(self):
        old = "RAG/results/rag_e6_v2/.gitignore"
        previous = self.c.entries[old]["sha256"]
        try:
            self.c.entries[old]["sha256"] = "0"*64
            with self.assertRaisesRegex(ValueError, "CROSS_SCIENTIFIC_SOURCE_CHANGED"):
                self.c.cross()
        finally:
            self.c.entries[old]["sha256"] = previous


    def checksum(self, which="D"):
        old = "RAG/results/phase3_e11_task_adaptation/e11"+which.lower()+"_training/SHA256SUMS.txt"
        return self.c.checksum_evidence(old, historical=snapshot())

    def test_D_checksum_source_identity_with_real_H0_failure(self):
        result = self.checksum("D")
        self.assertEqual(result["source_identity"], "PASS")
        self.assertEqual(result["historical_input_checks"], "FAIL")
        self.assertEqual([x["status"] for x in result["checks"]].count("FAIL"), 1)

    def test_E_checksum_source_identity_with_real_H0_failures(self):
        result = self.checksum("E")
        self.assertEqual(result["source_identity"], "PASS")
        self.assertEqual(result["historical_input_checks"], "FAIL")
        self.assertEqual([x["status"] for x in result["checks"]].count("FAIL"), 2)

    def test_checksum_current_location_is_explicit(self):
        result = self.checksum("D")
        self.assertEqual(ROOT/result["current_path"], self.c.current(result["historical_path"]))

    def test_checksum_unknown_record_rejected(self):
        with self.assertRaisesRegex(ValueError, "UNDECLARED_CHECKSUM_EVIDENCE"):
            self.c.checksum_evidence("manifests/unknown.txt", historical=snapshot())

    def test_checksum_prior_current_context_is_not_H1(self):
        with self.assertRaisesRegex(ValueError, "EXPLICIT_AUTHENTICATED_H1_CONTEXT_REQUIRED"):
            self.c.checksum_evidence("RAG/results/phase3_e11_task_adaptation/e11d_training/SHA256SUMS.txt",
                                    historical=snapshot("P26"))

    def test_checksum_wrong_catalog_snapshot_rejected(self):
        other = API.Catalog(ROOT)
        with self.assertRaisesRegex(ValueError, "EXPLICIT_AUTHENTICATED_H1_CONTEXT_REQUIRED"):
            other.checksum_evidence("RAG/results/phase3_e11_task_adaptation/e11d_training/SHA256SUMS.txt",
                                    historical=snapshot())

    def test_checksum_current_record_tamper_rejected(self):
        old = "RAG/results/phase3_e11_task_adaptation/e11d_training/SHA256SUMS.txt"
        path = self.c.current(old)
        read = Path.read_bytes
        with patch.object(Path, "read_bytes", lambda p: b"changed" if p == path else read(p)):
            with self.assertRaisesRegex(ValueError, "CURRENT_SOURCE_IDENTITY_MISMATCH"):
                self.checksum()

    def test_checksum_historical_neighbor_tamper_rejected(self):
        path = snapshot().root/"RAG/results/phase3_e11_task_adaptation/e11d_training/E11D_RESULTS.json"
        read = Path.read_bytes
        with patch.object(Path, "read_bytes", lambda p: b"changed" if p == path else read(p)):
            with self.assertRaisesRegex(ValueError, "HISTORICAL_SOURCE_IDENTITY_MISMATCH"):
                self.checksum()

    def test_checksum_missing_historical_neighbor_never_current_fallback(self):
        original = API.Snapshot.source
        def missing(obj, logical):
            if logical.endswith("/E11D_RESULTS.json"):
                raise FileNotFoundError("MISSING_REQUIRED_HISTORICAL_SOURCE")
            return original(obj, logical)
        with patch.object(API.Snapshot, "source", missing):
            with self.assertRaisesRegex(FileNotFoundError, "MISSING_REQUIRED_HISTORICAL_SOURCE"):
                self.checksum()

    def test_checksum_private_preservation_is_not_synthesized(self):
        with self.assertRaisesRegex(ValueError, "UNDECLARED_HISTORICAL_SOURCE"):
            snapshot().source("RAG/results/phase3_e11_task_adaptation/e11d_training/private/PRESERVED_SHA256.json")

    def test_checksum_evidence_has_no_execution_or_runtime_pass(self):
        result = self.checksum()
        self.assertFalse(result["scientific_execution"])
        self.assertEqual(result["runtime"], "NOT VERIFIED")
        self.assertEqual(result["required_private_preservation_ledger"], "NOT PROVIDED")

    def frozen_inventory(self, which):
        h = snapshot()
        relative = "RAG/results/phase3_e11_task_adaptation/"+("e11d_training/prepare.py" if which == "D" else "e11e_training/e11e_common.py")
        source = h.source(relative)
        fn = next(n for n in ast.parse(source.read_bytes()).body
                  if isinstance(n, ast.FunctionDef) and n.name == "protected_files")
        e11 = h.root/"RAG/results/phase3_e11_task_adaptation"
        helpers = h.source("RAG/results/phase3_e11_task_adaptation/scoring_common.py")
        original_functions = [n for n in ast.parse(helpers.read_bytes()).body
                              if isinstance(n, ast.FunctionDef)
                              and n.name in ("sha_file", "find_local_repo_root")]
        self.assertEqual(len(original_functions), 2)
        ns = {"Path": Path, "hashlib": hashlib}
        exec(compile(ast.Module(body=original_functions, type_ignores=[]), str(helpers), "exec"), ns)
        actual_root = ns["find_local_repo_root"](e11)
        self.assertEqual(actual_root, h.root)
        ns.update(ROOT=actual_root, E11=e11, C=e11/"e11c_training", D=e11/"e11d_training")
        exec(compile(ast.Module(body=[fn], type_ignores=[]), str(source), "exec"), ns)
        return ns["protected_files"]()

    def test_actual_D_frozen_reader_H1_namespace_fingerprint(self):
        values = self.frozen_inventory("D")
        self.assertEqual(len(values), 168)
        self.assertEqual(digest(json.dumps(values, sort_keys=True).encode()),
                         "c0c5b4607777f9eb49c2a6f47dd411e87bbab46a2e885a7c358b007923dee612")

    def test_actual_E_frozen_reader_still_sees_D_original_list(self):
        values = self.frozen_inventory("E")
        self.assertEqual(len(values), 194)
        self.assertEqual(values["RAG/results/phase3_e11_task_adaptation/e11d_training/SHA256SUMS.txt"],
                         self.checksum("D")["record_sha256"])
        self.assertEqual(digest(json.dumps(values, sort_keys=True).encode()),
                         "2ae50853449fccf7332aec040861489bd51278f87ec5025f465bad173bdc233e")

    def test_actual_historical_finalization_run_marker_stays_closed(self):
        h = snapshot()
        source = h.source("RAG/results/phase3_e11_task_adaptation/e11_finalization/finalize.py")
        main = next(n for n in ast.parse(source.read_bytes()).body
                    if isinstance(n, ast.FunctionDef) and n.name == "main")
        def require(ok, message):
            if not ok: raise ValueError(message)
        ns = {"E11": h.root/"RAG/results/phase3_e11_task_adaptation", "require": require}
        with self.assertRaisesRegex(ValueError, "final artifacts already exist"):
            exec(compile(ast.Module(body=main.body[:2], type_ignores=[]), str(source), "exec"), ns)


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
