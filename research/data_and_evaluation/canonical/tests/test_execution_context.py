"""Synthetic path-planning tests. No execution-directory creation by the helper."""
import copy
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
import unittest
import uuid


def load_context():
    p = Path(os.environ["SHROOM_H2_SUPPORT"])
    raw = p.read_bytes()
    if hashlib.sha256(raw).hexdigest() != os.environ["SHROOM_H2_SUPPORT_SHA256"]:
        raise RuntimeError("support pin mismatch")
    name = "_path_context_" + uuid.uuid4().hex
    m = importlib.util.module_from_spec(importlib.util.spec_from_file_location(name, p))
    sys.modules[name] = m
    exec(compile(raw, str(p), "exec"), m.__dict__)
    return m


c = load_context()


class ContextTests(unittest.TestCase):
    def setUp(self):
        base = Path(os.environ["SHROOM_H2_TEST_SCRATCH"])
        if not base.is_absolute() or not base.is_dir():
            raise RuntimeError("explicit external scratch required")
        self.case = base / ("context_" + uuid.uuid4().hex); self.case.mkdir()
        self.source = self.case / "source"; self.source.mkdir()
        self.input = self.case / "input.csv"; self.input.write_bytes(b"id,value\nSYNTHETIC,1\n")
        self.run = self.case / "new_run"

    def plan(self, **changes):
        kw = dict(run_dir=self.run, source_roots=[self.source],
                  input_paths=[self.input], output_names=["audit.csv", "logs/run.json"])
        kw.update(changes)
        return c.plan_run(**kw)

    def test_valid_external_plan_is_read_only(self):
        before = sorted(str(p.relative_to(self.case)) for p in self.case.rglob("*"))
        result = self.plan()
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["created"])
        self.assertFalse(result["execution_permitted"])
        self.assertFalse(self.run.exists())
        self.assertEqual(before, sorted(str(p.relative_to(self.case)) for p in self.case.rglob("*")))

    def test_existing_run_rejected_without_truncation(self):
        self.run.mkdir()
        p = self.run / "keep"; p.write_bytes(b"synthetic keep")
        with self.assertRaises(c.ValidationError): self.plan()
        self.assertEqual(p.read_bytes(), b"synthetic keep")

    def test_existing_file_run_rejected(self):
        self.run.write_bytes(b"do not truncate")
        with self.assertRaises(c.ValidationError): self.plan()
        self.assertEqual(self.run.read_bytes(), b"do not truncate")

    def test_missing_run_parent_rejected(self):
        with self.assertRaises(c.ValidationError): self.plan(run_dir=self.case / "absent" / "run")

    def test_relative_run_rejected(self):
        with self.assertRaises(c.ValidationError): self.plan(run_dir=Path("relative"))

    def test_physical_root_traversal_rejected(self):
        with self.assertRaises(c.ValidationError):
            self.plan(run_dir=self.case / ".." / "escaped_run")

    def test_unc_roots_rejected_before_filesystem_access(self):
        for root in (r"\\server\share", r"\\?\C:\device_root"):
            with self.subTest(root=root):
                with self.assertRaises(c.ValidationError):
                    c.FileEvidence(Path(root), mode="H1_SNAPSHOT",
                                   baseline_commit="1" * 40, baseline_tree="2" * 40)

    def test_missing_input_rejected(self):
        with self.assertRaises(c.ValidationError): self.plan(input_paths=[self.case / "missing.csv"])

    def test_directory_input_rejected(self):
        with self.assertRaises(c.ValidationError): self.plan(input_paths=[self.source])

    def test_missing_source_root_rejected(self):
        with self.assertRaises(c.ValidationError): self.plan(source_roots=[self.case / "missing"])

    def test_run_inside_source_rejected(self):
        with self.assertRaises(c.ValidationError): self.plan(run_dir=self.source / "run")

    def test_run_source_overlap_rejected(self):
        with self.assertRaises(c.ValidationError): self.plan(run_dir=self.source)

    def test_input_destination_overlap_rejected(self):
        with self.assertRaises(c.ValidationError): self.plan(run_dir=self.input)

    def test_git_ancestry_rejected(self):
        checkout = self.case / "checkout"; checkout.mkdir()
        (checkout / ".git").write_text("synthetic worktree pointer", encoding="utf-8")
        with self.assertRaises(c.ValidationError): self.plan(run_dir=checkout / "run")

    def test_output_traversal_rejected(self):
        with self.assertRaises(c.ValidationError): self.plan(output_names=["../private.csv"])

    def test_absolute_output_rejected(self):
        with self.assertRaises(c.ValidationError): self.plan(output_names=[str(self.input)])

    def test_backslash_output_rejected(self):
        with self.assertRaises(c.ValidationError): self.plan(output_names=["a\\b.csv"])

    def test_duplicate_case_output_rejected(self):
        with self.assertRaises(c.ValidationError): self.plan(output_names=["A.csv", "a.csv"])

    def test_output_file_directory_collision_rejected(self):
        with self.assertRaises(c.ValidationError): self.plan(output_names=["logs", "logs/run.json"])

    def test_empty_ownership_lists_rejected(self):
        for key in ("source_roots", "input_paths", "output_names"):
            with self.subTest(key=key):
                with self.assertRaises(c.ValidationError): self.plan(**{key: []})

    def test_unsafe_platform_paths_rejected(self):
        for p in ("/absolute", "../a", "a//b", "a/./b", "a:b", "a/.git/config",
                  "CON", "NUL.txt", "a/trailing.", 'a/"quote', "a/*", "a/\0"):
            with self.subTest(path=repr(p)):
                with self.assertRaises(c.ValidationError): c.logical_path(p)

    def test_evidence_cannot_escape_root(self):
        e = c.FileEvidence(self.case, mode="H1_SNAPSHOT",
                           baseline_commit="1" * 40, baseline_tree="2" * 40)
        with self.assertRaises(c.ValidationError): e.read("../outside")

    def test_evidence_requires_absolute_root(self):
        with self.assertRaises(c.ValidationError):
            c.FileEvidence(Path("."), mode="H1_SNAPSHOT",
                           baseline_commit="1" * 40, baseline_tree="2" * 40)

    def test_evidence_missing_root_is_not_created(self):
        p = self.case / "absent"
        with self.assertRaises(c.ValidationError):
            c.FileEvidence(p, mode="H1_SNAPSHOT",
                           baseline_commit="1" * 40, baseline_tree="2" * 40)
        self.assertFalse(p.exists())

    def test_evidence_rejects_directory_artifact(self):
        e = c.FileEvidence(self.case, mode="H1_SNAPSHOT",
                           baseline_commit="1" * 40, baseline_tree="2" * 40)
        with self.assertRaises(c.ValidationError): e.read("source")

    def test_evidence_missing_file_returns_none(self):
        e = c.FileEvidence(self.case, mode="H1_SNAPSHOT",
                           baseline_commit="1" * 40, baseline_tree="2" * 40)
        self.assertIsNone(e.read("absent.bin"))

    def test_no_overwrite_at_fixture_boundary(self):
        p = self.case / "complete"; p.write_bytes(b"complete")
        with self.assertRaises(FileExistsError):
            with p.open("xb") as handle: handle.write(b"wrong")
        self.assertEqual(p.read_bytes(), b"complete")

    def test_source_module_has_no_ml_imports(self):
        self.assertFalse(any(k in sys.modules for k in ("torch", "transformers", "pandas", "numpy")))

    def test_actual_ntfs_junction_is_rejected(self):
        p = Path(os.environ["SHROOM_H2_REPARSE_FIXTURE"])
        self.assertTrue(p.lstat().st_file_attributes & 1024)
        with self.assertRaises(c.ValidationError): self.plan(run_dir=p / "run")
        with self.assertRaises(c.ValidationError):
            c.FileEvidence(p, mode="H1_SNAPSHOT",
                           baseline_commit="1" * 40, baseline_tree="2" * 40)

    def test_missing_current_file_after_review_is_missing(self):
        raw = b"# synthetic\n"
        catalog = dict(schema_version=c.SCHEMA,
                       baseline={"commit": "1" * 40, "tree": "2" * 40},
                       definitions=copy.deepcopy(c.DEFINITIONS),
                       artifacts=[dict(id="src", role="source_historical",
                            historical_path="old/a.py", target_path="new/a.py",
                            h1={"sha256": c.sha256(raw), "git_blob": c.git_blob_id(raw), "size_bytes": len(raw)},
                            symbols={}, current={"status": "REVIEWED", "role": "source_current",
                            "sha256": c.sha256(raw), "review_id": "SYNTHETIC_ONLY", "symbols": {}})],
                       contracts={"H0": [{"artifact_id": "src", "expected_sha256": c.sha256(raw)}]},
                       evidence_sources=[], runtime_status="NOT VERIFIED")
        e = c.FileEvidence(self.case, mode="H2_CURRENT",
                           baseline_commit="1" * 40, baseline_tree="2" * 40)
        self.assertEqual(c.verify_artifact(catalog, "src", mode="H2_CURRENT", evidence=e).status, "MISSING")


if __name__ == "__main__":
    unittest.main()
