"""One CPU smoke: two synthetic orientation checks, then exactly 4 DM/4 MT/4 PG.

Only the frozen label-free FactCG input is read. No RF or evaluation imports.
The GPU package is imported read-only for its verified prompt/tokenization helpers.
"""
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import statistics
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
GPU = HERE.parent / 'factcg_gpu'
sys.path.insert(0, str(GPU))
from factcg_common import MODEL, REVISION, require, sha, write, validate_inputs, digest
from factcg_backend import chunk_reference, tokenize

def main():
    started = time.perf_counter()
    write(HERE / 'SMOKE_STARTED.json', dict(model=MODEL, revision=REVISION,
          selected_per_task=4, device='cpu', precision='float32', batch_size=1,
          orientation_minimum_gap=0.25, selection='First four canonical IDs sorted independently within each task',
          recommendation_rule='LOCAL_FULL_RUN if projected warm-cache total <=1800 seconds and minimum available RAM >=1 GiB; otherwise GPU_FULL_RUN'))
    frozen = {str(p): sha(p) for base in [GPU, HERE.parent / 'minicheck_gpu']
              for p in base.rglob('*') if p.is_file()}
    write(HERE / 'FROZEN_PACKAGES_BEFORE.json', frozen)
    report = dict(status='BLOCKED', model_id=MODEL, revision=REVISION, device='cpu', dtype='float32',
                  batch_size=1, model_loaded=False, outputs=0, leakage_check='PENDING',
                  recommendation='GPU_FULL_RUN', reason='', model_load_seconds=None,
                  inference_12_seconds=None, download_seconds=None)
    phase = 'preflight'
    stop = threading.Event()
    monitor = None
    results = []
    try:
        import psutil
        process = psutil.Process()
        memory = dict(peak_sampled_rss_bytes=process.memory_info().rss,
                      minimum_system_available_bytes=psutil.virtual_memory().available,
                      total_system_ram_bytes=psutil.virtual_memory().total)
        report['memory'] = memory
        def sample_memory():
            while not stop.wait(0.1):
                memory['peak_sampled_rss_bytes'] = max(memory['peak_sampled_rss_bytes'], process.memory_info().rss)
                memory['minimum_system_available_bytes'] = min(memory['minimum_system_available_bytes'], psutil.virtual_memory().available)
        monitor = threading.Thread(target=sample_memory, daemon=True)
        monitor.start()
        report['software'] = {name: importlib.metadata.version(name) for name in
                              ['torch', 'transformers', 'tokenizers', 'numpy', 'nltk', 'huggingface-hub',
                               'safetensors', 'sentencepiece', 'psutil', 'accelerate']}
        report['python'] = sys.version
        report['platform'] = platform.platform()
        report['cpu'] = platform.processor()
        m, rows = validate_inputs()
        require(m['reference_policy'] == {'DM': 'tgt', 'MT': 'tgt', 'PG': 'src'}, 'reference policy')
        # The validated artifact contains only four allowlisted text/ID fields.
        selected = [r for task in ['DM', 'MT', 'PG'] for r in
                    sorted((r for r in rows if r['task'] == task), key=lambda r: r['canonical_id'])[:4]]
        require(len(selected) == len({r['canonical_id'] for r in selected}) == 12, '12 unique samples')
        require(all(sum(r['task'] == t for r in selected) == 4 for t in ['DM', 'MT', 'PG']), 'task composition')
        # Independent reference provenance from existing label-free E9 NLI hash audit.
        audit = {r['canonical_id']: r for r in
                 [json.loads(line) for line in (HERE.parent / 'features/nli_input_hashes.jsonl').read_text().splitlines()]}
        expected_audit_hash = json.loads((HERE.parent / 'minicheck_gpu/GPU_RUN_MANIFEST.json').read_text())['local_frozen_sha256'][
            'RAG/results/phase3_e9_claim_verification/features/nli_input_hashes.jsonl']
        require(sha(HERE.parent / 'features/nli_input_hashes.jsonl') == expected_audit_hash, 'reference audit changed')
        for r in selected:
            require(set(r) == {'canonical_id', 'task', 'whole_hypothesis', 'reference_text'}, 'leakage allowlist')
            require(audit[r['canonical_id']]['reference_column'] == ('src' if r['task'] == 'PG' else 'tgt'), 'reference column')
            require(hashlib.sha256(r['reference_text'].encode()).hexdigest() == audit[r['canonical_id']]['premise_sha256'], 'reference text hash')
        report['leakage_check'] = 'PASS'
        report['reference_policy_check'] = 'PASS'
        report['input_sha256'] = sha(GPU / 'factcg_inputs.jsonl')
        report['selected_input_digest'] = digest(selected)
        report['selection'] = 'First four canonical IDs sorted independently within each task; no labels read'
        write(HERE / 'SELECTION_MANIFEST.json', dict(input_sha256=report['input_sha256'],
              selected_input_digest=report['selected_input_digest'], selection=report['selection'],
              samples=[dict(canonical_id=r['canonical_id'], task=r['task'], input_row_sha256=digest(r)) for r in selected]))
        require(psutil.virtual_memory().available >= 3 * 1024**3, 'Less than 3 GiB free RAM before loading; stop safely')
        import torch
        import nltk
        from transformers import AutoConfig, AutoTokenizer, AutoModelForSequenceClassification
        from huggingface_hub import hf_hub_download
        torch.set_num_threads(4)
        torch.set_num_interop_threads(1)
        torch.manual_seed(42)
        report['threads'] = dict(intraop=4, interop=1)
        report['cuda_available'] = torch.cuda.is_available()
        nltk.data.path.insert(0, str(GPU / 'nltk_data'))
        tokenizer = AutoTokenizer.from_pretrained(str(GPU / 'tokenizer_snapshot'), use_fast=True, local_files_only=True)
        phase = 'checkpoint download'
        checkpoint_started = time.perf_counter()
        checkpoint_path = Path(hf_hub_download(repo_id=MODEL, filename='model.safetensors', revision=REVISION,
                                             cache_dir=str(HERE / 'model_cache')))
        config_path = Path(hf_hub_download(repo_id=MODEL, filename='config.json', revision=REVISION,
                                          cache_dir=str(HERE / 'model_cache')))
        report['download_seconds'] = time.perf_counter() - checkpoint_started
        require(checkpoint_path.parent.name == REVISION and config_path.parent == checkpoint_path.parent, 'snapshot revision mismatch')
        require(sha(config_path) == sha(GPU / 'tokenizer_snapshot/config.json'), 'checkpoint config mismatch')
        phase = 'model load'
        print('Checkpoint available; loading exact FP32 safetensors on CPU.', flush=True)
        load_started = time.perf_counter()
        config = AutoConfig.from_pretrained(str(config_path.parent), num_labels=2,
                                            finetuning_task='text-classification', local_files_only=True)
        config.problem_type = 'single_label_classification'
        model = AutoModelForSequenceClassification.from_pretrained(
            str(checkpoint_path.parent), config=config, use_safetensors=True, local_files_only=True,
            torch_dtype=torch.float32, low_cpu_mem_usage=True, ignore_mismatched_sizes=False).eval()
        report['model_load_seconds'] = time.perf_counter() - load_started
        require(all(p.device.type == 'cpu' and p.dtype == torch.float32 for p in model.parameters()), 'CPU FP32 parameters')
        require(config.num_labels == 2, 'two-class head')
        report['model_loaded'] = True
        report['parameter_count'] = sum(p.numel() for p in model.parameters())
        def score(reference, hypothesis):
            probabilities = []
            chunks = chunk_reference(reference)
            require(bool(chunks), 'empty reference chunks')
            for chunk in chunks:
                batch = tokenize(tokenizer, [chunk], [hypothesis])
                require(batch['input_ids'].device.type == 'cpu', 'input device')
                with torch.no_grad():
                    logits = model(**batch).logits
                    require(tuple(logits.shape) == (1, 2), 'classifier shape')
                    probabilities.append(torch.softmax(logits, dim=-1)[0, 1].item())
            p = max(probabilities)
            require(math.isfinite(p) and 0 <= p <= 1, 'probability range')
            return p
        phase = 'orientation sanity check'
        print('Checking official class-1 support orientation on two synthetic pairs.', flush=True)
        sanity_started = time.perf_counter()
        supported = score('The meeting took place on Monday.', 'The meeting took place on Monday.')
        contradictory = score('The meeting took place on Monday.', 'The meeting took place on Friday.')
        report['orientation'] = dict(supported_probability=supported, contradictory_probability=contradictory,
                                    gap=supported-contradictory, required_gap=0.25,
                                    inference_seconds=time.perf_counter()-sanity_started,
                                    semantics='Official HF branch: softmax(logits)[:,1], max over reference chunks')
        require(supported - contradictory >= 0.25, 'orientation separation failed; do not score SHROOM rows')
        report['orientation']['status'] = 'PASS'
        print(f'Orientation PASS: supported={supported:.6f}, contradictory={contradictory:.6f}', flush=True)
        phase = '12 sample inference'
        elapsed = []
        smoke_started = time.perf_counter()
        with (HERE / 'smoke_outputs.jsonl').open('x', encoding='utf-8', newline='\n') as f:
            for r in selected:
                t = time.perf_counter()
                p = score(r['reference_text'], r['whole_hypothesis'])
                elapsed.append(time.perf_counter() - t)
                out = dict(canonical_id=r['canonical_id'], task=r['task'], factcg_support_probability=p)
                results.append(out)
                f.write(json.dumps(out, allow_nan=False) + '\n')
                f.flush()
                print(json.dumps(out), flush=True)
        report['inference_12_seconds'] = time.perf_counter() - smoke_started
        require(len(results) == 12 and {r['canonical_id'] for r in results} == {r['canonical_id'] for r in selected}, 'output coverage')
        require(all(math.isfinite(r['factcg_support_probability']) and 0 <= r['factcg_support_probability'] <= 1 for r in results), 'finite output range')
        report['outputs'] = len(results)
        report['counts_by_task'] = {task: sum(r['task'] == task for r in results) for task in ['DM','MT','PG']}
        report['output_sha256'] = sha(HERE / 'smoke_outputs.jsonl')
        report['per_sample_seconds'] = elapsed
        projected = report['model_load_seconds'] + statistics.mean(elapsed) * 561
        report['estimate_561'] = dict(warm_cache_load_plus_inference_seconds=projected,
                                    inference_only_seconds=statistics.mean(elapsed)*561,
                                    cold_download_additional_seconds=report['download_seconds'],
                                    mean_seconds_per_sample=statistics.mean(elapsed),
                                    median_seconds_per_sample=statistics.median(elapsed),
                                    slowest_sample_linear_projection_seconds=report['model_load_seconds']+max(elapsed)*561,
                                    limitation='Linear extrapolation from 12 fixed ID-selected samples; not a representative performance benchmark. No full run executed.')
        report['recommendation'] = 'LOCAL_FULL_RUN' if projected <= 1800 and memory['minimum_system_available_bytes'] >= 1024**3 else 'GPU_FULL_RUN'
        report['status'] = 'PASS'
        report['reason'] = 'Orientation, 12 sample coverage, finite range, reference policy and leakage checks passed'
        del model
    except Exception as exc:
        report['status'] = 'FAIL' if phase in ['orientation sanity check','12 sample inference'] else 'BLOCKED'
        report['reason'] = f'{phase}: {type(exc).__name__}: {exc}'
    finally:
        stop.set()
        if monitor:
            monitor.join(timeout=2)
        if 'process' in locals():
            mem = process.memory_info()
            report['memory']['os_peak_working_set_bytes'] = getattr(mem, 'peak_wset', None)
            report['memory']['measurement'] = 'Process RSS sampled every 0.1 sec; Windows OS peak working set when available; minimum available system RAM'
        changed = [path for path, before in frozen.items() if sha(Path(path)) != before]
        report['frozen_packages_unchanged'] = not changed
        if changed:
            report.update(status='FAIL', reason='Frozen package integrity changed')
        report['wall_seconds'] = time.perf_counter() - started
        write(HERE / 'LOCAL_SMOKE_REPORT.json', report)
        with (HERE / 'LOCAL_SMOKE_REPORT.md').open('x', encoding='utf-8') as f:
            f.write('# Local FactCG 12-sample smoke\n\n')
            f.write(f"Status: **{report['status']}**\n\n")
            f.write('| canonical_id | task | FactCG support probability |\n|---|---|---|\n')
            for r in results:
                f.write(f"| {r['canonical_id']} | {r['task']} | {r['factcg_support_probability']:.10f} |\n")
            f.write('\nRuntime and integrity metadata:\n\n```json\n' + json.dumps(report, indent=2) + '\n```\n')
            f.write('\n' + report['recommendation'] + '\n')
        print(report['status'] + ': ' + report['reason'], flush=True)
        print(report['recommendation'], flush=True)
    return 0 if report['status'] == 'PASS' else 1

if __name__ == '__main__':
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
    sys.exit(main())
