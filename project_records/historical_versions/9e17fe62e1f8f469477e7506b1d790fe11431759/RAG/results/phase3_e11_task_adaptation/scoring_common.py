"""Label-blind E11-B scoring contracts and durable per-detector score store."""

from __future__ import annotations

import hashlib
import json
import math
import os
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FROZEN_PROTOCOL_CONTENT_SHA = "c0645ef01f885ef22b7abaf5634f8a62d66a3e7174cb0d07aa2a47fba425a5ac"
FROZEN_PROTOCOL_FILE_SHA = "02bf948ec4a833588fe4f01a9bd745f9a409124538e704a34dffe53cf3348a7c"
POLICY = {"DM": "tgt", "MT": "tgt", "PG": "src"}
SCORING_FIELDS = {"sample_key", "task", "reference_text", "whole_hypothesis"}
FORBIDDEN_FIELDS = {"label", "labels", "label_bin", "gold", "p(H)", "p(Hallucination)",
                    "p_hallucination", "prediction", "pseudo_label"}
SCORE_FIELDS = {
    "factcg": ("factcg_support_probability",),
    "minicheck": ("minicheck_support_probability",),
    "hhem": ("hhem_ref_hyp_consistency",),
    "nli": ("nli_ref_hyp_entailment", "nli_ref_hyp_neutral", "nli_ref_hyp_contradiction"),
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def strict_json(text: str):
    def unique(items):
        value = {}
        for name, item in items:
            require(name not in value, "duplicate JSON field: " + name)
            value[name] = item
        return value

    return json.loads(text, object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(
                          ValueError("nonfinite JSON: " + value)))


def protocol() -> dict:
    path = HERE / "E11_TEACHER_PROTOCOL.json"
    require(sha_file(path) == FROZEN_PROTOCOL_FILE_SHA, "frozen protocol file changed")
    value = strict_json(path.read_text(encoding="utf-8"))
    content = {name: part for name, part in value.items() if name != "protocol_sha256"}
    require(sha_bytes(json_bytes(content)) == FROZEN_PROTOCOL_CONTENT_SHA ==
            value["protocol_sha256"], "frozen protocol content changed")
    require(value["reference_policy"] == POLICY, "reference policy changed")
    return value


def normalize(value: object) -> str:
    if value is None:
        text = ""
    elif isinstance(value, (list, dict)):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        text = str(value)
    return " ".join(unicodedata.normalize("NFC", text).strip().split())


def hash_parts(*parts: object) -> str:
    return sha_bytes("\u241f".join(normalize(part) for part in parts).encode("utf-8"))


def reference(row: dict) -> str:
    task = row["task"]
    require(task in POLICY, "invalid task")
    value = row[POLICY[task]]
    require(isinstance(value, str) and bool(value.strip()), "empty reference")
    return value


def text_keys(row: dict) -> dict[str, str]:
    return {"full": hash_parts(row["task"], row["src"], row["tgt"], row["hyp"]),
            "hyp": hash_parts(row["hyp"]),
            "task_ref": hash_parts(row["task"], reference(row)),
            "pair": hash_parts(row["task"], row["src"], row["tgt"])}


def scoring_row(row: dict) -> dict:
    # Extra source/provenance fields on master rows never reach a detector.
    require(not (FORBIDDEN_FIELDS & row.keys()), "leaky scoring source row")
    chosen = {"sample_key": row["sample_key"], "task": row["task"],
              "reference_text": row["reference_text"],
              "whole_hypothesis": row["whole_hypothesis"]}
    require(set(chosen) == SCORING_FIELDS and chosen["task"] in POLICY,
            "invalid scoring fields/task")
    require(isinstance(chosen["sample_key"], str) and chosen["sample_key"],
            "invalid sample key")
    require(all(isinstance(chosen[name], str) and chosen[name].strip()
                for name in ("reference_text", "whole_hypothesis")), "empty scoring text")
    return chosen


def scoring_digest(row: dict) -> str:
    return sha_bytes(json_bytes(scoring_row(row)))


def read_jsonl(path: Path) -> list[dict]:
    with Path(path).open(encoding="utf-8") as handle:
        return [strict_json(line) for line in handle if line.strip()]


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    temp = path.with_name(path.name + ".tmp")
    with temp.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    temp.replace(path)


def validate_record(record: dict, detector: str, source: dict, model_id: str,
                    revision: str) -> None:
    require(detector in SCORE_FIELDS, "unknown detector")
    names = SCORE_FIELDS[detector]
    require(set(record) == {"sample_key", "input_sha256", "detector", "model_id",
                            "revision", *names}, "score record field allowlist")
    require(record["sample_key"] == source["sample_key"], "score sample key mismatch")
    require(record["input_sha256"] == scoring_digest(source), "score input digest mismatch")
    require((record["detector"], record["model_id"], record["revision"]) ==
            (detector, model_id, revision), "score model provenance mismatch")
    for name in names:
        number = record[name]
        require(type(number) in (float, int) and math.isfinite(number) and
                0 <= number <= 1, "score out of range: " + name)
    if detector == "nli":
        require(abs(sum(record[name] for name in names) - 1) <= 2e-6,
                "NLI probabilities do not sum to 1")


class ScoreStore:
    """Append-only score journal; bad/duplicate/foreign rows fail closed on resume."""

    def __init__(self, folder: Path, detector: str, universe: list[dict],
                 model_id: str, revision: str, universe_sha256: str):
        require(detector in SCORE_FIELDS, "unknown detector")
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.detector, self.model_id, self.revision = detector, model_id, revision
        self.universe_sha256 = universe_sha256
        self.sources = {}
        for row in universe:
            source = scoring_row(row)
            require(source["sample_key"] not in self.sources, "duplicate input key")
            self.sources[source["sample_key"]] = source
        self.path = self.folder / "scores.jsonl"
        self.rows = {}
        manifest_path = self.folder / "manifest.json"
        require(manifest_path.exists() or not self.path.exists(),
                "score journal without prior manifest")
        if self.path.exists():
            with self.path.open("rb") as handle:
                lines = handle.readlines()
            require(all(line.endswith(b"\n") and line.strip() for line in lines),
                    "corrupt/incomplete score JSONL line")
            for line in lines:
                record = strict_json(line.decode("utf-8"))
                key = record["sample_key"]
                require(key in self.sources, "foreign score key")
                require(key not in self.rows, "duplicate score key")
                validate_record(record, detector, self.sources[key], model_id, revision)
                self.rows[key] = record
        if manifest_path.exists():
            manifest = strict_json(manifest_path.read_text(encoding="utf-8"))
            require(manifest["detector"] == detector and
                    manifest["universe_sha256"] == universe_sha256 and
                    manifest["model_id"] == model_id and manifest["revision"] == revision and
                    manifest["protocol_sha256"] == FROZEN_PROTOCOL_CONTENT_SHA,
                    "score store manifest mismatch")
            prior = manifest["completed_rows"]
            require(type(prior) is int and 0 <= prior <= len(self.rows),
                    "invalid score checkpoint count")
            if prior:
                require(sha_bytes(b"".join(lines[:prior])) == manifest["scores_sha256"],
                        "checkpointed score prefix corrupted")
            else:
                require(manifest["scores_sha256"] is None, "empty checkpoint SHA mismatch")
            if prior < len(self.rows):
                self.checkpoint()  # Valid appended tail after interrupted checkpoint.
        else:
            self.checkpoint()  # Establish a durable empty checkpoint before first append.

    def append(self, records: list[dict]) -> None:
        require(records, "empty score batch")
        pending = {}
        for record in records:
            key = record["sample_key"]
            require(key in self.sources, "foreign score key")
            require(key not in self.rows and key not in pending, "duplicate score key")
            validate_record(record, self.detector, self.sources[key],
                            self.model_id, self.revision)
            pending[key] = record
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self.rows.update(pending)
        self.checkpoint()

    def checkpoint(self) -> None:
        atomic_json(self.folder / "manifest.json", {
            "schema_version": 1, "detector": self.detector,
            "model_id": self.model_id, "revision": self.revision,
            "protocol_sha256": FROZEN_PROTOCOL_CONTENT_SHA,
            "universe_sha256": self.universe_sha256,
            "universe_rows": len(self.sources), "completed_rows": len(self.rows),
            "scores_sha256": sha_file(self.path) if self.path.exists() else None,
        })

    def missing(self, requested: list[dict]) -> list[dict]:
        wanted = [scoring_row(row) for row in requested]
        require(len({row["sample_key"] for row in wanted}) == len(wanted),
                "duplicate requested key")
        require(all(row["sample_key"] in self.sources and
                    row == self.sources[row["sample_key"]] for row in wanted),
                "requested row not in score universe")
        return [row for row in wanted if row["sample_key"] not in self.rows]

    def validate_scope(self, requested: list[dict]) -> dict:
        missing = self.missing(requested)
        require(not missing, f"missing score rows: {len(missing)}")
        return {"detector": self.detector, "status": "PASS", "requested_rows": len(requested),
                "store_rows": len(self.rows), "scores_sha256": sha_file(self.path)}
