"""Read-only H0/H1/H2 evidence checks and pure execution-path planning.

H0 is the original identity asserted by frozen records. H1 is the pinned public
snapshot, which can differ from H0. H2 is a separately reviewed adapted source.
PASS below certifies the selected byte/context check, never experiment execution.
No project sources, models, Git subprocesses or network clients are imported.
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

SCHEMA = "shroom-canonical-lineage-v1"
MODES = frozenset({"H0_REPLAY", "H1_SNAPSHOT", "H2_CURRENT"})
ROLES = frozenset({"source_historical", "record_public_historical", "input_original"})
DEFINITIONS = {
    "H0": "the original experimental artifact identities stated in frozen records. Some actual original inputs/metadata are not in the public checkout. An expected hash is a claim to check, not evidence that the file is available.",
    "H1": "public Git baseline 11822d92070cd29360445cb4dacd8d110c655248, with tree 81690aef257042354b6886f145919ae794e941ee. It authenticates exact published source/record bytes at their historical paths.",
    "H2": "a future reviewed current-layout implementation. It does not exist yet for the two canonical sources. Its full-file hashes must be measured after approved adaptation/review, not guessed in a planning report."
}


class ValidationError(ValueError):
    """Invalid or unverifiable declaration; no fallback is permitted."""


@dataclass(frozen=True)
class Check:
    artifact: str
    status: str
    reason: str
    mode: str
    expected_sha256: str | None = None
    actual_sha256: str | None = None

    def as_dict(self):
        return dict(self.__dict__)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def git_blob_id(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def strict_json(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValidationError("duplicate JSON key")
            result[key] = value
        return result

    def invalid(_):
        raise ValidationError("nonfinite JSON value")

    def number(text):
        value = float(text)
        if not math.isfinite(value):
            raise ValidationError("nonfinite JSON number")
        return value

    try:
        return json.loads(text, object_pairs_hook=unique, parse_constant=invalid, parse_float=number)
    except (json.JSONDecodeError, TypeError) as error:
        raise ValidationError("invalid JSON") from error


def keys(value, required, optional=()):
    if not isinstance(value, dict) or set(value) - (set(required) | set(optional)) or not set(required) <= set(value):
        raise ValidationError("unknown or missing schema field")


def digest(value, length=64):
    if not isinstance(value, str) or re.fullmatch("[0-9a-f]{" + str(length) + "}", value) is None:
        raise ValidationError("invalid digest")
    return value


def logical_path(value):
    if (not isinstance(value, str) or not value or "\\" in value
            or "\0" in value or ":" in value or value.startswith("/")
            or any(part in ("", ".", "..") for part in value.split("/"))
            or any(part.rstrip(". ") != part for part in value.split("/"))
            or any(part.casefold() in (".git", ".hg", ".svn") for part in value.split("/"))):
        raise ValidationError("unsafe logical path")
    for part in value.split("/"):
        if (any(ord(ch) < 32 or ch in '<>"|?*' for ch in part)
                or re.fullmatch(r"(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])", part.split(".")[0])):
            raise ValidationError("unsafe platform path component")
    return PurePosixPath(value).as_posix()


def symbols(value):
    if not isinstance(value, dict):
        raise ValidationError("invalid symbol map")
    for name, expected in value.items():
        if not isinstance(name, str) or re.fullmatch(r"[A-Za-z_]\w*", name) is None:
            raise ValidationError("invalid symbol")
        digest(expected)
    return value


def validate_catalog(value):
    keys(value, ("schema_version", "baseline", "definitions", "artifacts", "contracts",
                 "evidence_sources", "runtime_status"))
    if value["schema_version"] != SCHEMA or value["definitions"] != DEFINITIONS:
        raise ValidationError("unknown schema or changed lineage definitions")
    if value["runtime_status"] != "NOT VERIFIED":
        raise ValidationError("catalog cannot certify runtime")
    keys(value["baseline"], ("commit", "tree"))
    digest(value["baseline"]["commit"], 40)
    digest(value["baseline"]["tree"], 40)
    if not isinstance(value["artifacts"], list) or not value["artifacts"]:
        raise ValidationError("empty artifact catalog")
    ids, paths, targets = set(), set(), set()
    for entry in value["artifacts"]:
        keys(entry, ("id", "role", "historical_path", "target_path", "h1", "current", "symbols"))
        name = entry["id"]
        if not isinstance(name, str) or re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", name) is None or name in ids:
            raise ValidationError("invalid or duplicate logical identity")
        ids.add(name)
        path = logical_path(entry["historical_path"])
        if path.casefold() in paths:
            raise ValidationError("duplicate historical path")
        paths.add(path.casefold())
        if entry["role"] not in ROLES:
            raise ValidationError("unknown role")
        target = entry["target_path"]
        if target is not None:
            target = logical_path(target)
            if target.casefold() in targets or target.casefold() == path.casefold():
                raise ValidationError("duplicate target or historical path reused as H2")
            targets.add(target.casefold())
        h1 = entry["h1"]
        if h1 is not None:
            keys(h1, ("sha256", "git_blob", "size_bytes"))
            digest(h1["sha256"]); digest(h1["git_blob"], 40)
            if type(h1["size_bytes"]) is not int or h1["size_bytes"] < 0:
                raise ValidationError("invalid size")
        symbols(entry["symbols"])
        current = entry["current"]
        keys(current, ("status", "role", "sha256", "review_id", "symbols"))
        if current["role"] != ("source_current" if entry["role"] == "source_historical" else entry["role"]):
            raise ValidationError("current role substitution")
        symbols(current["symbols"])
        if current["status"] == "UNIMPLEMENTED":
            if any(current[k] is not None for k in ("sha256", "review_id")) or current["symbols"]:
                raise ValidationError("unimplemented source cannot carry invented approval")
        elif current["status"] == "REVIEWED":
            digest(current["sha256"])
            if target is None or not isinstance(current["review_id"], str) or not current["review_id"].strip():
                raise ValidationError("reviewed target needs independent review reference")
            if current["symbols"] != entry["symbols"]:
                raise ValidationError("scientific symbol lineage was changed")
            if entry["role"] != "source_historical" and (h1 is None or current["sha256"] != h1["sha256"]):
                raise ValidationError("historical record cannot be relabeled as adapted input")
        else:
            raise ValidationError("unknown current implementation state")
    if targets & paths:
        raise ValidationError("current target collides with a historical identity")
    if not isinstance(value["contracts"], dict) or not value["contracts"]:
        raise ValidationError("missing contracts")
    for name, contract in value["contracts"].items():
        if not isinstance(name, str) or re.fullmatch(r"[A-Z][A-Z0-9_]*", name) is None:
            raise ValidationError("invalid contract name")
        if not isinstance(contract, list) or not contract:
            raise ValidationError("empty contract")
        seen = set()
        for requirement in contract:
            keys(requirement, ("artifact_id", "expected_sha256"))
            identity = requirement["artifact_id"]
            if identity not in ids or identity in seen:
                raise ValidationError("unknown/duplicate contract identity")
            seen.add(identity); digest(requirement["expected_sha256"])
    if not isinstance(value["evidence_sources"], list):
        raise ValidationError("invalid evidence source ledger")
    for evidence in value["evidence_sources"]:
        keys(evidence, ("path", "sha256"))
        logical_path(evidence["path"]); digest(evidence["sha256"])
    return value


def load_catalog(path, *, expected_sha256):
    """Trust is the caller's independent pin, not a digest inside the registry."""
    digest(expected_sha256)
    reject_links(Path(path))
    raw = Path(path).read_bytes()
    if sha256(raw) != expected_sha256:
        raise ValidationError("catalog pin mismatch")
    return validate_catalog(strict_json(raw.decode("utf-8")))


def reject_links(path):
    p = Path(path)
    if not p.is_absolute():
        raise ValidationError("physical path must be explicit and absolute")
    if ".." in p.parts or p.drive.startswith("\\\\"):
        raise ValidationError("physical traversal or UNC/device root rejected")
    for item in (p, *p.parents):
        try:
            info = item.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 1024:
            raise ValidationError("symlink/reparse path rejected")
    return p


def confined(root, relative):
    root = reject_links(Path(root))
    if not root.is_dir():
        raise ValidationError("evidence root is missing")
    rel = logical_path(relative)
    target = reject_links(root.joinpath(*rel.split("/")))
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValidationError("path escapes explicit root")
    return target


class FileEvidence:
    """An explicitly declared materialized context, never an implicit CWD search."""

    def __init__(self, root, *, mode, baseline_commit, baseline_tree):
        if mode not in MODES:
            raise ValidationError("unknown execution context")
        self.root = reject_links(Path(root))
        if not self.root.is_dir():
            raise ValidationError("missing evidence root")
        self.mode = mode
        self.baseline_commit = digest(baseline_commit, 40)
        self.baseline_tree = digest(baseline_tree, 40)

    def read(self, relative):
        p = confined(self.root, relative)
        try:
            info = p.stat()
        except FileNotFoundError:
            return None
        if not stat.S_ISREG(info.st_mode):
            raise ValidationError("artifact is not a regular file")
        return p.read_bytes()


def source_symbols(raw):
    """Parse source only; never execute/import a historical or adapted module."""
    try:
        text = raw.decode("utf-8")
        tree = ast.parse(text)
    except (UnicodeDecodeError, SyntaxError) as error:
        raise ValidationError("invalid source syntax") from error
    found = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in found:
                raise ValidationError("duplicate top-level symbol")
            found[node.name] = sha256(ast.get_source_segment(text, node).encode("utf-8"))
    return found


def verify_artifact(catalog, identity, *, mode, evidence, presented_path=None, expected_h0=None):
    """Return a byte/context result. Runtime and algorithm equivalence are separate."""
    try:
        validate_catalog(catalog)
        if mode not in MODES or evidence.mode != mode:
            raise ValidationError("wrong execution context")
        if (evidence.baseline_commit != catalog["baseline"]["commit"]
                or evidence.baseline_tree != catalog["baseline"]["tree"]):
            raise ValidationError("unverified baseline identity")
        entries = {item["id"]: item for item in catalog["artifacts"]}
        if identity not in entries:
            raise ValidationError("unknown artifact")
        item = entries[identity]
        relative = item["target_path"] if mode == "H2_CURRENT" else item["historical_path"]
        if presented_path is not None and logical_path(presented_path) != relative:
            raise ValidationError("unexpected artifact path for context")
        if mode == "H2_CURRENT":
            if relative is None or item["current"]["status"] != "REVIEWED":
                return Check(identity, "NOT VERIFIED", "H2_UNIMPLEMENTED", mode)
            expected = item["current"]["sha256"]
        elif mode == "H0_REPLAY":
            expected = digest(expected_h0)
            frozen = {r["expected_sha256"] for contract in catalog["contracts"].values()
                      for r in contract if r["artifact_id"] == identity}
            if expected not in frozen:
                raise ValidationError("H0 expected hash is not in the pinned contract")
        else:
            if item["h1"] is None:
                return Check(identity, "MISSING", "NO_H1_EVIDENCE", mode)
            expected = item["h1"]["sha256"]
        raw = evidence.read(relative)
        if raw is None:
            return Check(identity, "MISSING", "REQUIRED_ARTIFACT_MISSING", mode, expected)
        actual = sha256(raw)
        if actual != expected:
            return Check(identity, "FAIL", "SHA256_MISMATCH", mode, expected, actual)
        if mode == "H1_SNAPSHOT":
            h1 = item["h1"]
            if len(raw) != h1["size_bytes"] or git_blob_id(raw) != h1["git_blob"]:
                return Check(identity, "FAIL", "H1_OBJECT_IDENTITY_MISMATCH", mode, expected, actual)
        if item["symbols"]:
            found = source_symbols(raw)
            if any(found.get(k) != v for k, v in item["symbols"].items()):
                return Check(identity, "FAIL", "SYMBOL_LINEAGE_MISMATCH", mode, expected, actual)
        return Check(identity, "PASS", "SELECTED_CONTEXT_BYTES_VERIFIED", mode, expected, actual)
    except (ValidationError, OSError, ValueError, TypeError) as error:
        # Do not put physical paths, source text or sensitive values in diagnostics.
        return Check(identity, "FAIL", type(error).__name__ + ": " + str(error).split("\n")[0]
                     if isinstance(error, ValidationError) else "EVIDENCE_READ_ERROR", mode)


def combine(checks):
    states = [c.status for c in checks]
    if not states:
        return "NOT VERIFIED"
    for state in ("FAIL", "MISSING", "NOT VERIFIED"):
        if state in states:
            return state
    return "PASS"


def verify_contract(catalog, contract, *, mode, evidence):
    try:
        validate_catalog(catalog)
        if mode != "H0_REPLAY" or evidence.mode != mode or contract not in catalog["contracts"]:
            raise ValidationError("contract requires explicit H0_REPLAY context")
        checks = [verify_artifact(catalog, req["artifact_id"], mode=mode, evidence=evidence,
                                  expected_h0=req["expected_sha256"])
                  for req in catalog["contracts"][contract]]
    except (ValidationError, TypeError):
        checks = [Check(str(contract), "FAIL", "INVALID_CONTRACT_CONTEXT", str(mode))]
    return {
        "mode": mode, "contract": contract, "status": combine(checks),
        "checks": [c.as_dict() for c in checks],
        "counts": {s: sum(c.status == s for c in checks)
                   for s in ("PASS", "FAIL", "MISSING", "NOT VERIFIED")},
        "runtime_status": "NOT VERIFIED",
        "execution_permitted": False,
    }


def plan_run(run_dir, *, source_roots, input_paths, output_names):
    """Pure validation only. Does not mkdir, touch, open an output or execute code."""
    run = reject_links(Path(run_dir))
    if run.exists() or not run.parent.is_dir():
        raise ValidationError("run must be absent with an existing parent")
    if not source_roots or not input_paths or not output_names:
        raise ValidationError("explicit source/input/output ownership required")
    roots = [reject_links(Path(p)) for p in source_roots]
    if any(not p.is_dir() for p in roots):
        raise ValidationError("source root is missing")
    inputs = [reject_links(Path(p)) for p in input_paths]
    if any(not p.is_file() for p in inputs):
        raise ValidationError("input path is missing or not a file")
    resolved = run.resolve()
    for p in roots:
        if resolved.is_relative_to(p.resolve()) or p.resolve().is_relative_to(resolved):
            raise ValidationError("run/source overlap")
    for p in inputs:
        if p.resolve().is_relative_to(resolved) or resolved.is_relative_to(p.resolve()):
            raise ValidationError("run/input overlap")
    # Even an undeclared Git checkout on the output ancestry is forbidden.
    if any((parent / ".git").exists() for parent in (run, *run.parents)):
        raise ValidationError("run is inside Git")
    names = [logical_path(n) for n in output_names]
    if len({n.casefold() for n in names}) != len(names):
        raise ValidationError("duplicate output path")
    for a in names:
        if any(b != a and b.casefold().startswith(a.casefold() + "/") for b in names):
            raise ValidationError("output file/directory collision")
    return {"run_dir": str(run), "outputs": [str(run.joinpath(*n.split("/"))) for n in names],
            "status": "PASS", "created": False, "execution_permitted": False}
