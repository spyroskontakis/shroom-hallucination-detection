"""Offline simulation of Modal's /root script and /opt/e11 helper layout."""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

import e11_modal
from scoring_common import HERE, require, sha_file


def main() -> dict:
    with tempfile.TemporaryDirectory(prefix="e11-layout-") as scratch:
        root = Path(scratch)
        runtime = root / "opt" / "e11"
        function_dir = root / "root"
        elsewhere = root / "unrelated-working-directory"
        phase3 = root / "opt" / "SHROOM" / "SHROOM2024" / "RAG" / "results" / "phase3_e9_claim_verification"
        models = root / "opt" / "e11_models"
        volume = root / "results"
        for directory in (runtime, function_dir, elsewhere, phase3, models, volume):
            directory.mkdir(parents=True, exist_ok=True)
        for name in e11_modal.E11_IMAGE_FILES:
            shutil.copyfile(HERE / name, runtime / name)
            require(sha_file(runtime / name) == sha_file(HERE / name),
                    "simulated E11 mounted file differs: " + name)
        # Modal independently mounts the function module under /root. In this
        # Windows-only simulation, substitute the temporary /opt/e11 analogue
        # in a COPY of that module; the real source remains unchanged.
        function_source = (HERE / "e11_modal.py").read_text(encoding="utf-8")
        original_root = 'REMOTE_E11 = "/opt/e11"'
        require(function_source.count(original_root) == 1, "remote import root declaration")
        simulated_source = function_source.replace(
            original_root, "REMOTE_E11 = " + repr(str(runtime)))
        (function_dir / "e11_modal.py").write_text(simulated_source, encoding="utf-8")
        for stage in ("minicheck_gpu", "factcg_gpu"):
            (phase3 / f"{stage}_portable.zip").touch()
            (phase3 / stage).mkdir()
            for filename in e11_modal.FROZEN_PACKAGE_FILES[stage]:
                (phase3 / stage / filename).touch()
        for name, filenames in e11_modal.MODEL_ASSETS.items():
            (models / name).mkdir()
            for filename in filenames:
                (models / name / filename).touch()

        # Python starts outside both source directories and imports helpers
        # only after adding the explicitly configured remote helper directory.
        code = "\n".join([
            "import json, pathlib, sys",
            f"module_dir = pathlib.Path({str(runtime)!r})",
            "sys.path.insert(0, str(module_dir))",
            "import scoring_common, detector_adapters, run_detector",
            "for module in (scoring_common, detector_adapters, run_detector):",
            "    assert pathlib.Path(module.__file__).resolve().parent == module_dir.resolve()",
            "assert scoring_common.protocol()['status'] == 'FROZEN_BEFORE_PSEUDO_LABEL_GENERATION'",
            "print(json.dumps({'status':'PASS','modules':3,'cwd':str(pathlib.Path.cwd()),'module_root':str(module_dir)}))",
        ])
        process = subprocess.run([sys.executable, "-I", "-B", "-c", code],
                                 cwd=elsewhere, capture_output=True, text=True)
        require(process.returncode == 0,
                "independent-CWD import failed: " + process.stdout + process.stderr)
        imported = json.loads(process.stdout.strip())
        require(imported["cwd"] == str(elsewhere) and imported["modules"] == 3,
                "import CWD contract")

        hydrate = "\n".join([
            "import json, pathlib, sys, modal",
            "modal.is_local = lambda: False",
            f"sys.path.insert(0, {str(function_dir)!r})",
            "import e11_modal",
            f"expected = pathlib.Path({str(runtime)!r}).resolve()",
            "assert pathlib.Path(e11_modal.__file__).resolve().parent != expected",
            "assert pathlib.Path(e11_modal.HERE).resolve() == expected",
            "assert pathlib.Path(e11_modal._module_dir).resolve() == expected",
            "print(json.dumps({'status':'PASS','hydrated_from':str(pathlib.Path(e11_modal.__file__).parent),'helpers_from':str(expected)}))",
        ])
        hydrated = subprocess.run([sys.executable, "-B", "-c", hydrate],
                                  cwd=elsewhere, capture_output=True, text=True)
        require(hydrated.returncode == 0,
                "simulated Modal hydration failed: " + hydrated.stdout + hydrated.stderr)
        hydrate_result = json.loads(hydrated.stdout.strip())
        require(hydrate_result["status"] == "PASS", "hydration status")

        e11_modal.verify_remote_layout(runtime, phase3, models, volume)
        (runtime / "scoring_common.py").unlink()
        with contextlib.redirect_stdout(io.StringIO()) as diagnostic:
            try:
                e11_modal.verify_remote_layout(runtime, phase3, models, volume)
            except RuntimeError as exc:
                require("E11_LAYOUT_FAIL" in str(exc) and
                        "scoring_common.py" in str(exc), "missing-module diagnostic")
            else:
                raise AssertionError("missing-module check did not fail")
        require("E11_LAYOUT_FAIL" in diagnostic.getvalue(), "layout failure not printed")

        frozen_factcg = PurePosixPath(e11_modal.REMOTE_PHASE3) / "factcg_gpu" / "factcg_common.py"
        require(str(frozen_factcg.parents[3]) == "/opt/SHROOM/SHROOM2024/RAG",
                "frozen FactCG parent-depth layout")
        require(e11_modal.REMOTE_E11 == "/opt/e11" and
                e11_modal.REMOTE_OUTPUT == "/results/e11", "remote root drift")
        for detector in ("factcg", "minicheck", "hhem", "nli"):
            benchmark = e11_modal.stage_command(detector, "benchmark")
            full = e11_modal.stage_command(detector, "full")
            require("--full-run" not in benchmark and "--full-run" in full,
                    "benchmark/full execution guard")
            require("/opt/e11/run_detector.py" in benchmark,
                    "detector subprocess module path")

        return {"status": "PASS", "imports_from_other_cwd": 3,
                "function_hydration_from_separate_directory": "PASS",
                "synthetic_layout_preflight": "PASS",
                "missing_module_diagnostic": "PASS",
                "factcg_parent_depth": "PASS",
                "benchmark_full_guard": "PASS",
                "modal_job_started": False}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
