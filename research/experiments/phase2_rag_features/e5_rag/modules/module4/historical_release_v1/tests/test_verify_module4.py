from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "verify_module4.py"
SPEC = importlib.util.spec_from_file_location("verify_module4", SCRIPT)
verifier = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(verifier)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class VerifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "repo"
        self.release = self.root / "RAG" / "module4_release_v1"
        self.release.mkdir(parents=True)
        self.source = self.release / "README.md"
        self.source.write_bytes(b"source\n")
        self.artifact = self.root / "artifacts" / "local.bin"
        self.artifact.parent.mkdir()
        self.artifact.write_bytes(b"artifact\n")
        self.manifest = self.release / "RELEASE_MANIFEST.json"
        self.write_manifest()

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def entry(path: str, data: bytes) -> dict[str, object]:
        return {"path": path, "size": len(data), "sha256": digest(data)}

    def manifest_data(self) -> dict[str, object]:
        return {
            "schema_version": verifier.SCHEMA_VERSION,
            "release_root": "RAG/module4_release_v1",
            "inventories": {
                "source": [self.entry("RAG/module4_release_v1/README.md", b"source\n")],
                "local_artifacts": [self.entry("artifacts/local.bin", b"artifact\n")],
            },
        }

    def write_manifest(self, data: dict[str, object] | None = None) -> None:
        self.manifest.write_text(
            json.dumps(data or self.manifest_data()), encoding="utf-8"
        )

    def run_verify(self, mode: str = "local-artifacts") -> dict[str, object]:
        return verifier.verify(self.root, self.manifest, mode)

    def test_valid_file_passes(self) -> None:
        result = self.run_verify()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["checked_count"], 2)

    def test_hash_mismatch_fails(self) -> None:
        self.source.write_bytes(b"Source\n")
        result = self.run_verify("source")
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("sha256", result["errors"][0])

    def test_size_mismatch_fails(self) -> None:
        data = self.manifest_data()
        data["inventories"]["source"][0]["size"] += 1
        self.write_manifest(data)
        self.assertEqual(self.run_verify("source")["status"], "FAIL")

    def test_missing_required_file_fails_without_reconstruction(self) -> None:
        self.artifact.unlink()
        result = self.run_verify()
        self.assertEqual(result["status"], "FAIL")
        self.assertFalse(self.artifact.exists())

    def test_duplicate_manifest_entries_rejected(self) -> None:
        data = self.manifest_data()
        data["inventories"]["source"].append(
            dict(data["inventories"]["source"][0])
        )
        self.write_manifest(data)
        with self.assertRaises(verifier.ManifestError):
            self.run_verify("source")

    def test_duplicate_json_keys_rejected(self) -> None:
        self.manifest.write_text(
            '{"schema_version":"module4-release-manifest-v1",'
            '"schema_version":"module4-release-manifest-v1"}',
            encoding="utf-8",
        )
        with self.assertRaises(verifier.ManifestError):
            self.run_verify("source")

    def test_invalid_schema_and_empty_inventory_rejected(self) -> None:
        data = self.manifest_data()
        data["schema_version"] = "unknown"
        self.write_manifest(data)
        with self.assertRaises(verifier.ManifestError):
            self.run_verify("source")
        data = self.manifest_data()
        data["inventories"]["source"] = []
        self.write_manifest(data)
        with self.assertRaises(verifier.ManifestError):
            self.run_verify("source")

    def test_path_traversal_rejected(self) -> None:
        data = self.manifest_data()
        data["inventories"]["local_artifacts"][0]["path"] = "../outside.bin"
        self.write_manifest(data)
        with self.assertRaises(verifier.ManifestError):
            self.run_verify()

    def test_absolute_path_injection_rejected(self) -> None:
        for injected in ("C:\\outside.bin", "/tmp/outside.bin", "\\\\host\\share"):
            data = self.manifest_data()
            data["inventories"]["local_artifacts"][0]["path"] = injected
            self.write_manifest(data)
            with self.assertRaises(verifier.ManifestError):
                self.run_verify()

    def test_runs_from_different_working_directory(self) -> None:
        other = Path(self.temp.name) / "elsewhere"
        other.mkdir()
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--repo-root",
                str(self.root),
                "--manifest",
                "RAG/module4_release_v1/RELEASE_MANIFEST.json",
                "--mode",
                "source",
                "--json",
            ],
            cwd=other,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, verifier.EXIT_PASS, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["status"], "PASS")

    def test_source_and_local_modes_are_distinct(self) -> None:
        self.artifact.unlink()
        source = self.run_verify("source")
        local = self.run_verify("local-artifacts")
        self.assertEqual(source["status"], "PASS")
        self.assertTrue(source["external_artifacts_not_checked"])
        self.assertEqual(source["skipped_local_artifact_count"], 1)
        self.assertEqual(local["status"], "FAIL")

    def test_checked_files_remain_byte_identical(self) -> None:
        before = {
            path: (path.read_bytes(), path.stat().st_mtime_ns)
            for path in (self.source, self.artifact)
        }
        self.run_verify()
        after = {
            path: (path.read_bytes(), path.stat().st_mtime_ns)
            for path in (self.source, self.artifact)
        }
        self.assertEqual(before, after)

    def test_symlink_escape_rejected(self) -> None:
        outside = Path(self.temp.name) / "outside.bin"
        outside.write_bytes(b"outside")
        link = self.root / "artifacts" / "escape.bin"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Symlinks unavailable: {exc}")
        data = self.manifest_data()
        data["inventories"]["local_artifacts"] = [
            self.entry("artifacts/escape.bin", b"outside")
        ]
        self.write_manifest(data)
        result = self.run_verify()
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("escapes repository root", result["errors"][0])


if __name__ == "__main__":
    unittest.main()
