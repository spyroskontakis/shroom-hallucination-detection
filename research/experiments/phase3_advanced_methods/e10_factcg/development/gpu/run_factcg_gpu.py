"""Frozen GPU-only FactCG extraction. Requires --run to load weights."""
import argparse
import importlib.metadata as metadata
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from factcg_common import (HERE, MODEL, REVISION, SETTINGS, require, sha, write,
                           validate_inputs, validate_outputs, row_metadata)

class Blocked(RuntimeError):
    pass

def gate(ok, reason):
    if not ok:
        raise Blocked(reason)

def preflight(m, report):
    report['device'] = dict(platform=platform.platform(), python=sys.version)
    gate(platform.system() == 'Linux' and platform.machine() == 'x86_64', 'Linux x86_64 required')
    gate(sys.version_info[:2] == (3, 11), 'Python 3.11 required')
    versions = {}
    for name, expected in m['dependency_versions'].items():
        try:
            versions[name] = metadata.version(name).split('+')[0]
        except metadata.PackageNotFoundError as exc:
            raise Blocked('Missing dependency: ' + name) from exc
        gate(versions[name] == expected, 'Dependency mismatch: ' + name)
    report['dependencies'] = versions
    check = subprocess.run([sys.executable, '-m', 'pip', 'check'], capture_output=True, text=True)
    gate(check.returncode == 0, 'pip check failed: ' + check.stdout + check.stderr)
    import torch
    report['device'].update(torch=torch.__version__, torch_cuda=torch.version.cuda,
                            cuda_available=torch.cuda.is_available())
    gate(torch.version.cuda == '12.1' and torch.cuda.is_available(), 'Working CUDA 12.1 PyTorch required; CPU fallback prohibited')
    gate(torch.cuda.device_count() == 1, 'Expose one GPU with CUDA_VISIBLE_DEVICES=0')
    free, total = torch.cuda.mem_get_info()
    report['device'].update(gpu_name=torch.cuda.get_device_name(0), total_vram_bytes=total,
                            free_vram_bytes=free, compute_capability=list(torch.cuda.get_device_capability()))
    gate(total >= 15 * 1024**3 and free >= 12 * 1024**3, 'Conservative FP32 gate: >=15 GiB total / >=12 GiB free VRAM')
    import psutil
    report['device']['available_ram_bytes'] = psutil.virtual_memory().available
    gate(psutil.virtual_memory().available >= 8 * 1024**3, 'At least 8 GiB available host RAM required')
    driver = subprocess.run(['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader'], capture_output=True, text=True)
    gate(driver.returncode == 0, 'NVIDIA driver query failed')
    report['device']['driver'] = driver.stdout.strip()
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.manual_seed(42)
    value = torch.ones(8, device='cuda', dtype=torch.float32)
    gate((value @ value).item() == 8, 'CUDA FP32 kernel check')
    torch.cuda.synchronize()
    del value
    torch.cuda.empty_cache()
    import transformers
    import nltk
    nltk.data.path.insert(0, str(HERE / 'nltk_data'))
    gate(nltk.word_tokenize('A check.') == ['A', 'check', '.'], 'Bundled NLTK resource check')

def execute(destination, run, cache_dir):
    destination.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    report = dict(status='BLOCKED', model_id=MODEL, model_revision=REVISION,
                  manifest_sha256=sha(HERE / 'GPU_RUN_MANIFEST.json'), model_loaded=False,
                  samples_processed=0, inference_errors=[], retries=0, output_sha256=None,
                  settings=SETTINGS, dependencies={}, device={}, truncated_chunks=0,
                  reference_chunks=0, max_untruncated_tokens=0, reason='')
    phase = 'preflight'
    try:
        m, inputs = validate_inputs()
        preflight(m, report)
        gate(run, 'Preflight passed; --run required for download and inference')
        import shutil
        cache_dir.mkdir(parents=True, exist_ok=True)
        gate(shutil.disk_usage(cache_dir).free >= 6 * 1024**3, 'At least 6 GiB free cache disk required')
        phase = 'model loading'
        from factcg_backend import load, score
        tokenizer, model = load(cache_dir)
        report['model_loaded'] = True
        phase = 'inference'
        partial = destination / 'factcg_scores.partial.jsonl'
        with partial.open('x', encoding='utf-8', newline='\n') as f:
            for r in inputs:
                p, audit = score(tokenizer, model, r['reference_text'], r['whole_hypothesis'])
                import math
                require(math.isfinite(p) and 0 <= p <= 1, 'invalid backend probability')
                out = dict(canonical_id=r['canonical_id'], support_probability=p,
                           model_id=MODEL, inference_metadata=row_metadata(m, r))
                f.write(json.dumps(out, ensure_ascii=False, allow_nan=False) + '\n')
                f.flush()
                os.fsync(f.fileno())
                report['samples_processed'] += 1
                report['truncated_chunks'] += audit['truncated_chunks']
                report['reference_chunks'] += audit['reference_chunks']
                report['max_untruncated_tokens'] = max(report['max_untruncated_tokens'], audit['max_untruncated_tokens'])
                if report['samples_processed'] % 25 == 0 or report['samples_processed'] == 561:
                    print(f"FactCG: {report['samples_processed']}/561", flush=True)
        validate_outputs(partial)
        output = destination / 'factcg_scores.jsonl'
        partial.rename(output)
        report.update(status='PASS', output_sha256=sha(output), reason='561 frozen pairs scored and validated')
    except Blocked as exc:
        report['reason'] = str(exc)
    except Exception as exc:
        report['status'] = 'FAIL' if phase == 'inference' else 'BLOCKED'
        report['reason'] = f'{phase}: {type(exc).__name__}: {exc}'
        if phase == 'inference':
            report['inference_errors'].append(report['reason'])
    finally:
        report['elapsed_seconds'] = time.monotonic() - start
        write(destination / 'FACTCG_GPU_REPORT.json', report)
        with (destination / 'FACTCG_GPU_REPORT.md').open('x', encoding='utf-8') as f:
            f.write('# FactCG GPU report\n\n```json\n' + json.dumps(report, indent=2) + '\n```\n')
        frozen = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], capture_output=True, text=True)
        (destination / 'environment_freeze.txt').write_text(frozen.stdout, encoding='utf-8')
    print(report['status'] + ': ' + report['reason'])
    return 0 if report['status'] == 'PASS' else (2 if report['status'] == 'BLOCKED' else 1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--cache-dir', type=Path, default=Path.home() / '.cache/e10_factcg')
    args = parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    sys.exit(execute(args.output_dir, args.run, args.cache_dir))
