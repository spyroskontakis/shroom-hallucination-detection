"""Offline binding tests. Fixture hashes are not substitutes for historical H0.

Only original stdlib common-helper bodies are imported. No scientific entry,
notebook, model backend, training or inference is executed.
"""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import uuid

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / "research/shared_tools/canonical_execution_context.py").is_file())
spec = importlib.util.spec_from_file_location("_cross_context_test_api", ROOT / "research/shared_tools/cross_experiment_context_v1.py")
API = importlib.util.module_from_spec(spec)
spec.loader.exec_module(API)


def digest(data):
    return hashlib.sha256(data).hexdigest()


class FixtureOriginals:
    """Test-only declared inputs; never accepted by the production CLI pin."""
    def __init__(self, production, expected):
        self.production, self.expected = production, expected

    def __getattr__(self, name):
        return getattr(self.production, name)

    def expected_originals(self, group):
        return self.expected


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = API.Contract(ROOT)

    def setUp(self):
        self.work = Path(os.environ["SHROOM_TEST_SCRATCH"]) / ("contract_" + uuid.uuid4().hex)
        self.work.mkdir()

    def mutated(self, change):
        value = copy.deepcopy(self.contract.data)
        change(value)
        raw = json.dumps(value).encode()
        path = ROOT / API.CATALOG
        old = Path.read_bytes
        with patch.object(Path, "read_bytes", lambda p: raw if p == path else old(p)):
            with self.assertRaises((ValueError, KeyError, OSError)):
                API.Contract(ROOT, path, digest(raw))

    def test_complete_current_binding(self):
        self.assertEqual(self.contract.verify_sources()["artifacts"], 53)

    def test_wrong_contract_version(self):
        self.mutated(lambda d: d.update(version="unknown"))

    def test_wrong_current_hash(self):
        self.mutated(lambda d: d["artifacts"][0].update(current_sha256="0" * 64))

    def test_wrong_derived_hash(self):
        self.mutated(lambda d: next(x for x in d["artifacts"] if x["historical_path"].endswith(".py")).update(derived_sha256="0" * 64))

    def test_wrong_scientific_projection(self):
        self.mutated(lambda d: next(x for x in d["artifacts"] if x["historical_path"].endswith(".py")).update(scientific_projection="0" * 64))

    def test_missing_current_source(self):
        self.mutated(lambda d: d["artifacts"][0].update(current_path="research/missing_source"))

    def test_duplicate_current_source(self):
        self.mutated(lambda d: d["artifacts"][1].update(current_path=d["artifacts"][0]["current_path"]))

    def test_wrong_input_schema(self):
        self.mutated(lambda d: d["groups"]["v2"]["features"].__setitem__(0, "wrong_feature"))

    def test_wrong_feature_count(self):
        self.mutated(lambda d: d["groups"]["v3"].update(feature_count=35))

    def test_wrong_contract_pin(self):
        with self.assertRaises(ValueError):
            API.Contract(ROOT, pin="0" * 64)

    def test_wrong_cli_pin_before_loading(self):
        with patch.object(API, "Contract", side_effect=AssertionError("must not load")):
            with self.assertRaises(ValueError):
                API.main(["--expected-sha256", "0" * 64, "--group", "v2"])

    def test_missing_required_consumer(self):
        self.mutated(lambda d: d.update(artifacts=[x for x in d["artifacts"] if not x["historical_path"].endswith("/v2_common.py")]))

    def test_valid_original_h1_source(self):
        logical = API.GROUPS["v2"] + "scripts/extract_features.py"
        original = self.work / logical
        original.parent.mkdir(parents=True)
        original.write_bytes(API.ungated(self.contract.source(logical).read_bytes()))
        self.assertEqual(self.contract.historical_source(logical, self.work), original)

    def test_adapted_source_cannot_substitute_original(self):
        logical = API.GROUPS["v2"] + "scripts/extract_features.py"
        original = self.work / logical
        original.parent.mkdir(parents=True)
        original.write_bytes(self.contract.source(logical).read_bytes())
        with self.assertRaises(ValueError):
            self.contract.historical_source(logical, self.work)

    def test_missing_original_source(self):
        with self.assertRaises(FileNotFoundError):
            self.contract.historical_source(API.GROUPS["v2"] + "scripts/extract_features.py", self.work)

    def test_wrong_historical_sha(self):
        logical = API.GROUPS["v2"] + "scripts/extract_features.py"
        original = self.work / logical
        original.parent.mkdir(parents=True)
        original.write_bytes(b"wrong historical source")
        with self.assertRaises(ValueError):
            self.contract.historical_source(logical, self.work)

    def test_retained_e10_e11_sources_remain_original(self):
        for group in API.GROUPS:
            logical = API.GROUPS[group] + "scripts/" + group + "_common.py"
            item = self.contract.artifacts[logical]
            self.assertEqual(item["current_path"], logical)
            self.assertEqual(item["current_sha256"], item["h1"]["sha256"])

    def test_model_hashes_required_in_both_profiles(self):
        for group in API.GROUPS:
            requirements = self.contract.expected_originals(group)
            self.assertTrue(any("/model/" in p for p in requirements))


class CommonCases:
    @classmethod
    def setUpClass(cls):
        cls.contract = API.Contract(ROOT)

    def setUp(self):
        self.work = Path(os.environ["SHROOM_TEST_SCRATCH"]) / (self.GROUP + "_" + uuid.uuid4().hex)
        self.work.mkdir()
        self.original, self.temp, self.run = self.work / "original", self.work / "temporary", self.work / "run"
        self.original.mkdir()
        self.temp.mkdir()
        self.cache = self.temp / "cache"
        self.cache.mkdir()
        self.expected = {}
        self.proxy = FixtureOriginals(self.contract, self.expected)
        self.prefix = API.GROUPS[self.GROUP]

    def put(self, logical, raw):
        path = self.original / logical
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        self.expected[logical] = digest(raw)
        return path

    def ctx(self, *, production=False, synthetic=False, **kw):
        values = dict(contract=self.contract if production else self.proxy, group=self.GROUP,
                      original=self.original, run=self.run, temporary=self.temp,
                      cache=self.cache, synthetic=synthetic)
        values.update(kw)
        return API.runtime(**values)

    def fixtures(self):
        # Hand-written toy evidence. None of these hashes is historical H0.
        context = self.ctx(synthetic=True)
        common = context.load_library(self.prefix + "scripts/" + self.GROUP + "_common.py")
        source = self.put(self.prefix + "scripts/toy_original.py", b"toy historical source\n")
        self.put("synthetic/input.csv", b"id,value\n1,2\n")
        self.put(self.prefix + "model/toy_weights.bin", b"toy asset, not a model")
        manifest = {"protected_sha256": {"synthetic/input.csv": self.expected["synthetic/input.csv"]}}
        lock = {"frozen_files": {"scripts/toy_original.py": self.expected[self.prefix + "scripts/toy_original.py"]}}
        acquisition = {"model_id": common.MODEL_ID, "revision": common.REVISION,
                       "files": {"toy": {"path": "model/toy_weights.bin", "sha256": self.expected[self.prefix + "model/toy_weights.bin"]}}}
        for name, value in [("config/input_manifest.json", manifest), ("config/run_config.json", lock), ("provenance/acquisition.json", acquisition)]:
            self.put(self.prefix + name, json.dumps(value).encode())
        return source

    def test_actual_common_functions_import_without_writes(self):
        context = self.ctx(synthetic=True)
        before = {p.relative_to(self.work).as_posix() for p in self.work.rglob("*")}
        common = context.load_library(self.prefix + "scripts/" + self.GROUP + "_common.py")
        self.assertEqual(common.ROOT, self.original)
        self.assertEqual(common.OUT, self.run)
        self.assertEqual(before, {p.relative_to(self.work).as_posix() for p in self.work.rglob("*")})

    def test_actual_finder_resolves_current_common_import(self):
        context = self.ctx(synthetic=True)
        finder = API.Finder(context, API.engine(ROOT, self.GROUP), self.GROUP)
        name = self.GROUP + "_common"
        self.assertNotIn(name, sys.modules)
        sys.meta_path.insert(0, finder)
        try:
            common = __import__(name)
            self.assertEqual(common.OUT, self.run)
            self.assertEqual(common.ROOT, self.original)
        finally:
            sys.meta_path.remove(finder)
            sys.modules.pop(name, None)

    def test_actual_writer_isolated_and_no_overwrite(self):
        self.fixtures()
        before = {p: p.read_bytes() for p in self.original.rglob("*") if p.is_file()}
        context = self.ctx()
        context.prepare()
        common = context.load_library(self.prefix + "scripts/" + self.GROUP + "_common.py")
        path = self.run / "diagnostic/toy.json"
        common.write_json(path, {"toy": True})
        self.assertEqual(json.loads(path.read_text()), {"toy": True})
        with self.assertRaises((ValueError, FileExistsError)):
            common.write_json(path, {"toy": False})
        self.assertEqual(before, {p: p.read_bytes() for p in self.original.rglob("*") if p.is_file()})

    def test_actual_historical_guard_bodies_accept_toy_evidence(self):
        self.fixtures()
        context = self.ctx()
        common = context.load_library(self.prefix + "scripts/" + self.GROUP + "_common.py")
        self.assertEqual(len(common.verify_inputs()["protected_sha256"]), 1)
        self.assertEqual(len(common.verify_models()["files"]), 1)
        self.assertEqual(len(common.verify_freeze()["frozen_files"]), 1)
        self.assertFalse(self.run.exists())

    def test_guard_rejects_original_current_substitution(self):
        source = self.fixtures()
        context = self.ctx()
        common = context.load_library(self.prefix + "scripts/" + self.GROUP + "_common.py")
        source.write_bytes(b"current adapted source is not the original")
        with self.assertRaises((ValueError, AssertionError)):
            common.verify_freeze()
        self.assertFalse(self.run.exists())

    def test_wrong_input_identity_before_run(self):
        self.fixtures()
        (self.original / "synthetic/input.csv").write_bytes(b"wrong input")
        with self.assertRaises(ValueError):
            self.ctx()
        self.assertFalse(self.run.exists())

    def test_missing_input_before_run(self):
        self.expected["synthetic/missing.csv"] = "0" * 64
        with self.assertRaises(ValueError):
            self.ctx()
        self.assertFalse(self.run.exists())

    def test_missing_model_asset_before_run(self):
        self.expected[self.prefix + "model/missing.bin"] = "0" * 64
        with self.assertRaises(ValueError):
            self.ctx()
        self.assertFalse(self.run.exists())

    def test_wrong_model_identity_before_run(self):
        self.fixtures()
        (self.original / (self.prefix + "model/toy_weights.bin")).write_bytes(b"changed asset")
        with self.assertRaises(ValueError):
            self.ctx()
        self.assertFalse(self.run.exists())

    def test_real_originals_are_not_satisfied_by_toy_fixtures(self):
        self.fixtures()
        with self.assertRaises(ValueError):
            self.ctx(production=True)
        self.assertFalse(self.run.exists())

    def test_output_inside_git_rejected(self):
        with self.assertRaises(ValueError):
            self.ctx(run=ROOT / "should_never_be_created")

    def test_input_output_overlap_rejected(self):
        with self.assertRaises(ValueError):
            self.ctx(run=self.original / "run")

    def test_cache_outside_temporary_rejected(self):
        with self.assertRaises(ValueError):
            self.ctx(cache=self.original)

    def test_existing_run_marker_collision_rejected(self):
        self.run.mkdir()
        (self.run / "H2_RUN_IDENTITY.json").write_text("existing")
        with self.assertRaises(ValueError):
            self.ctx()

    def test_historical_marker_not_bypassed(self):
        self.put(self.prefix + "evaluation/evaluation_started.json", b"historical marker")
        context = self.ctx(synthetic=True)
        with self.assertRaises(ValueError):
            context.validate_entry(self.prefix + "scripts/evaluate_" + self.GROUP + ".py")
        self.assertFalse(self.run.exists())

    def test_public_historical_marker_cannot_be_omitted_from_inputs(self):
        context = self.ctx(synthetic=True)
        self.assertFalse((self.original / (self.prefix + "evaluation/evaluation_started.json")).exists())
        with self.assertRaises(ValueError):
            context.validate_entry(self.prefix + "scripts/evaluate_" + self.GROUP + ".py")
        self.assertFalse(self.run.exists())

    def test_report_gate_cannot_be_skipped(self):
        context = self.ctx(synthetic=True)
        with self.assertRaises(ValueError):
            context.validate_entry(self.prefix + "scripts/report_" + self.GROUP + ".py")
        self.assertFalse(self.run.exists())

    def test_synthetic_context_cannot_execute(self):
        context = self.ctx(synthetic=True)
        with self.assertRaises(ValueError):
            context.execute(self.prefix + "scripts/extract_features.py")
        self.assertFalse(self.run.exists())

    def test_wrong_group_entry_rejected(self):
        other = "v3" if self.GROUP == "v2" else "v2"
        with self.assertRaises(ValueError):
            self.ctx(synthetic=True).validate_entry(API.GROUPS[other] + "scripts/extract_features.py")

    def test_original_read_cannot_fall_back_to_current_source(self):
        context = self.ctx(synthetic=True)
        logical = self.prefix + "scripts/" + self.GROUP + "_common.py"
        with self.assertRaises(ValueError):
            with context.historical_reads():
                context.io_path(self.run / ("scripts/" + self.GROUP + "_common.py"))
        self.assertTrue(self.contract.source(logical).is_file())

    def test_current_source_read_uses_validated_mapping(self):
        context = self.ctx(synthetic=True)
        logical = self.prefix + "scripts/extract_features.py"
        self.assertEqual(context.io_path(self.run / "scripts/extract_features.py"), self.contract.source(logical))

    def test_historical_download_and_freeze_entries_static_only(self):
        context = self.ctx(synthetic=True)
        with self.assertRaises(ValueError):
            context.validate_entry(self.prefix + "scripts/freeze_run.py")


class V2Tests(CommonCases, unittest.TestCase):
    GROUP = "v2"


class V3Tests(CommonCases, unittest.TestCase):
    GROUP = "v3"


if __name__ == "__main__":
    unittest.main()
