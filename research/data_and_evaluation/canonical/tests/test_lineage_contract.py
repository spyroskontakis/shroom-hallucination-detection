"""Synthetic lineage checks only. Fixtures stay in the external test scratch."""
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import unittest
import uuid
from contextlib import redirect_stdout


def load_checked(path, pin, name):
    p = Path(path)
    raw = p.read_bytes()
    if hashlib.sha256(raw).hexdigest() != pin:
        raise RuntimeError("test module pin mismatch")
    module = importlib.util.module_from_spec(importlib.util.spec_from_file_location(name, p))
    sys.modules[name] = module
    exec(compile(raw, str(p), "exec"), module.__dict__)
    return module


c = load_checked(os.environ["SHROOM_H2_SUPPORT"], os.environ["SHROOM_H2_SUPPORT_SHA256"],
                 "_test_context_" + uuid.uuid4().hex)


class LineageTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(os.environ["SHROOM_H2_TEST_SCRATCH"])
        if not self.base.is_absolute() or not self.base.is_dir():
            raise RuntimeError("explicit external scratch required")
        self.case = self.base / ("lineage_" + uuid.uuid4().hex)
        self.case.mkdir()
        self.root = self.case / "evidence"; self.root.mkdir()
        self.legacy = "legacy/source.py"; self.target = "current/source.py"
        self.raw = b"def identity(value):\n    return value\n"
        p = self.root / self.legacy; p.parent.mkdir(); p.write_bytes(self.raw)
        self.body = c.source_symbols(self.raw)
        self.cat = {
            "schema_version": c.SCHEMA,
            "baseline": {"commit": "1" * 40, "tree": "2" * 40},
            "definitions": copy.deepcopy(c.DEFINITIONS),
            "artifacts": [{
                "id": "source", "role": "source_historical",
                "historical_path": self.legacy, "target_path": self.target,
                "h1": {"sha256": c.sha256(self.raw), "git_blob": c.git_blob_id(self.raw),
                       "size_bytes": len(self.raw)},
                "current": {"status": "UNIMPLEMENTED", "role": "source_current",
                            "sha256": None, "review_id": None, "symbols": {}},
                "symbols": self.body.copy(),
            }],
            "contracts": {"ORIGINAL": [{"artifact_id": "source", "expected_sha256": c.sha256(self.raw)}]},
            "evidence_sources": [], "runtime_status": "NOT VERIFIED",
        }

    def evidence(self, mode="H1_SNAPSHOT", **kw):
        return c.FileEvidence(self.root, mode=mode,
                              baseline_commit=kw.get("commit", "1" * 40),
                              baseline_tree=kw.get("tree", "2" * 40))

    def check(self, mode="H1_SNAPSHOT", **kw):
        return c.verify_artifact(self.cat, "source", mode=mode,
                                 evidence=self.evidence(mode), **kw)

    def reviewed(self):
        new = b"# Synthetic adapter bootstrap only\n" + self.raw
        p = self.root / self.target; p.parent.mkdir(); p.write_bytes(new)
        self.cat["artifacts"][0]["current"] = {
            "status": "REVIEWED", "role": "source_current",
            "sha256": c.sha256(new), "review_id": "SYNTHETIC_TEST_ONLY",
            "symbols": self.body.copy(),
        }
        return p

    def test_valid_h1_historical_source(self):
        self.assertEqual(self.check().status, "PASS")

    def test_valid_h0_frozen_source(self):
        result = c.verify_contract(self.cat, "ORIGINAL", mode="H0_REPLAY",
                                   evidence=self.evidence("H0_REPLAY"))
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["runtime_status"], "NOT VERIFIED")
        self.assertFalse(result["execution_permitted"])

    def test_h1_blob_identity_is_required(self):
        self.cat["artifacts"][0]["h1"]["git_blob"] = "0" * 40
        self.assertEqual(self.check().reason, "H1_OBJECT_IDENTITY_MISMATCH")

    def test_h1_size_identity_is_required(self):
        self.cat["artifacts"][0]["h1"]["size_bytes"] += 1
        self.assertEqual(self.check().status, "FAIL")

    def test_tampered_source_is_fail(self):
        (self.root / self.legacy).write_bytes(self.raw + b"# changed\n")
        self.assertEqual(self.check().status, "FAIL")

    def test_missing_is_not_pass(self):
        # Declare a valid but absent synthetic historical path, without deleting evidence.
        self.cat["artifacts"][0]["historical_path"] = "absent/source.py"
        self.assertEqual(self.check().status, "MISSING")

    def test_wrong_context_provider_is_fail(self):
        x = c.verify_artifact(self.cat, "source", mode="H0_REPLAY", evidence=self.evidence())
        self.assertEqual(x.status, "FAIL")

    def test_wrong_baseline_commit_is_fail(self):
        x = c.verify_artifact(self.cat, "source", mode="H1_SNAPSHOT",
                              evidence=self.evidence(commit="3" * 40))
        self.assertEqual(x.status, "FAIL")

    def test_wrong_baseline_tree_is_fail(self):
        x = c.verify_artifact(self.cat, "source", mode="H1_SNAPSHOT",
                              evidence=self.evidence(tree="3" * 40))
        self.assertEqual(x.status, "FAIL")

    def test_unknown_mode_is_fail(self):
        x = c.verify_artifact(self.cat, "source", mode="OTHER", evidence=self.evidence())
        self.assertEqual(x.status, "FAIL")

    def test_unknown_artifact_is_fail(self):
        x = c.verify_artifact(self.cat, "unknown", mode="H1_SNAPSHOT", evidence=self.evidence())
        self.assertEqual(x.status, "FAIL")

    def test_wrong_historical_path_is_fail(self):
        self.assertEqual(self.check(presented_path=self.target).status, "FAIL")

    def test_unimplemented_h2_is_not_verified(self):
        self.assertEqual(self.check("H2_CURRENT").status, "NOT VERIFIED")

    def test_reviewed_synthetic_h2_context(self):
        self.reviewed()
        x = self.check("H2_CURRENT", presented_path=self.target)
        self.assertEqual(x.status, "PASS")
        self.assertEqual(self.check().status, "PASS")  # old bytes independently retained

    def test_historical_path_cannot_be_h2_presentation(self):
        self.reviewed()
        self.assertEqual(self.check("H2_CURRENT", presented_path=self.legacy).status, "FAIL")

    def test_h2_bytes_cannot_pass_historical_hash(self):
        p = self.reviewed()
        (self.root / self.legacy).write_bytes(p.read_bytes())
        self.assertEqual(self.check().status, "FAIL")

    def test_scientific_symbol_change_is_fail(self):
        p = self.reviewed()
        p.write_bytes(b"def identity(value):\n    return 0\n")
        self.cat["artifacts"][0]["current"]["sha256"] = c.sha256(p.read_bytes())
        self.assertEqual(self.check("H2_CURRENT").status, "FAIL")

    def test_missing_symbol_is_fail(self):
        p = self.reviewed(); p.write_bytes(b"# no function\n")
        self.cat["artifacts"][0]["current"]["sha256"] = c.sha256(p.read_bytes())
        self.assertEqual(self.check("H2_CURRENT").status, "FAIL")

    def test_current_hash_needs_review_reference(self):
        self.reviewed(); self.cat["artifacts"][0]["current"]["review_id"] = ""
        self.assertEqual(self.check("H2_CURRENT").status, "FAIL")

    def test_cannot_refresh_scientific_anchor(self):
        self.reviewed()
        self.cat["artifacts"][0]["current"]["symbols"]["identity"] = "0" * 64
        self.assertEqual(self.check("H2_CURRENT").status, "FAIL")

    def test_h0_mismatch_does_not_fall_back_to_h1(self):
        self.cat["contracts"]["ORIGINAL"][0]["expected_sha256"] = c.sha256(b"missing-original-H0")
        result = c.verify_contract(self.cat, "ORIGINAL", mode="H0_REPLAY",
                                   evidence=self.evidence("H0_REPLAY"))
        self.assertEqual(result["counts"]["FAIL"], 1)
        self.assertEqual(self.check().status, "PASS")
        self.assertFalse(result["execution_permitted"])

    def test_caller_cannot_replace_frozen_expected_hash(self):
        self.cat["contracts"]["ORIGINAL"][0]["expected_sha256"] = c.sha256(b"H0-original")
        result = self.check("H0_REPLAY", expected_h0=c.sha256(self.raw))
        self.assertEqual(result.status, "FAIL")

    def test_contract_rejects_h1_as_runtime_context(self):
        result = c.verify_contract(self.cat, "ORIGINAL", mode="H1_SNAPSHOT",
                                   evidence=self.evidence())
        self.assertEqual(result["status"], "FAIL")

    def test_missing_h0_is_reported(self):
        self.cat["artifacts"][0]["historical_path"] = "missing/original.py"
        result = c.verify_contract(self.cat, "ORIGINAL", mode="H0_REPLAY",
                                   evidence=self.evidence("H0_REPLAY"))
        self.assertEqual(result["counts"]["MISSING"], 1)

    def test_duplicate_json_key_rejected(self):
        with self.assertRaises(c.ValidationError): c.strict_json('{"a":1,"a":2}')

    def test_nonfinite_json_rejected(self):
        for text in ("NaN", "Infinity", "-Infinity", "1e999"):
            with self.subTest(text=text):
                with self.assertRaises(c.ValidationError): c.strict_json(text)

    def test_schema_and_unknown_fields_rejected(self):
        for key, value in (("schema_version", "other"), ("extra", True)):
            bad = copy.deepcopy(self.cat); bad[key] = value
            with self.assertRaises(c.ValidationError): c.validate_catalog(bad)

    def test_duplicate_identity_rejected(self):
        self.cat["artifacts"].append(copy.deepcopy(self.cat["artifacts"][0]))
        with self.assertRaises(c.ValidationError): c.validate_catalog(self.cat)

    def test_duplicate_target_rejected(self):
        second = copy.deepcopy(self.cat["artifacts"][0])
        second.update(id="other", historical_path="other/source.py")
        self.cat["artifacts"].append(second)
        with self.assertRaises(c.ValidationError): c.validate_catalog(self.cat)

    def test_role_substitution_rejected(self):
        self.cat["artifacts"][0]["current"]["role"] = "input_original"
        self.assertEqual(self.check("H2_CURRENT").status, "FAIL")

    def test_path_traversal_rejected(self):
        self.cat["artifacts"][0]["historical_path"] = "../private.py"
        self.assertEqual(self.check().status, "FAIL")

    def test_catalog_requires_independent_pin(self):
        p = self.case / "catalog.json"; p.write_text(json.dumps(self.cat), encoding="utf-8")
        self.assertEqual(c.load_catalog(p, expected_sha256=c.sha256(p.read_bytes()))["schema_version"], c.SCHEMA)
        with self.assertRaises(c.ValidationError): c.load_catalog(p, expected_sha256="0" * 64)

    def test_catalog_tamper_rejected(self):
        p = self.case / "catalog.json"; p.write_text(json.dumps(self.cat), encoding="utf-8")
        pin = c.sha256(p.read_bytes())
        self.cat["contracts"]["ORIGINAL"][0]["expected_sha256"] = "0" * 64
        p.write_text(json.dumps(self.cat), encoding="utf-8")
        with self.assertRaises(c.ValidationError): c.load_catalog(p, expected_sha256=pin)

    def test_public_catalog_keeps_all_h2_unimplemented(self):
        real = c.load_catalog(os.environ["SHROOM_H2_CATALOG"],
                              expected_sha256=os.environ["SHROOM_H2_CATALOG_SHA256"])
        self.assertTrue(all(x["current"]["status"] == "UNIMPLEMENTED" for x in real["artifacts"]))
        self.assertEqual(real["runtime_status"], "NOT VERIFIED")

    def test_public_e10_pending_ledger_is_not_cured(self):
        real = c.load_catalog(os.environ["SHROOM_H2_CATALOG"],
                              expected_sha256=os.environ["SHROOM_H2_CATALOG_SHA256"])
        byid = {x["id"]: x for x in real["artifacts"]}
        states = ["MISSING" if byid[x["artifact_id"]]["h1"] is None else
                  "PASS" if byid[x["artifact_id"]]["h1"]["sha256"] == x["expected_sha256"]
                  else "FAIL" for x in real["contracts"]["E10"]]
        self.assertEqual({s: states.count(s) for s in ("PASS", "FAIL", "MISSING")},
                         {"PASS": 11, "FAIL": 2, "MISSING": 6})

    def test_aggregate_never_promotes_missing_or_not_verified(self):
        for state in ("FAIL", "MISSING", "NOT VERIFIED"):
            self.assertEqual(c.combine([c.Check("x", state, "synthetic", "H0_REPLAY"),
                                        c.Check("y", "PASS", "synthetic", "H0_REPLAY")]), state)

    def test_source_is_parsed_never_executed(self):
        raw = b"raise RuntimeError('must not run')\ndef identity(value):\n    return value\n"
        (self.root / self.legacy).write_bytes(raw)
        self.cat["artifacts"][0]["h1"] = {"sha256": c.sha256(raw),
            "git_blob": c.git_blob_id(raw), "size_bytes": len(raw)}
        self.assertEqual(self.check().status, "PASS")

    def test_duplicate_symbol_is_rejected(self):
        with self.assertRaises(c.ValidationError): c.source_symbols(self.raw + self.raw)

    def test_cli_requires_explicit_context(self):
        v = load_checked(os.environ["SHROOM_H2_VERIFIER"],
                         os.environ["SHROOM_H2_VERIFIER_SHA256"], "_test_cli_" + uuid.uuid4().hex)
        with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            v.parser().parse_args([])

    def test_cli_valid_synthetic_snapshot(self):
        v = load_checked(os.environ["SHROOM_H2_VERIFIER"],
                         os.environ["SHROOM_H2_VERIFIER_SHA256"], "_test_cli_" + uuid.uuid4().hex)
        p = self.case / "catalog.json"; p.write_text(json.dumps(self.cat), encoding="utf-8")
        args = ["--support", os.environ["SHROOM_H2_SUPPORT"], "--support-sha256", os.environ["SHROOM_H2_SUPPORT_SHA256"],
                "--catalog", str(p), "--catalog-sha256", c.sha256(p.read_bytes()), "--root", str(self.root),
                "--baseline-commit", "1" * 40, "--baseline-tree", "2" * 40,
                "--mode", "H1_SNAPSHOT", "--artifact", "source"]
        with redirect_stdout(io.StringIO()) as buffer:
            code = v.main(args)
        result = json.loads(buffer.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["runtime_status"], "NOT VERIFIED")
        self.assertFalse(result["execution_permitted"])


if __name__ == "__main__":
    unittest.main()
