"""Read-only validation of downloaded E11 raw scores; never fits a teacher."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scoring_common import (HERE, SCORE_FIELDS, protocol, read_jsonl, require,
                            scoring_row, validate_record)


def validate_file(path: Path, detector: str, universe: list[dict],
                  requested: list[dict], model_id: str, revision: str) -> dict:
    sources = {row["sample_key"]: scoring_row(row) for row in universe}
    require(len(sources) == len(universe), "duplicate source key")
    rows = read_jsonl(path)
    seen = set()
    for record in rows:
        key = record["sample_key"]
        require(key in sources and key not in seen, "foreign or duplicate score key")
        validate_record(record, detector, sources[key], model_id, revision)
        seen.add(key)
    requested_ids = {row["sample_key"] for row in requested}
    require(len(requested_ids) == len(requested), "duplicate requested key")
    missing = requested_ids - seen
    require(not missing, f"{detector}: missing {len(missing)} requested score rows")
    return {"detector": detector, "stored": len(rows), "requested": len(requested),
            "missing": 0, "status": "PASS"}


def validate_download(directory: Path, scope: str) -> dict:
    require(scope in {"benchmark", "full"}, "scope must be benchmark or full")
    spec = protocol()
    master = read_jsonl(HERE / "unlabeled_master.jsonl")
    requested = (read_jsonl(HERE / "benchmark_600.jsonl")
                 if scope == "benchmark" else master)
    human = read_jsonl(HERE / "human_whole_hyp_minicheck_inputs.jsonl")
    results = {}
    for detector in ("factcg", "minicheck", "hhem", "nli"):
        model = spec["detectors"][detector]
        path = directory / "raw_detector_scores" / detector / "scores.jsonl"
        results[detector] = validate_file(path, detector, master, requested,
                                          model["model_id"], model["revision"])
    mini = spec["detectors"]["minicheck"]
    results["human_minicheck"] = validate_file(
        directory / "human_minicheck" / "scores.jsonl", "minicheck", human, human,
        mini["model_id"], mini["revision"])
    return {"status": "PASS", "scope": scope, "detectors": results,
            "teacher_or_pseudo_labels_generated": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=("benchmark", "full"), required=True)
    parser.add_argument("--directory", type=Path, required=True,
                        help="Local directory containing raw_detector_scores/ and human_minicheck/")
    args = parser.parse_args()
    print(json.dumps(validate_download(args.directory, args.scope), indent=2))


if __name__ == "__main__":
    main()
