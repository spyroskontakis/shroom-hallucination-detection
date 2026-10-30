"""Future read-only Modal Volume downloads; no GPU job or pseudo-label work."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

VOLUME = "shroom-e11-raw-detector-scores"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--scope", choices=("benchmark", "full"), required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", args.run_id) is None:
        raise ValueError("invalid run ID")
    files = [f"runs/{args.run_id}/COMPLETE.json"]
    for detector in ("factcg", "minicheck", "nli", "hhem"):
        base = f"raw_detector_scores/{detector}"
        files.extend([base + "/scores.jsonl", base + "/manifest.json",
                      base + f"/validation_{args.scope}.json"])
    files.extend(["human_minicheck/scores.jsonl", "human_minicheck/manifest.json",
                  "human_minicheck/validation_human.json"])
    for item in files:
        remote = "e11/" + item
        local = args.destination / item
        local.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([sys.executable, "-m", "modal", "volume", "get",
                        VOLUME, remote, str(local)], check=True)
    status = json.loads((args.destination / f"runs/{args.run_id}/COMPLETE.json").read_text(
        encoding="utf-8"))
    if status.get("status") != "PASS" or status.get("mode") != args.scope:
        raise ValueError("Downloaded run is not a completed matching scope")
    print(f"Downloaded {len(files)} files to {args.destination}")


if __name__ == "__main__":
    main()
