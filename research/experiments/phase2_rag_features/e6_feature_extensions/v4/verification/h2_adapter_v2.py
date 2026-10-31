"""Current E6-v4 layout binding over the unchanged, pinned v1 adapter engine.

This version completes the 62-file source layout. Historical v1 remains bound
to its own snapshot. Neither version certifies numerical reproduction.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
from pathlib import Path

VERSION = "shroom-e6-v4-h2-v2"
ENGINE = "research/experiments/phase2_rag_features/e6_feature_extensions/v4/verification/h2_adapter_v1.py"
ENGINE_SHA256 = "b96923c93678e1e81d936b0bb43c672fa7d9b7b94561f63e3901a2c8ba86ae2b"
DEFAULT_CONTRACT = "research/experiments/phase2_rag_features/e6_feature_extensions/v4/configs/current_layout_h2_v2.json"
CONTRACT_SHA256 = "755c9dd55f5d3174f2e266104c9140fecb2d391a8d34f7cde25ec1c05838aee3"


def repository_root(origin=__file__):
    for parent in Path(origin).resolve().parents:
        if (parent / "research/shared_tools/canonical_execution_context.py").is_file() and (parent / "research/README.md").is_file():
            return parent
    raise ValueError("Reviewed source checkout not found")


def implementation(root):
    """Load only the measured engine; change version/layout constants, not code."""
    root = Path(root)
    if not root.is_absolute() or ".." in root.parts:
        raise ValueError("Explicit absolute source root required")
    path = root / ENGINE
    for item in (path, *path.parents):
        if item.is_symlink() or (item.exists() and getattr(item.lstat(), "st_file_attributes", 0) & 1024):
            raise ValueError("Reparse source rejected")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ENGINE_SHA256:
        raise ValueError("Historical adapter engine identity mismatch")
    spec = importlib.util.spec_from_file_location("_e6_v4_current_v2_engine", path)
    engine = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), "exec"), engine.__dict__)
    engine.VERSION = VERSION
    engine.DEFAULT_CONTRACT = DEFAULT_CONTRACT
    return engine


def contract(root, *, expected_sha256=CONTRACT_SHA256):
    if expected_sha256 != CONTRACT_SHA256:
        raise ValueError("Unknown current contract pin")
    engine = implementation(root)
    return engine.Contract(Path(root), Path(root) / DEFAULT_CONTRACT, CONTRACT_SHA256)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--entry", help="Exact historical E6-v4 source identity")
    parser.add_argument("--execute", action="store_true", help="Requires separate scientific execution approval and explicit original/run/temp roots")
    args = parser.parse_args(argv)
    if args.expected_sha256 != CONTRACT_SHA256:
        raise ValueError("Unknown current contract pin")
    root = repository_root()
    engine = implementation(root)
    forwarded = ["--contract", str(root / DEFAULT_CONTRACT), "--expected-sha256", CONTRACT_SHA256]
    if args.entry:
        forwarded += ["--entry", args.entry]
    if args.execute:
        forwarded.append("--execute")
    # The existing engine validates all source/model/input identities, isolated
    # roots, run ownership and audit policy before any scientific entry executes.
    return engine.main(forwarded)


if __name__ == "__main__":
    raise SystemExit(main())
