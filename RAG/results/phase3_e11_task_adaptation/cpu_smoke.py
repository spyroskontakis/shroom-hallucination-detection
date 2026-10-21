"""Optional local synthetic-only CPU smoke for the original E6 NLI/HHEM backends."""

from __future__ import annotations

import argparse
import json
import math
import sys

from scoring_common import ROOT, require


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--detector", choices=("nli", "hhem"), required=True)
    args = parser.parse_args()
    folder = (ROOT / "RAG/results/rag_e6_v2/scripts" if args.detector == "nli"
              else ROOT / "RAG/results/rag_e6_v3/scripts")
    sys.path.insert(0, str(folder))
    backend = (__import__("nli_backend") if args.detector == "nli"
               else __import__("hhem_backend"))
    tokenizer, model = backend.load_backend()
    pairs = [
        {"pair_id": "synthetic-supported:A", "canonical_id": "synthetic-supported",
         "group": "A", "premise": "Athens is in Greece.",
         "hypothesis": "Athens is in Greece."},
        {"pair_id": "synthetic-contradicted:A", "canonical_id": "synthetic-contradicted",
         "group": "A", "premise": "Athens is in Greece.",
         "hypothesis": "Athens is in Canada."},
    ]
    scores, audits = backend.infer_batch(tokenizer, model, pairs)
    require(len(scores) == len(audits) == 2, "synthetic smoke row count")
    if args.detector == "nli":
        for row in scores:
            values = [row[name] for name in ("entailment", "neutral", "contradiction")]
            require(all(math.isfinite(x) and 0 <= x <= 1 for x in values), "NLI range")
            require(abs(sum(values) - 1) <= 2e-6, "NLI probability sum")
    else:
        require(all(math.isfinite(row["consistency"]) and
                    0 <= row["consistency"] <= 1 for row in scores), "HHEM range")
    print(json.dumps({"status": "PASS", "detector": args.detector,
                      "synthetic_pairs": 2, "device": "cpu", "scores": scores,
                      "human_or_unlabeled_data_used": False}, indent=2))


if __name__ == "__main__":
    main()
