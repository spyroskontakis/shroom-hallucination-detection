"""Offline E11-A freeze/preparation tests. Never imports CUDA or fits a model."""

from __future__ import annotations

import ast
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import e11a_modal
import e11a_prepare_data
import e11a_train_fold
from scoring_common import HERE, ROOT, sha_file
from validate_e11a_protocol import EXPECTED_SHA, read_jsonl, validate_local


class E11APreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = e11a_prepare_data.load_protocol()
        cls.prepared = json.loads(e11a_prepare_data.MANIFEST.read_text(encoding="utf-8"))

    def test_frozen_identity_model_labels_and_threshold(self):
        self.assertEqual(self.spec["protocol_sha256"], EXPECTED_SHA)
        self.assertEqual(self.spec["data"]["label_mapping"],
                         {"0": "Not Hallucination", "1": "Hallucination"})
        self.assertEqual(self.spec["model"]["revision"],
                         "b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7")
        self.assertEqual(self.spec["output"]["classification_threshold"], 0.5)

    def test_local_pretraining_validator(self):
        self.assertEqual(validate_local()["status"], "PASS")

    def test_preparation_idempotent_without_training(self):
        self.assertEqual(e11a_prepare_data.main(), self.prepared)
        self.assertFalse((HERE / "e11a_prepared" / "oof_predictions.jsonl").exists())

    def test_locked_fold_ids_and_smoke_selection(self):
        for fold_id in range(1, 6):
            fold = self.prepared["folds"][str(fold_id)]
            training = read_jsonl(HERE / fold["train_path"])
            heldout = read_jsonl(HERE / fold["heldout_path"])
            self.assertTrue(all(r["fold_id"] != fold_id for r in training))
            self.assertTrue(all(r["fold_id"] == fold_id for r in heldout))
            self.assertFalse({r["sample_id"] for r in training} &
                             {r["sample_id"] for r in heldout})
        training = read_jsonl(HERE / self.prepared["folds"]["1"]["train_path"])
        selected = e11a_train_fold.select_smoke_rows(training)
        self.assertEqual(len(selected), 32)
        self.assertEqual(sum(r["label"] == 0 for r in selected), 16)
        self.assertEqual(sum(r["label"] == 1 for r in selected), 16)
        self.assertTrue(all(r["fold_id"] != 1 for r in selected))

    def test_full_fold_and_smoke_guards_before_gpu(self):
        with self.assertRaisesRegex(ValueError, "allow-full-fold"):
            e11a_train_fold.execute(1, "fold", HERE, HERE, HERE,
                                     "guard-test", False)
        with self.assertRaisesRegex(ValueError, "fold 1 only"):
            e11a_train_fold.execute(2, "smoke", HERE, HERE, HERE,
                                     "guard-test", False)
        self.assertEqual(e11a_train_fold.linear_lr(1e-5, 1, 10, 2), 5e-6)
        self.assertEqual(e11a_train_fold.linear_lr(1e-5, 10, 10, 2), 0)

    def test_modal_smoke_configuration_static(self):
        checked = e11a_modal.validate_local_config()
        self.assertEqual((checked["modal_gpu"], checked["modal_disk_mib"]),
                         ("A100-80GB", 524288))
        self.assertFalse(checked["modal_job_started"])
        self.assertEqual(e11a_modal.TIMEOUT_SECONDS, 1800)
        self.assertEqual(e11a_modal.VOLUME, "shroom-e11a-training-results")

    def test_no_test_pseudo_or_detector_inputs_in_prepared_rows(self):
        for fold_id in range(1, 6):
            for split in ("train", "heldout"):
                name = self.prepared["folds"][str(fold_id)][split + "_path"]
                rows = read_jsonl(HERE / name)
                self.assertTrue(all(set(r) == {
                    "sample_id", "fold_id", "task", "reference_field",
                    "text", "text_pair", "label"} for r in rows))
                self.assertTrue(all("HYPOTHESIS:\n" in r["text_pair"] for r in rows))
        for name in ("e11a_prepare_data.py", "e11a_train_fold.py", "e11a_modal.py",
                     "validate_e11a_protocol.py"):
            source = (HERE / name).read_text(encoding="utf-8")
            ast.parse(source)
            self.assertNotIn("SHROOM_test-labeled", source)
            self.assertNotIn("test.model-agnostic.json", source)
            self.assertNotIn("retained_pseudo_labels.jsonl", source)
            self.assertNotIn("factcg_support_probability", source)
            self.assertNotIn("minicheck_support_probability", source)

    def test_shallow_remote_import_from_other_cwd(self):
        with tempfile.TemporaryDirectory(prefix="e11a-shallow-") as scratch:
            runtime = Path(scratch) / "opt" / "e11a"
            elsewhere = Path(scratch) / "unrelated"
            runtime.mkdir(parents=True)
            elsewhere.mkdir()
            for name in ("scoring_common.py", "e11a_prepare_data.py",
                         "validate_e11a_protocol.py", "e11a_train_fold.py",
                         "E11A_TRAINING_PROTOCOL.json"):
                (runtime / name).write_bytes((HERE / name).read_bytes())
            code = ("import sys,pathlib; "
                    f"sys.path.insert(0,{str(runtime)!r}); "
                    "import scoring_common,e11a_prepare_data,validate_e11a_protocol,e11a_train_fold; "
                    "assert scoring_common.ROOT is None; "
                    "assert e11a_prepare_data.load_protocol()['experiment_id']=='E11-A'")
            result = subprocess.run([sys.executable, "-I", "-B", "-c", code],
                                    cwd=elsewhere, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_modal_function_hydration_from_separate_directory(self):
        with tempfile.TemporaryDirectory(prefix="e11a-hydration-") as scratch:
            runtime = Path(scratch) / "opt" / "e11a"
            function_dir = Path(scratch) / "root"
            elsewhere = Path(scratch) / "unrelated"
            for directory in (runtime, function_dir, elsewhere):
                directory.mkdir(parents=True)
            for name in ("scoring_common.py", "e11a_prepare_data.py",
                         "validate_e11a_protocol.py", "e11a_train_fold.py",
                         "E11A_TRAINING_PROTOCOL.json"):
                shutil.copyfile(HERE / name, runtime / name)
            source = (HERE / "e11a_modal.py").read_text(encoding="utf-8")
            declaration = 'REMOTE_ROOT = "/opt/e11a"'
            self.assertEqual(source.count(declaration), 1)
            (function_dir / "e11a_modal.py").write_text(
                source.replace(declaration, "REMOTE_ROOT = " + repr(str(runtime))),
                encoding="utf-8")
            code = ("import pathlib,sys,modal; modal.is_local=lambda:False; "
                    f"sys.path.insert(0,{str(function_dir)!r}); "
                    "import e11a_modal; "
                    f"assert pathlib.Path(e11a_modal.HERE).resolve()==pathlib.Path({str(runtime)!r}).resolve(); "
                    "assert e11a_modal.ROOT is None")
            result = subprocess.run([sys.executable, "-B", "-c", code],
                                    cwd=elsewhere, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
