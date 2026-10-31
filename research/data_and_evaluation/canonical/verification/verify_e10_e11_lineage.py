"""Read-only lineage CLI; no historical validator or scientific source import.

All roots, mode, baseline and trust pins are explicit. No Git/network subprocess
or output file is used. A PASS is only a selected-context evidence check.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def load_support(path, expected_sha256):
    # The caller pins the reviewed support file independently of the catalog.
    if len(expected_sha256) != 64 or any(c not in "0123456789abcdef" for c in expected_sha256):
        raise ValueError("invalid support digest")
    p = Path(path)
    if not p.is_absolute():
        raise ValueError("explicit absolute support path required")
    for parent in (p, *p.parents):
        if parent.is_symlink() or (parent.exists() and getattr(parent.lstat(), "st_file_attributes", 0) & 1024):
            raise ValueError("support reparse path rejected")
    raw = p.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("support pin mismatch")
    name = "_shroom_context_" + expected_sha256
    if name in sys.modules:
        raise ValueError("support module identity already loaded; use a fresh process")
    spec = importlib.util.spec_from_file_location(name, p)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        # Compile the exact authenticated bytes, never a path-loaded .pyc.
        exec(compile(raw, str(p), "exec"), module.__dict__)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def parser():
    p = argparse.ArgumentParser(description="Read-only H0/H1/H2 byte/context diagnostics; no runtime certification.")
    p.add_argument("--support", required=True)
    p.add_argument("--support-sha256", required=True)
    p.add_argument("--catalog", required=True)
    p.add_argument("--catalog-sha256", required=True)
    p.add_argument("--root", required=True)
    p.add_argument("--baseline-commit", required=True)
    p.add_argument("--baseline-tree", required=True)
    p.add_argument("--mode", choices=("H0_REPLAY", "H1_SNAPSHOT", "H2_CURRENT"), required=True)
    selection = p.add_mutually_exclusive_group(required=True)
    selection.add_argument("--contract")
    selection.add_argument("--artifact", action="append")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        context = load_support(args.support, args.support_sha256)
        catalog = context.load_catalog(args.catalog, expected_sha256=args.catalog_sha256)
        evidence = context.FileEvidence(args.root, mode=args.mode,
                                        baseline_commit=args.baseline_commit,
                                        baseline_tree=args.baseline_tree)
        if args.contract:
            result = context.verify_contract(catalog, args.contract, mode=args.mode, evidence=evidence)
        else:
            if len(set(args.artifact)) != len(args.artifact):
                raise ValueError("duplicate selected artifact")
            checks = [context.verify_artifact(catalog, name, mode=args.mode, evidence=evidence)
                      for name in args.artifact]
            result = {"mode": args.mode, "status": context.combine(checks),
                      "checks": [c.as_dict() for c in checks],
                      "counts": {s: sum(c.status == s for c in checks)
                                 for s in ("PASS", "FAIL", "MISSING", "NOT VERIFIED")},
                      "runtime_status": "NOT VERIFIED", "execution_permitted": False}
    except (ValueError, OSError, TypeError, UnicodeError):
        result = {"status": "FAIL", "reason": "INVALID_DECLARATION_OR_EVIDENCE",
                  "runtime_status": "NOT VERIFIED", "execution_permitted": False}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
