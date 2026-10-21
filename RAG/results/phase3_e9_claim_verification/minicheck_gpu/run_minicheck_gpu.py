"""Explicit opt-in GPU execution; fixed official whole-claim MiniCheck/vLLM path."""
import argparse
import importlib.metadata as metadata
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch
from gpu_common import (HERE, MODEL, REVISION, COMMIT, SETTINGS, require, sha,
                        read, write, validate_inputs, output_metadata, validate_outputs)

class Blocked(RuntimeError):
    pass

def gate(ok, reason):
    if not ok:
        raise Blocked(reason)

def preflight(m, report):
    report['device'] = dict(platform=platform.platform(), python=sys.version)
    gate(platform.system() == 'Linux' and platform.machine() == 'x86_64', 'Linux x86_64 required')
    gate(sys.version_info[:2] == (3, 11), 'Use a clean Python 3.11 environment')
    versions = {}
    for name, version in m['dependency_versions'].items():
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            raise Blocked('Missing dependency: ' + name)
        gate(versions[name].split('+')[0] == version, 'Dependency version mismatch: ' + name)
    report['dependencies'] = versions
    airports = metadata.distribution('pyairports').read_text('direct_url.json')
    from gpu_common import loads
    gate(airports is not None and loads(airports).get('vcs_info', {}).get('commit_id') ==
         '9699eae8c6b03c97239018dea92e01daa8594936', 'Historical pyairports source pin mismatch')
    checked = subprocess.run([sys.executable, '-m', 'pip', 'check'], capture_output=True, text=True)
    gate(checked.returncode == 0, 'pip check failed: ' + checked.stdout + checked.stderr)
    dist = metadata.distribution('minicheck')
    direct = dist.read_text('direct_url.json')
    from gpu_common import loads
    gate(direct is not None and loads(direct).get('vcs_info', {}).get('commit_id') == COMMIT,
         'MiniCheck must be installed from the pinned official Git commit')
    for name, expected in m['official_source_sha256'].items():
        gate(sha(dist.locate_file('minicheck/' + name)) == expected, 'MiniCheck source mismatch: ' + name)
    import torch
    report['device'].update(torch=torch.__version__, torch_cuda=torch.version.cuda,
                            cuda_available=torch.cuda.is_available())
    gate(torch.version.cuda == '12.1' and torch.cuda.is_available(), 'CUDA 12.1 PyTorch build and working CUDA GPU required')
    gate(torch.cuda.device_count() == 1, 'Expose exactly one GPU with CUDA_VISIBLE_DEVICES=0')
    prop = torch.cuda.get_device_properties(0)
    free, total = torch.cuda.mem_get_info(0)
    report['device'].update(name=prop.name, total_vram_bytes=total, free_vram_bytes=free,
                            compute_capability=list(torch.cuda.get_device_capability(0)))
    driver = subprocess.run(['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader'],
                            capture_output=True, text=True)
    gate(driver.returncode == 0, 'Cannot query NVIDIA driver')
    report['device']['nvidia_driver'] = driver.stdout.strip()
    gate(prop.major >= 8 and torch.cuda.is_bf16_supported(), 'BF16 requires NVIDIA compute capability >= 8.0; no FP16 fallback')
    gate(total >= 39 * 1024**3 and free >= 35 * 1024**3,
         'Preparation safety gate: >=39 GiB total and >=35 GiB free VRAM; use A100 40/80GB or equivalent')
    import psutil
    report['device']['available_ram_bytes'] = psutil.virtual_memory().available
    gate(psutil.virtual_memory().available >= 24 * 1024**3, 'At least 24 GiB available host RAM required')
    try:
        value = torch.ones(8, device='cuda', dtype=torch.bfloat16)
        gate(float((value @ value).item()) == 8, 'CUDA BF16 kernel check failed')
        torch.cuda.synchronize()
        del value
        torch.cuda.empty_cache()
        import vllm
        from minicheck.minicheck import MiniCheck
        import nltk
        nltk.data.path.insert(0, str(HERE / 'nltk_data'))
        gate(nltk.sent_tokenize('One sentence. Another sentence.') == ['One sentence.', 'Another sentence.'], 'NLTK resource check')
    except Exception as exc:
        raise Blocked('CUDA/backend dependency import check failed: ' + str(exc)) from exc

def load_scorer(cache_dir):
    import torch
    import vllm
    from minicheck.minicheck import MiniCheck
    original = vllm.LLM

    def pinned_llm(**kwargs):
        # Upstream exposes no revision argument. Add revision pins at the engine
        # construction boundary only; all prompt/chunk/scoring code is untouched.
        require(kwargs['model'] == MODEL and kwargs['dtype'] == torch.bfloat16, 'official engine identity')
        require(kwargs['max_model_len'] == 32768 and kwargs['seed'] == 2024 and
                kwargs['tensor_parallel_size'] == 1 and kwargs['enable_prefix_caching'] is False,
                'official engine settings drift')
        return original(**kwargs, revision=REVISION, tokenizer_revision=REVISION,
                        code_revision=REVISION, quantization=None, device='cuda',
                        gpu_memory_utilization=0.9, cpu_offload_gb=0, kv_cache_dtype='auto')

    with patch.object(vllm, 'LLM', pinned_llm):
        scorer = MiniCheck(model_name='Bespoke-MiniCheck-7B', max_model_len=32768,
                          tensor_parallel_size=1, max_tokens=1, enable_prefix_caching=False,
                          cache_dir=str(cache_dir))
    cfg = scorer.model.llm.llm_engine.model_config
    require(cfg.model == MODEL and cfg.revision == REVISION and cfg.tokenizer_revision == REVISION,
            'loaded checkpoint identity')
    require(cfg.dtype == torch.bfloat16 and cfg.quantization is None, 'loaded precision/quantization')
    require(getattr(cfg.hf_config, 'quantization_config', None) is None, 'quantized checkpoint prohibited')
    return scorer

def execute(destination, run, cache_dir):
    # Exclusive directories prevent accidental overwrite or mixing of runs.
    destination.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    report = dict(status='BLOCKED', model_id=MODEL, model_revision=REVISION,
                  model_loaded=False, claims_processed=0, inference_errors=[], retries=0,
                  output_sha256=None, settings=SETTINGS, device={}, reason='',
                  manifest_sha256=sha(HERE / 'GPU_RUN_MANIFEST.json'))
    phase = 'preflight'
    output = destination / 'minicheck_scores.jsonl'
    try:
        m, inputs = validate_inputs()
        preflight(m, report)
        gate(run, 'Preflight passed; inference requires --run')
        cache_dir.mkdir(parents=True, exist_ok=True)
        import shutil
        gate(shutil.disk_usage(cache_dir).free >= 35 * 1024**3, 'At least 35 GiB free model-cache disk required')
        phase = 'model loading'
        scorer = load_scorer(cache_dir)
        report['model_loaded'] = True
        phase = 'inference'
        partial = destination / 'minicheck_scores.partial.jsonl'
        import json
        import math
        with partial.open('x', encoding='utf-8', newline='\n') as f:
            for offset in range(0, len(inputs), SETTINGS['batch_claims']):
                batch = inputs[offset:offset + SETTINGS['batch_claims']]
                _, probabilities, _, _ = scorer.score(
                    docs=[r['reference_text'] for r in batch],
                    claims=[r['claim_text'] for r in batch], chunk_size=32468)
                require(len(probabilities) == len(batch), 'backend output length')
                for r, p in zip(batch, probabilities):
                    p = float(p)
                    require(math.isfinite(p) and 0 <= p <= 1, 'backend probability')
                    out = dict(canonical_id=r['canonical_id'], claim_index=r['claim_index'],
                               support_probability=p, model_id=MODEL, inference_metadata=output_metadata(m, r))
                    f.write(json.dumps(out, ensure_ascii=False, allow_nan=False) + '\n')
                    report['claims_processed'] += 1
                f.flush()
                os.fsync(f.fileno())
                print(f"Claims processed: {report['claims_processed']}/575", flush=True)
        validate_outputs(partial)
        partial.rename(output)
        report.update(status='PASS', output_sha256=sha(output), reason='All frozen claims scored and validated')
    except Blocked as exc:
        report['reason'] = str(exc)
    except Exception as exc:
        report['status'] = 'BLOCKED' if phase in ('preflight', 'model loading') else 'FAIL'
        report['reason'] = f'{phase}: {type(exc).__name__}: {exc}'
        if phase == 'inference':
            report['inference_errors'].append(report['reason'])
    finally:
        report['elapsed_seconds'] = time.monotonic() - started
        write(destination / 'MINICHECK_GPU_REPORT.json', report)
        with (destination / 'MINICHECK_GPU_REPORT.md').open('x', encoding='utf-8') as f:
            f.write('# MiniCheck GPU report\n\n```json\n')
            import json
            f.write(json.dumps(report, indent=2, ensure_ascii=False))
            f.write('\n```\n')
        freeze = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], capture_output=True, text=True)
        (destination / 'environment_freeze.txt').write_text(freeze.stdout, encoding='utf-8')
    print(report['status'] + ': ' + report['reason'])
    return 0 if report['status'] == 'PASS' else (2 if report['status'] == 'BLOCKED' else 1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', help='Explicitly authorize model download and scoring')
    parser.add_argument('--output-dir', type=Path, required=True, help='New directory; never overwritten')
    parser.add_argument('--cache-dir', type=Path, default=Path.home() / '.cache/e9_minicheck')
    args = parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    os.environ['VLLM_ATTENTION_BACKEND'] = 'FLASH_ATTN'
    os.environ['VLLM_NO_USAGE_STATS'] = '1'
    os.environ['DO_NOT_TRACK'] = '1'
    sys.exit(execute(args.output_dir, args.run, args.cache_dir))
