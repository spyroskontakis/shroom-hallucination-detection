"""Create E11-B label-blind raw-scoring inputs and text-only eligibility maps."""

from __future__ import annotations

import csv
import io
import json
import math
from collections import Counter
from pathlib import Path

from scoring_common import (HERE, ROOT, FORBIDDEN_FIELDS, POLICY, hash_parts, protocol,
                            read_jsonl, reference, require, scoring_row, sha_bytes,
                            sha_file, strict_json, text_keys)

FACTCG_RETURN = ROOT / "RAG/results/phase3_e9_claim_verification/factcg_gpu/returned_phase3-003/factcg_scores.jsonl"
E6_MATRIX = ROOT / "RAG/results/rag_e6_v3/features/e6_v3_36_features.csv"
EXPECTED_E6_SHA = "1e6386fbd0b89a3a295828259ec8fea9b5b3fc03465d65f82e546687c32e7229"
EXPECTED_ELIGIBLE = [28575, 28623, 28627, 28611, 28615]
HUMAN_FIELDS = ["sample_key", "canonical_id", "task", "fold_id",
                "factcg_support_probability", "hhem_ref_hyp_consistency",
                "nli_ref_hyp_entailment", "nli_ref_hyp_neutral", "nli_ref_hyp_contradiction",
                "minicheck_support_probability", "minicheck_status"]


def existing_or_new(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.read_bytes() == data, "prepared output changed: " + str(path))
        return
    with path.open("xb") as handle:
        handle.write(data)


def jsonl_bytes(rows: list[dict]) -> bytes:
    return b"".join(json.dumps(row, ensure_ascii=False, allow_nan=False,
                               separators=(",", ":")).encode("utf-8") + b"\n" for row in rows)


def csv_bytes(rows: list[dict], fields: list[str]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def checked(path: Path, expected: str) -> Path:
    require(path.is_file() and sha_file(path) == expected, "source hash mismatch: " + str(path))
    return path


def human_inputs(spec: dict, folds: dict) -> tuple[list[dict], list[dict], list[dict], dict]:
    canonical = read_csv(checked(ROOT / spec["inputs"]["canonical_human"]["path"],
                                 spec["inputs"]["canonical_human"]["sha256"]))
    require(len(canonical) == 561 and len({r["canonical_id"] for r in canonical}) == 561,
            "canonical human population")
    require(Counter(r["task"] for r in canonical) == {"DM": 211, "MT": 216, "PG": 134},
            "canonical task counts")
    fact = read_jsonl(FACTCG_RETURN)
    require(len(fact) == 561, "FactCG human row count")
    fact_by_id = {}
    for row in fact:
        cid = row["canonical_id"]
        require(cid not in fact_by_id, "duplicate FactCG human score")
        require(row["model_id"] == spec["detectors"]["factcg"]["model_id"] and
                row["inference_metadata"]["model_revision"] ==
                spec["detectors"]["factcg"]["revision"], "FactCG human provenance")
        fact_by_id[cid] = row
    require(sha_file(E6_MATRIX) == EXPECTED_E6_SHA, "E6-v3 feature matrix changed")
    e6 = read_csv(E6_MATRIX)
    require(len(e6) == 561 and len({r["canonical_id"] for r in e6}) == 561,
            "E6-v3 matrix population")
    e6_by_id = {r["canonical_id"]: r for r in e6}
    ids = {r["canonical_id"] for r in canonical}
    require(set(fact_by_id) == set(e6_by_id) == ids == set(folds),
            "human score ID coverage")

    table, detector_inputs = [], []
    for row in canonical:
        cid = row["canonical_id"]
        scores = e6_by_id[cid]
        nli = [float(scores["nli2_ref_hyp_" + label])
               for label in ("entailment", "neutral", "contradiction")]
        hhem = float(scores["hhem_ref_hyp_consistency"])
        factcg = float(fact_by_id[cid]["support_probability"])
        require(all(math.isfinite(x) and 0 <= x <= 1 for x in [*nli, hhem, factcg]),
                "human score range")
        require(abs(sum(nli) - 1) <= 2e-6, "human NLI sum")
        table.append({
            "sample_key": cid, "canonical_id": cid, "task": row["task"],
            "fold_id": folds[cid], "factcg_support_probability": factcg,
            "hhem_ref_hyp_consistency": hhem,
            "nli_ref_hyp_entailment": nli[0], "nli_ref_hyp_neutral": nli[1],
            "nli_ref_hyp_contradiction": nli[2],
            "minicheck_support_probability": "", "minicheck_status": "PENDING_WHOLE_HYPOTHESIS",
        })
        detector_inputs.append({"sample_key": cid, "task": row["task"],
                                "reference_text": reference(row),
                                "whole_hypothesis": row["hyp"]})
    require(all(set(scoring_row(r)) == {"sample_key", "task", "reference_text",
                                               "whole_hypothesis"} for r in detector_inputs),
            "human detector input allowlist")
    return canonical, table, detector_inputs, {
        "factcg_human_scores_sha256": sha_file(FACTCG_RETURN),
        "e6_v3_human_features_sha256": EXPECTED_E6_SHA,
        "factcg_reused": len(table), "hhem_reused": len(table), "nli_reused": len(table),
        "whole_hyp_minicheck_pending": len(table),
    }


def unlabeled_master(spec: dict) -> tuple[list[dict], list[dict], dict]:
    source = checked(ROOT / spec["inputs"]["unlabeled"]["path"],
                     spec["inputs"]["unlabeled"]["sha256"])
    raw = strict_json(source.read_text(encoding="utf-8"))
    require(len(raw) == 30000, "unlabeled row count")
    require(Counter(r["task"] for r in raw) == {"DM": 10000, "MT": 10000, "PG": 10000},
            "unlabeled task balance")
    require(all(not (FORBIDDEN_FIELDS & row.keys()) for row in raw), "labels in unlabeled data")
    require(all(row["tgt"] == "" for row in raw if row["task"] == "PG"),
            "PG empty target contract")
    first = {}
    for index, row in enumerate(raw):
        require(set(row) == {"task", "src", "tgt", "hyp", "ref", "model"},
                "unlabeled source schema")
        require(isinstance(row["hyp"], str) and row["hyp"].strip(), "empty hypothesis")
        ref = reference(row)
        sample_key = text_keys(row)["full"]
        if sample_key not in first:
            first[sample_key] = {
                "sample_key": sample_key, "task": row["task"], "src": row["src"],
                "tgt": row["tgt"], "hyp": row["hyp"], "reference_text": ref,
                "whole_hypothesis": row["hyp"], "ordering_key": sample_key,
                "source_row_index": index,
                "provenance": spec["inputs"]["unlabeled"]["sha256"],
            }
    master = [first[key] for key in sorted(first)]
    require(len(master) == 28649, "deduplicated unlabeled count")
    require(len({r["sample_key"] for r in master}) == len(master), "master duplicate")
    require(all(r["reference_text"] == r["src"] for r in master if r["task"] == "PG"),
            "PG reference must use source")
    benchmark = []
    for task in ("DM", "MT", "PG"):
        benchmark.extend([r for r in master if r["task"] == task][:200])
    require(len(benchmark) == 600 and
            Counter(r["task"] for r in benchmark) == {"DM": 200, "MT": 200, "PG": 200},
            "benchmark task balance")
    benchmark = [scoring_row(row) for row in benchmark]
    return master, benchmark, {"raw_rows": len(raw), "unique_rows": len(master),
                               "master_task_counts": dict(Counter(r["task"] for r in master)),
                               "pg_empty_target_rows": sum(r["task"] == "PG" and r["tgt"] == ""
                                                           for r in master)}


def eligibility_maps(canonical: list[dict], folds: dict, master: list[dict]) -> tuple[dict, dict]:
    outputs, counts = {}, {}
    row_keys = {r["sample_key"]: text_keys(r) for r in master}
    for fold_id in range(1, 6):
        heldout = [r for r in canonical if folds[r["canonical_id"]] == fold_id]
        blocked = {name: set() for name in ("full", "hyp", "task_ref", "pair")}
        for row in heldout:
            for name, value in text_keys(row).items():
                blocked[name].add(value)
        map_rows = []
        for row in master:
            matches = [name for name in ("full", "hyp", "task_ref", "pair")
                       if row_keys[row["sample_key"]][name] in blocked[name]]
            map_rows.append({"sample_key": row["sample_key"],
                             "eligible": not bool(matches),
                             "purge_reason": matches[0] if matches else None})
        eligible = sum(row["eligible"] for row in map_rows)
        require(eligible == EXPECTED_ELIGIBLE[fold_id - 1],
                f"fold {fold_id} purge count drift: {eligible}")
        outputs[fold_id] = map_rows
        counts[str(fold_id)] = {"heldout_human": len(heldout),
                                "eligible": eligible, "purged": len(master) - eligible,
                                "purge_reason_first_match": dict(Counter(
                                    r["purge_reason"] for r in map_rows if not r["eligible"]))}
    return outputs, counts


def main() -> None:
    spec = protocol()
    fold_rows = read_csv(checked(ROOT / spec["inputs"]["locked_folds"]["path"],
                                 spec["inputs"]["locked_folds"]["sha256"]))
    require(len(fold_rows) == 561, "fold row count")
    folds = {r["canonical_id"]: int(r["fold_id"]) for r in fold_rows}
    require(len(folds) == 561, "duplicate fold IDs")
    canonical, human, mini_inputs, human_report = human_inputs(spec, folds)
    master, benchmark, master_report = unlabeled_master(spec)
    eligibility, fold_report = eligibility_maps(canonical, folds, master)
    outputs = {
        "HUMAN_TEACHER_INPUTS.csv": csv_bytes(human, HUMAN_FIELDS),
        "human_whole_hyp_minicheck_inputs.jsonl": jsonl_bytes(mini_inputs),
        "unlabeled_master.jsonl": jsonl_bytes(master),
        "benchmark_600.jsonl": jsonl_bytes(benchmark),
    }
    for fold_id, rows in eligibility.items():
        outputs[f"fold_{fold_id}_eligibility.jsonl"] = jsonl_bytes(rows)
    for name, data in outputs.items():
        existing_or_new(HERE / name, data)
    report = {
        "status": "PASS", "protocol_sha256": spec["protocol_sha256"],
        "human": {"rows": len(human), "tasks": dict(Counter(r["task"] for r in human)),
                  **human_report},
        "unlabeled": master_report,
        "benchmark": {"rows": len(benchmark),
                      "task_counts": dict(Counter(r["task"] for r in benchmark))},
        "folds": fold_report,
        "prepared_sha256": {name: sha_bytes(data) for name, data in outputs.items()},
        "no_labels_in_detector_inputs": True,
        "inference_or_teacher_fit_run": False,
    }
    existing_or_new(HERE / "E11_INPUT_PREPARATION_REPORT.json",
                    (json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8"))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
