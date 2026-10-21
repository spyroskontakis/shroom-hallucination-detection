"""Offline E11-B data, leakage, score, resume, and no-run guard tests."""

from __future__ import annotations

import ast
import csv
import contextlib
import io
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

import e11_modal
import import_layout_smoke
import detector_adapters
import prepare_scoring_inputs as prep
import run_detector
from scoring_common import (HERE, ROOT, FROZEN_PROTOCOL_CONTENT_SHA,
                            FROZEN_PROTOCOL_FILE_SHA, ScoreStore, hash_parts,
                            normalize, protocol, read_jsonl, reference,
                            scoring_digest, scoring_row, sha_file, validate_record)


class PreparedDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = protocol()
        cls.report = json.loads((HERE / "E11_INPUT_PREPARATION_REPORT.json").read_text(encoding="utf-8"))
        cls.manifest = json.loads((HERE / "E11_SCORING_MANIFEST.json").read_text(encoding="utf-8"))
        cls.master = read_jsonl(HERE / "unlabeled_master.jsonl")
        cls.benchmark = read_jsonl(HERE / "benchmark_600.jsonl")
        cls.human_minicheck = read_jsonl(HERE / "human_whole_hyp_minicheck_inputs.jsonl")
        with (HERE / "HUMAN_TEACHER_INPUTS.csv").open(encoding="utf-8", newline="") as handle:
            cls.human = list(csv.DictReader(handle))

    def test_frozen_protocol_byte_and_content_hash(self):
        self.assertEqual(sha_file(HERE / "E11_TEACHER_PROTOCOL.json"),
                         FROZEN_PROTOCOL_FILE_SHA)
        self.assertEqual(self.spec["protocol_sha256"], FROZEN_PROTOCOL_CONTENT_SHA)
        self.assertEqual(self.spec["leakage_and_selection"]["thresholds"],
                         {"hallucination_min_inclusive": 0.95,
                          "not_hallucination_max_inclusive": 0.05})
        self.assertEqual(self.spec["teacher"]["configuration"],
                         {"penalty": "l2", "C": 1.0, "solver": "lbfgs",
                          "class_weight": "balanced", "max_iter": 2000,
                          "random_state": 42})

    def test_reproducible_preparation(self):
        with contextlib.redirect_stdout(io.StringIO()):
            prep.main()  # Refuses different bytes; no inference or teacher fitting.
        for name, digest in self.report["prepared_sha256"].items():
            self.assertEqual(sha_file(HERE / name), digest, name)

    def test_human_population_and_reuse_coverage(self):
        self.assertEqual(len(self.human), 561)
        self.assertEqual(len({r["sample_key"] for r in self.human}), 561)
        self.assertEqual(Counter(r["task"] for r in self.human),
                         {"DM": 211, "MT": 216, "PG": 134})
        self.assertEqual(len(self.human_minicheck), 561)
        for row in self.human:
            self.assertEqual(row["sample_key"], row["canonical_id"])
            self.assertEqual(row["minicheck_status"], "PENDING_WHOLE_HYPOTHESIS")
            self.assertEqual(row["minicheck_support_probability"], "")
            for name in ("factcg_support_probability", "hhem_ref_hyp_consistency",
                         "nli_ref_hyp_entailment", "nli_ref_hyp_neutral",
                         "nli_ref_hyp_contradiction"):
                self.assertTrue(0 <= float(row[name]) <= 1)

    def test_factcg_join_exact_existing_scores(self):
        source = read_jsonl(ROOT / self.manifest["human_existing_score_sources"]["factcg"]["path"])
        by_id = {r["canonical_id"]: r for r in source}
        self.assertEqual(len(source), len(by_id), 561)
        for row in self.human:
            self.assertEqual(float(row["factcg_support_probability"]),
                             float(by_id[row["canonical_id"]]["support_probability"]))

    def test_hhem_nli_join_exact_existing_matrix(self):
        path = ROOT / self.manifest["human_existing_score_sources"]["nli_hhem"]["path"]
        with path.open(encoding="utf-8", newline="") as handle:
            matrix = {r["canonical_id"]: r for r in csv.DictReader(handle)}
        self.assertEqual(len(matrix), 561)
        for row in self.human:
            old = matrix[row["canonical_id"]]
            self.assertEqual(float(row["hhem_ref_hyp_consistency"]),
                             float(old["hhem_ref_hyp_consistency"]))
            for label in ("entailment", "neutral", "contradiction"):
                self.assertEqual(float(row["nli_ref_hyp_" + label]),
                                 float(old["nli2_ref_hyp_" + label]))

    def test_human_minicheck_whole_hyp_only(self):
        with (ROOT / self.spec["inputs"]["canonical_human"]["path"]).open(
                encoding="utf-8", newline="") as handle:
            canonical = {r["canonical_id"]: r for r in csv.DictReader(handle)}
        for row in self.human_minicheck:
            self.assertEqual(set(row), {"sample_key", "task", "reference_text",
                                        "whole_hypothesis"})
            source = canonical[row["sample_key"]]
            self.assertEqual(row["whole_hypothesis"], source["hyp"])
            self.assertEqual(row["reference_text"], reference(source))

    def test_unlabeled_counts_and_pg_reference(self):
        self.assertEqual(self.report["unlabeled"]["raw_rows"], 30000)
        self.assertEqual(len(self.master), 28649)
        self.assertEqual(len({r["sample_key"] for r in self.master}), 28649)
        self.assertEqual(Counter(r["task"] for r in self.master),
                         {"DM": 10000, "MT": 8649, "PG": 10000})
        for row in self.master:
            self.assertEqual(row["sample_key"], hash_parts(
                row["task"], row["src"], row["tgt"], row["hyp"]))
            self.assertEqual(row["reference_text"], reference(row))
            if row["task"] == "PG":
                self.assertEqual(row["tgt"], "")
                self.assertEqual(row["reference_text"], row["src"])

    def test_normalization_and_policy(self):
        self.assertEqual(normalize(" e\u0301  \t X "), "é X")
        self.assertNotEqual(normalize("Truth"), normalize("truth"))
        self.assertEqual(reference({"task": "DM", "src": "source", "tgt": "target"}), "target")
        self.assertEqual(reference({"task": "MT", "src": "source", "tgt": "target"}), "target")
        self.assertEqual(reference({"task": "PG", "src": "source", "tgt": ""}), "source")

    def test_benchmark_exact_balance_and_hash_order(self):
        self.assertEqual(len(self.benchmark), 600)
        self.assertEqual(len({r["sample_key"] for r in self.benchmark}), 600)
        self.assertEqual(Counter(r["task"] for r in self.benchmark),
                         {"DM": 200, "MT": 200, "PG": 200})
        self.assertEqual(sha_file(HERE / "benchmark_600.jsonl"),
                         self.manifest["prepared_sha256"]["benchmark_600.jsonl"])
        for task in ("DM", "MT", "PG"):
            actual = [r["sample_key"] for r in self.benchmark if r["task"] == task]
            expected = sorted(r["sample_key"] for r in self.master if r["task"] == task)[:200]
            self.assertEqual(actual, expected)

    def test_five_fold_eligibility_maps_and_text_purge(self):
        expected = [28575, 28623, 28627, 28611, 28615]
        master_ids = [r["sample_key"] for r in self.master]
        for fold, count in enumerate(expected, 1):
            rows = read_jsonl(HERE / f"fold_{fold}_eligibility.jsonl")
            self.assertEqual(len(rows), 28649)
            self.assertEqual([r["sample_key"] for r in rows], master_ids)
            self.assertEqual(sum(r["eligible"] for r in rows), count)
            self.assertTrue(all(r["purge_reason"] in
                                (None, "full", "hyp", "task_ref", "pair") for r in rows))

    def test_detector_inputs_are_strictly_label_blind(self):
        for row in self.benchmark + self.human_minicheck:
            self.assertEqual(set(row), {"sample_key", "task", "reference_text",
                                        "whole_hypothesis"})
            self.assertEqual(scoring_row(row), row)
        for row in self.master:
            self.assertFalse(set(row) & {"label", "labels", "label_bin", "gold",
                                         "p(H)", "p_hallucination", "prediction"})

    def test_nli_indices_and_hhem_orientation(self):
        config = json.loads((ROOT / "RAG/results/rag_e6_v2/model/config.json").read_text())
        self.assertEqual(config["id2label"],
                         {"0": "entailment", "1": "neutral", "2": "contradiction"})
        backend = (ROOT / "RAG/results/rag_e6_v3/scripts/hhem_backend.py").read_text()
        self.assertIn("torch.sigmoid(logits[:,0])", backend)
        self.assertIn("'consistency'", backend)
        self.assertIn("Higher means supported/consistent", self.spec["detectors"]["hhem"]["orientation"])

    def test_modal_resources_and_full_guard(self):
        self.assertEqual(e11_modal.validate_local()["status"], "PASS")
        modal = self.manifest["modal"]
        self.assertEqual((modal["gpu"], modal["gpu_count"], modal["memory_mib"],
                          modal["ephemeral_disk_mib"], modal["timeout_seconds"]),
                         ("A100-80GB", 1, 65536, 524288, 43200))
        self.assertNotIn("--full-run", e11_modal.stage_command("factcg", "benchmark"))
        self.assertIn("--full-run", e11_modal.stage_command("factcg", "full"))
        with self.assertRaises(ValueError):
            run_detector.run("factcg", "full", HERE, HERE, HERE, HERE, HERE, 64, False)

    def test_remote_import_layout_from_independent_cwd(self):
        result = import_layout_smoke.main()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["imports_from_other_cwd"], 3)
        self.assertEqual(result["indexed_parent_depth_lookups"], [])
        self.assertFalse(result["modal_job_started"])

    def test_local_root_discovery_uses_marker_not_fixed_depth(self):
        from scoring_common import find_local_repo_root
        self.assertEqual(find_local_repo_root(HERE), ROOT)
        self.assertIsNone(find_local_repo_root(Path(tempfile.gettempdir()) / "opt" / "e11"))

    def test_no_official_test_or_teacher_training_in_operational_code(self):
        for name in ("scoring_common.py", "prepare_scoring_inputs.py",
                     "detector_adapters.py", "run_detector.py", "e11_modal.py"):
            source = (HERE / name).read_text(encoding="utf-8")
            ast.parse(source)
            self.assertNotIn("SHROOM_test-labeled", source)
            self.assertNotIn("test.model-agnostic.json", source)
            self.assertNotIn("LogisticRegression(", source)
            self.assertNotIn("predict_proba(", source)


class ScoreContractTests(unittest.TestCase):
    def setUp(self):
        self.spec = protocol()
        self.universe = [{"sample_key": f"key-{i}", "task": "DM",
                          "reference_text": f"Evidence {i}",
                          "whole_hypothesis": f"Claim {i}"} for i in range(3)]
        self.fact = self.spec["detectors"]["factcg"]
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / "factcg"

    def record(self, i, value=0.6):
        return run_detector.make_records("factcg", [self.universe[i]],
                                         [{"factcg_support_probability": value}],
                                         self.fact["model_id"], self.fact["revision"])[0]

    def store(self):
        return ScoreStore(self.folder, "factcg", self.universe,
                          self.fact["model_id"], self.fact["revision"], "universe-digest")

    def test_partial_resume_without_recompute(self):
        store = self.store()
        store.append([self.record(0)])
        resumed = self.store()
        self.assertEqual([r["sample_key"] for r in resumed.missing(self.universe)],
                         ["key-1", "key-2"])
        resumed.append([self.record(1), self.record(2)])
        self.assertEqual(self.store().validate_scope(self.universe)["requested_rows"], 3)

    def test_valid_tail_after_interrupted_checkpoint_reconciles(self):
        store = self.store()
        store.append([self.record(0)])
        # Simulate a process killed after fsync of a complete row but before
        # the manifest's next atomic checkpoint.
        with (self.folder / "scores.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(self.record(1)) + "\n")
        resumed = self.store()
        self.assertEqual([r["sample_key"] for r in resumed.missing(self.universe)],
                         ["key-2"])
        manifest = json.loads((self.folder / "manifest.json").read_text())
        self.assertEqual(manifest["completed_rows"], 2)

    def test_duplicate_output_fails(self):
        store = self.store()
        store.append([self.record(0)])
        with (self.folder / "scores.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(self.record(0)) + "\n")
        with self.assertRaises(ValueError):
            self.store()

    def test_missing_output_detected(self):
        store = self.store()
        store.append([self.record(0)])
        with self.assertRaisesRegex(ValueError, "missing score rows"):
            store.validate_scope(self.universe)

    def test_corrupt_checkpointed_score_detected(self):
        store = self.store()
        store.append([self.record(0)])
        path = self.folder / "scores.jsonl"
        path.write_bytes(path.read_bytes().replace(b"0.6", b"0.7"))
        with self.assertRaises(ValueError):
            self.store()

    def test_invalid_score_ranges_and_nli_sum(self):
        with self.assertRaises(ValueError):
            self.record(0, 1.1)
        nli = self.spec["detectors"]["nli"]
        with self.assertRaisesRegex(ValueError, "sum to 1"):
            run_detector.make_records("nli", [self.universe[0]], [{
                "nli_ref_hyp_entailment": 0.4, "nli_ref_hyp_neutral": 0.4,
                "nli_ref_hyp_contradiction": 0.4}], nli["model_id"], nli["revision"])

    def test_hhem_and_minicheck_ranges(self):
        for name, score_field in [("hhem", "hhem_ref_hyp_consistency"),
                                  ("minicheck", "minicheck_support_probability")]:
            spec = self.spec["detectors"][name]
            record = run_detector.make_records(
                name, [self.universe[0]], [{score_field: 0.5}],
                spec["model_id"], spec["revision"])[0]
            validate_record(record, name, self.universe[0],
                            spec["model_id"], spec["revision"])

    def test_factcg_adapter_passes_entire_reference_hypothesis(self):
        calls = []
        class FakeBackend:
            def score(self, tokenizer, model, reference_text, whole_hypothesis):
                calls.append((reference_text, whole_hypothesis))
                return 0.73, {"reference_chunks": 1}
        adapter = detector_adapters.FactCGAdapter.__new__(detector_adapters.FactCGAdapter)
        adapter.backend, adapter.tokenizer, adapter.model = FakeBackend(), object(), object()
        self.assertEqual(adapter.score(self.universe[:1]),
                         [{"factcg_support_probability": 0.73}])
        self.assertEqual(calls, [("Evidence 0", "Claim 0")])

    def test_minicheck_adapter_batches_whole_hypotheses(self):
        calls = []
        class FakeScorer:
            def score(self, docs, claims, chunk_size):
                calls.append((docs, claims, chunk_size))
                return None, [0.8] * len(claims), None, None
        adapter = detector_adapters.MiniCheckAdapter.__new__(detector_adapters.MiniCheckAdapter)
        adapter.scorer = FakeScorer()
        rows = [{"sample_key": f"k{i}", "task": "PG", "reference_text": f"Source {i}",
                 "whole_hypothesis": f"Whole hypothesis {i}"} for i in range(17)]
        self.assertEqual(len(adapter.score(rows)), 17)
        self.assertEqual([len(call[1]) for call in calls], [16, 1])
        self.assertEqual(calls[0][1][0], "Whole hypothesis 0")
        self.assertTrue(all(call[2] == 32468 for call in calls))


if __name__ == "__main__":
    unittest.main(verbosity=2)
