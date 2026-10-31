"""Offline negative/unit tests for the repository verifier, not experiment replay."""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

FILE = Path(__file__).resolve().parents[1] / "verify_repository.py"
SPEC = importlib.util.spec_from_file_location("shroom_verifier_test_api", FILE)
V = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V)


class VerifierTests(unittest.TestCase):
    def test_module_import_has_no_main_call(self):
        self.assertTrue(callable(V.verify))

    def test_root_detection(self):
        self.assertEqual(V.root_of(FILE), FILE.parents[2])

    def test_status_actual_failure(self):
        self.assertEqual(V.status_code({"checks":[{"status":"FAIL"}]}), 1)

    def test_h0_failure_is_never_pass(self):
        self.assertEqual(V.status_code({"checks":[{"status":"KNOWN_HISTORICAL_EXCEPTION","historical_status":"FAIL"}]}), 1)

    def test_unknown_runtime_is_not_success(self):
        self.assertEqual(V.status_code({"checks":[{"status":"NOT_VERIFIED"}]}), 2)

    def test_missing_artifact_is_not_success(self):
        self.assertEqual(V.status_code({"checks":[{"status":"BLOCKED_MISSING_ARTIFACT"}]}), 2)

    def test_all_pass(self):
        self.assertEqual(V.status_code({"checks":[{"status":"PASS"}]}), 0)

    def test_source_failure_prevents_test_worker_start(self):
        result={"scope":"TEST_FIXTURE","files":0,"checks":[{"check":"public_file","status":"FAIL"}]}
        with patch.object(V,"root_of",return_value=FILE.parents[2]), \
             patch.object(V,"load_index",return_value={}), \
             patch.object(V,"publication_inventory",return_value=({},"TEST_FIXTURE")), \
             patch.object(V,"verify",return_value=result), \
             patch.object(V,"run_tests",side_effect=AssertionError("unsafe worker")), \
             patch("builtins.print"):
            self.assertEqual(V.main(["--tests","--scratch","never_created"]),1)
        self.assertEqual(result["checks"][-1]["status"],"NOT_VERIFIED")

    def test_relative_scratch_rejected_before_any_write(self):
        with self.assertRaisesRegex(ValueError,"absolute"):
            V.run_tests(FILE.parents[2],{},Path("relative_scratch"))

    def test_network_scratch_rejected_before_any_filesystem_read(self):
        with patch.object(V,"reject_links",side_effect=AssertionError("network path read")):
            with self.assertRaisesRegex(ValueError,"Network scratch"):
                V.run_tests(FILE.parents[2],{},Path("//unreachable.invalid/scratch"))

    def test_read_only_git_disables_lazy_fetch_and_prompts(self):
        from types import SimpleNamespace
        with patch.object(V.subprocess,"run",return_value=SimpleNamespace(returncode=0,stdout=b"",stderr=b"")) as call:
            V.git(FILE.parents[2],"ls-tree","HEAD")
        env=call.call_args.kwargs["env"]
        self.assertEqual(env["GIT_NO_LAZY_FETCH"],"1")
        self.assertEqual(env["GIT_TERMINAL_PROMPT"],"0")
        self.assertEqual(env["GIT_NO_REPLACE_OBJECTS"],"1")

    def test_absolute_mapping_rejected(self):
        with self.assertRaises(ValueError): V.logical("/private/file")

    def test_parent_mapping_rejected(self):
        with self.assertRaises(ValueError): V.logical("a/../private")

    def test_windows_mapping_rejected(self):
        with self.assertRaises(ValueError): V.logical("C:/private")

    def test_backslash_mapping_rejected(self):
        with self.assertRaises(ValueError): V.logical("a\\b")

    def test_git_metadata_mapping_rejected(self):
        with self.assertRaises(ValueError): V.logical("a/.git/config")

    def test_valid_mapping(self):
        self.assertEqual(V.logical("research/source.py"), "research/source.py")

    def test_original_links_pass(self):
        rows=V.local_links("docs/a.md","[ok](../research/x.py)",{"research/x.py"})
        self.assertEqual(rows[0]["status"],"PASS")

    def test_frozen_broken_link_stays_fail(self):
        rows=V.local_links(V.E11,"[old](../../../codex/evaluation_protocol_decision.md)",set())
        self.assertEqual(rows[0]["status"],"FAIL")

    def test_directory_link(self):
        self.assertEqual(V.local_links("README.md","[x](research/)",{"research/a.py"})[0]["status"],"PASS")

    def test_external_links_not_claimed_live_verified(self):
        self.assertEqual(V.local_links("README.md","[x](https://example.org/x)",set()),[])

    def test_reference_link(self):
        self.assertEqual(V.local_links("docs/x.md","[a]: ../missing.py",set())[0]["status"],"FAIL")

    def test_percent_encoded_link(self):
        self.assertEqual(V.local_links("README.md","[x](a%20b.md)",{"a b.md"})[0]["status"],"PASS")

    def test_json_invalid(self):
        self.assertEqual(V.syntax_status("x.json",b"{",{})["status"],"FAIL")

    def test_notebook_invalid(self):
        self.assertEqual(V.syntax_status("x.ipynb",b"{}",{})["status"],"FAIL")

    def test_notebook_magics_are_not_executed(self):
        raw=json.dumps({"nbformat":4,"cells":[{"cell_type":"code","source":["!never execute"],"outputs":[]}]}).encode()
        self.assertEqual(V.syntax_status("x.ipynb",raw,{})["status"],"PASS")

    def test_python_invalid(self):
        self.assertEqual(V.syntax_status("x.py",b"if :",{})["status"],"FAIL")

    def test_exact_historical_syntax_evidence(self):
        raw=b"if :"
        value=V.syntax_status("e8.py",raw,{"e8.py":V.digest(raw)})
        self.assertEqual(value["status"],"KNOWN_HISTORICAL_EXCEPTION")
        self.assertEqual(value["historical_status"],"FAIL")

    def test_changed_historical_syntax_evidence_rejected(self):
        self.assertEqual(V.syntax_status("e8.py",b"if : changed",{"e8.py":V.digest(b"if :")})["status"],"FAIL")

    def test_credentials_signal_is_redacted(self):
        raw=("ghp_"+"a"*35).encode()
        result=V.privacy_findings("x.py",raw)
        self.assertTrue(result)
        self.assertNotIn(raw.decode(),json.dumps(result))

    def test_json_escaped_personal_path(self):
        raw=json.dumps({"path":"C:"+"/Users/"+"Someone/private"}).encode()
        self.assertTrue(V.privacy_findings("x.json",raw))

    def test_weights_disallowed(self):
        self.assertEqual(V.privacy_findings("weights/model.safetensors",b"")[0]["status"],"FAIL")

    def test_code_only_is_not_raw_dataset(self):
        self.assertEqual(V.privacy_findings("research/source.py",b"MODEL='model/id'"),[])

    def test_changed_public_payload_fails_before_helper_import(self):
        with patch.object(V,"load_compatibility",side_effect=AssertionError("unsafe import")):
            result=V.verify(FILE.parents[2],{"protected_files":{}},{"README.md":{"sha256":"0"*64}},"FIXTURE")
        self.assertEqual(V.status_code(result),1)
        self.assertEqual(result["checks"][0]["reason"],"changed")

    def test_missing_migration_source_fails_before_helper_import(self):
        with patch.object(Path,"is_file",return_value=False), \
             patch.object(V,"load_compatibility",side_effect=AssertionError("unsafe import")):
            result=V.verify(FILE.parents[2],{"protected_files":{}},{"source.py":{"sha256":"0"*64}},"FIXTURE")
        self.assertEqual(V.status_code(result),1)
        self.assertEqual(result["checks"][0]["reason"],"missing")

    def test_unsafe_path_fails_before_helper_import(self):
        with patch.object(V,"reject_links",side_effect=ValueError("reparse")), \
             patch.object(V,"load_compatibility",side_effect=AssertionError("unsafe import")):
            result=V.verify(FILE.parents[2],{"protected_files":{}},{"source.py":{"sha256":"0"*64}},"FIXTURE")
        self.assertEqual(V.status_code(result),1)
        self.assertEqual(result["checks"][0]["reason"],"unsafe_or_unreadable")

    def test_refreshed_snapshot_cannot_hide_changed_protected_source(self):
        raw=(FILE.parents[2]/"README.md").read_bytes()
        index={"protected_files":{"README.md":"0"*64}}
        with patch.object(V,"load_compatibility",side_effect=AssertionError("unsafe import")):
            result=V.verify(FILE.parents[2],index,{"README.md":{"sha256":V.digest(raw)}},"FIXTURE")
        self.assertEqual(V.status_code(result),1)
        self.assertEqual(result["checks"][0]["check"],"protected_file")

    def test_protected_file_cannot_be_omitted_from_public_projection(self):
        with patch.object(V,"load_compatibility",side_effect=AssertionError("unsafe import")):
            result=V.verify(FILE.parents[2],{"protected_files":{"README.md":"0"*64}},{},"FIXTURE")
        self.assertEqual(V.status_code(result),1)
        self.assertEqual(result["checks"][0]["reason"],"missing_from_snapshot")

    def test_missing_public_verification_authority_is_failure(self):
        result=V.verify(FILE.parents[2],{"protected_files":{},"compatibility":{"path":"helper.py"}},{},"FIXTURE")
        self.assertEqual(V.status_code(result),1)
        self.assertEqual(result["checks"][0]["reason"],"compatibility_validator_not_in_public_snapshot")

    def test_rejected_catalog_is_structured_failure(self):
        raw=FILE.read_bytes()
        inventory={"research/shared_tools/verify_repository.py":{"sha256":V.digest(raw)}}
        index={"protected_files":{},"compatibility":{"path":"research/shared_tools/verify_repository.py"}}
        with patch.object(V,"load_compatibility",side_effect=ValueError("pinned source mismatch")):
            result=V.verify(FILE.parents[2],index,inventory,"FIXTURE")
        self.assertEqual(V.status_code(result),1)
        self.assertEqual(result["checks"][0]["check"],"source_contract")

    def test_fenced_examples_keep_real_line_numbers(self):
        fence=chr(96)*3
        text="Heading\n"+fence+"python\n[fake](missing)\n"+fence+"\n[real](ok.md)\n"
        rows=V.local_links("README.md",text,{"ok.md"})
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["line"],5)
        self.assertEqual(rows[0]["status"],"PASS")

    def test_tilde_fenced_examples_are_not_links(self):
        rows=V.local_links("README.md","~~~text\n[fake](missing)\n~~~\n[real](ok.md)\n",{"ok.md"})
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["line"],4)

    def test_missing_markdown_image_is_reported(self):
        self.assertEqual(V.local_links("README.md","![plot](missing.png)",set())[0]["status"],"FAIL")

    def test_documented_privacy_projection_keeps_original_requirement_failed(self):
        records=[{"path":"record.json","original_sha256":"0"*64,"sha256":"1"*64,
                  "verification_level":"PUBLIC_SAFE_DERIVATIVE_SHA256","changes":[{"change":"private fields removed"}]}]
        result=V.derivative_evidence(records,"record.json","0"*64,"1"*64)
        self.assertEqual(result["classification"],"DOCUMENTED_PUBLIC_SAFE_DERIVATIVE")
        self.assertEqual(result["original_hash_requirement"],"FAIL")
        self.assertEqual(result["scientific_value_equivalence"],"NOT_INDEPENDENTLY_VERIFIED")

    def test_wrong_original_hash_is_not_explained_by_projection_record(self):
        records=[{"path":"record.json","original_sha256":"2"*64,"sha256":"1"*64,
                  "verification_level":"PUBLIC_SAFE_DERIVATIVE_SHA256"}]
        result=V.derivative_evidence(records,"record.json","0"*64,"1"*64)
        self.assertEqual(result["classification"],"UNEXPLAINED_HISTORICAL_MISMATCH")

    def test_invalid_authority_has_json_exit_three(self):
        import io
        from contextlib import redirect_stdout
        output=io.StringIO()
        with patch.object(V,"root_of",side_effect=ValueError("invalid authority")), redirect_stdout(output):
            self.assertEqual(V.main(["--json"]),3)
        result=json.loads(output.getvalue())
        self.assertEqual(result["exit"],3)
        self.assertEqual(result["checks"][0]["status"],"NOT_VERIFIED")

    def test_read_only_verification_source_avoids_add_commit_push(self):
        tree=ast.parse(FILE.read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=="git":
                args=[x.value for x in node.args if isinstance(x,ast.Constant) and isinstance(x.value,str)]
                self.assertFalse(any(x in ("add","commit","push","merge","checkout","reset","fetch") for x in args))



class ArchiveLayoutTests(unittest.TestCase):
    def setUp(self):
        root = V.root_of(FILE)
        self.index = json.loads((root / V.INDEX).read_bytes())
        self.hashes = {x["original"]: x["public_h1_sha256"]
                       for x in self.index["historical_archive_layout"]["entries"]}

    def test_archive_extends_current_layout_without_rewriting_v2_plan(self):
        original = json.dumps(self.index["migration_destinations"], sort_keys=True)
        targets = V.approved_destinations(self.index, self.hashes)
        self.assertEqual(len(targets), 790)
        for old in V.ARCHIVE_ORIGINALS:
            self.assertEqual(targets[old], V.ARCHIVE_ROOT+"/"+old)
        self.assertEqual(json.dumps(self.index["migration_destinations"], sort_keys=True), original)

    def test_unknown_archive_version_rejected(self):
        self.index["historical_archive_layout"]["version"] = "unknown"
        with self.assertRaises(ValueError): V.approved_destinations(self.index, self.hashes)

    def test_missing_archive_source_rejected(self):
        self.index["historical_archive_layout"]["entries"].pop()
        with self.assertRaises(ValueError): V.approved_destinations(self.index, self.hashes)

    def test_additional_archive_source_rejected(self):
        self.index["historical_archive_layout"]["entries"].append({"original": "unapproved.py"})
        with self.assertRaises(ValueError): V.approved_destinations(self.index, self.hashes)

    def test_arbitrary_archive_destination_rejected(self):
        self.index["historical_archive_layout"]["entries"][0]["destination"] = "research/elsewhere.py"
        with self.assertRaises(ValueError): V.approved_destinations(self.index, self.hashes)

    def test_extra_archive_binding_fields_rejected(self):
        self.index["historical_archive_layout"]["entries"][0]["fallback"] = "old_path"
        with self.assertRaises(ValueError): V.approved_destinations(self.index, self.hashes)

    def test_archive_hash_must_match_independent_original_evidence(self):
        self.index["historical_archive_layout"]["entries"][0]["public_h1_sha256"] = "0"*64
        with self.assertRaises(ValueError): V.approved_destinations(self.index, self.hashes)

    def test_missing_original_evidence_cannot_be_waived(self):
        with self.assertRaises(ValueError): V.approved_destinations(self.index, {})

    def test_current_catalog_cannot_be_hidden_outside_public_projection(self):
        raw = FILE.read_bytes()
        name = "research/shared_tools/verify_repository.py"
        index = {"protected_files": {}, "compatibility": {"path": name},
                 "compatibility_catalog": {"path": "hidden_catalog.json"}}
        with patch.object(V, "load_compatibility", side_effect=AssertionError("unsafe helper import")):
            result = V.verify(FILE.parents[2], index, {name: {"sha256": V.digest(raw)}}, "FIXTURE")
        self.assertEqual(result["checks"][0]["reason"], "compatibility_catalog_not_in_public_snapshot")
        self.assertEqual(V.status_code(result), 1)


class SmokeImportCases:
    NAME = None

    def load(self):
        root=V.root_of(FILE)
        path=root/("research/experiments/phase3_advanced_methods/e10_factcg/development/local_smoke/"+self.NAME)
        spec=importlib.util.spec_from_file_location("safe_smoke_"+self.NAME.replace(".","_"),path)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_actual_import_does_not_mutate_sys_path(self):
        import sys
        before=list(sys.path)
        self.load()
        self.assertEqual(sys.path,before)

    def test_actual_import_does_not_load_model_or_frozen_helpers(self):
        import sys
        before=set(sys.modules)
        self.load()
        self.assertFalse((set(sys.modules)-before)&{"torch","transformers","factcg_common","factcg_backend","modal"})

    def test_missing_original_helpers_fail_before_writes(self):
        module=self.load()
        with patch.object(Path,"is_file",return_value=False):
            with self.assertRaisesRegex(FileNotFoundError,"BLOCKED_MISSING_INPUTS"):
                module._load_historical_helpers()

    def test_scientific_main_ast_matches_authentic_original(self):
        module=self.load()
        root=Path(os.environ["SHROOM_SNAPSHOT_H1"])
        name="RAG/results/phase3_e9_claim_verification/factcg_local_smoke/"+self.NAME
        old=next(n for n in ast.parse((root/name).read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=="main")
        current=next(n for n in ast.parse(Path(module.__file__).read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=="main")
        self.assertEqual(ast.unparse(current.body[0]),"_load_historical_helpers()")
        current.body=current.body[1:]
        # Three previously reviewed IO-only aliases follow the relocated,
        # byte-identical selection/checkpoint records. Model logic is untouched.
        aliases=[n for n in ast.walk(current) if isinstance(n,ast.Name) and n.id=="RECORDS"]
        self.assertEqual(len(aliases),3 if self.NAME=="run_cpu_sun12.py" else 0)
        for node in aliases: node.id="HERE"
        self.assertEqual(ast.dump(current,include_attributes=False),ast.dump(old,include_attributes=False))


class OriginalSmokeImportTests(SmokeImportCases,unittest.TestCase):
    NAME="run_local_smoke.py"


class SunSmokeImportTests(SmokeImportCases,unittest.TestCase):
    NAME="run_cpu_sun12.py"


if __name__=="__main__":
    unittest.main()
