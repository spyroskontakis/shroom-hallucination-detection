"""Requested CPU-only smoke using the existing frozen 12-ID manifest.

Reads label-free portable input, selection manifest, pinned model metadata only.
Does not import evaluation code or access canonical label/fold/prediction files.
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
OUT = HERE / 'cpu_sun12'
sys.path.insert(0, str(GPU))
from factcg_common import MODEL, REVISION, require, sha, digest, write, validate_inputs
from factcg_backend import chunk_reference, tokenize

def main():
    OUT.mkdir(exist_ok=False)
    wall = time.perf_counter()
    # Hash only the prepared portable package, not experiment results or folds.
    frozen = {str(p): sha(p) for p in GPU.rglob('*') if p.is_file()}
    report = dict(status='BLOCKED', model_name=MODEL, revision=REVISION, revision_verified=False,
                  device='cpu', leakage_status='PENDING', recommendation='GPU_FULL_RUN',
                  outputs=[], error=None)
    stop = threading.Event()
    monitor = None
    phase = 'input validation'
    try:
        m, rows = validate_inputs()
        selection = json.loads((HERE / 'SELECTION_MANIFEST.json').read_text())
        require(selection['input_sha256'] == sha(GPU / 'factcg_inputs.jsonl'), 'selection input hash')
        by_id = {r['canonical_id']: r for r in rows}
        selected = [by_id[r['canonical_id']] for r in selection['samples']]
        require(len(selected) == len({r['canonical_id'] for r in selected}) == 12, '12 unique IDs')
        require(digest(selected) == selection['selected_input_digest'], 'frozen selection digest')
        for r, saved in zip(selected, selection['samples']):
            require(digest(r) == saved['input_row_sha256'] and r['task'] == saved['task'], 'frozen sample identity')
        expected = [r for task in ['DM', 'MT', 'PG'] for r in
                    sorted((r for r in rows if r['task'] == task), key=lambda r: r['canonical_id'])[:4]]
        require(selected == expected, 'frozen label-blind first-four selection')
        require(m['reference_policy'] == {'DM':'tgt','MT':'tgt','PG':'src'}, 'frozen reference policy')
        require(all(set(r) == {'canonical_id','task','whole_hypothesis','reference_text'} for r in rows), 'input allowlist')
        write(OUT / 'SELECTION_MANIFEST.json', selection)
        print('REQUESTED REVISION:', REVISION, flush=True)
        print('FROZEN IDS BEFORE MODEL LOAD:', flush=True)
        for r in selected:
            print(r['canonical_id'], r['task'], flush=True)
        report['leakage_status'] = 'PASS'
        report['leakage_justification'] = 'Existing label-blind 12-ID manifest and four-field hash-validated portable input only; no labels, p(Hallucination), previous predictions/correctness, folds, or official test data accessed.'
        report['reference_policy'] = m['reference_policy']
        report['selection_manifest_sha256'] = sha(HERE / 'SELECTION_MANIFEST.json')
        import psutil
        proc = psutil.Process()
        available = psutil.virtual_memory()
        report['environment'] = dict(os=platform.platform(), cpu=platform.processor(),
                                    physical_cpus=psutil.cpu_count(logical=False), logical_cpus=psutil.cpu_count(),
                                    ram_total_bytes=available.total, ram_available_start_bytes=available.available,
                                    python=platform.python_version())
        # CPU registry description is local hardware metadata, not user data.
        if platform.system() == 'Windows':
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
                report['environment']['cpu'] = winreg.QueryValueEx(key, 'ProcessorNameString')[0].strip()
        report['software'] = {p:importlib.metadata.version(p) for p in
                             ['torch','transformers','tokenizers','numpy','safetensors','nltk','huggingface-hub','accelerate','psutil']}
        mem = dict(peak_sampled_rss_bytes=proc.memory_info().rss, min_available_system_bytes=available.available)
        report['memory'] = mem
        def monitor_memory():
            while not stop.wait(0.05):
                mem['peak_sampled_rss_bytes'] = max(mem['peak_sampled_rss_bytes'], proc.memory_info().rss)
                mem['min_available_system_bytes'] = min(mem['min_available_system_bytes'], psutil.virtual_memory().available)
        monitor = threading.Thread(target=monitor_memory, daemon=True)
        monitor.start()
        require(available.available >= 3 * 1024**3, 'Insufficient free RAM before CPU smoke')
        phase = 'cache preparation'
        import torch
        import nltk
        from huggingface_hub import snapshot_download
        from transformers import AutoTokenizer, AutoConfig, AutoModelForSequenceClassification
        torch.set_num_threads(4)
        torch.set_num_interop_threads(1)
        torch.manual_seed(42)
        nltk.data.path.insert(0, str(GPU / 'nltk_data'))
        report['threads'] = dict(intraop=4, interop=1)
        cache_started = time.perf_counter()
        cache = HERE / 'model_cache'
        names = ['config.json','model.safetensors','tokenizer.json','tokenizer_config.json',
                 'special_tokens_map.json','added_tokens.json','spm.model']
        snapshot = Path(snapshot_download(repo_id=MODEL, revision=REVISION, cache_dir=str(cache),
                                          allow_patterns=names, max_workers=2))
        require(snapshot.name == REVISION, 'snapshot revision')
        release = json.loads((HERE / 'CHECKPOINT_RELEASE_METADATA.json').read_text())
        require(release['revision'] == REVISION and release['model_id'] == MODEL, 'release metadata')
        require(sha(snapshot / 'model.safetensors') == release['file']['lfs']['oid'], 'safetensors SHA256')
        report['weights_sha256'] = release['file']['lfs']['oid']
        for name in names:
            if name != 'model.safetensors':
                require(sha(snapshot/name) == sha(GPU/'tokenizer_snapshot'/name), 'pinned tokenizer/config content: '+name)
        report['download_or_cache_time_sec'] = time.perf_counter()-cache_started
        report['cache_note'] = 'Weights cached from prior interrupted-turn smoke; cache preparation includes tokenizer acquisition and checkpoint hash verification. Prior first weight download was separate.'
        phase = 'model load'
        mem['rss_before_load_bytes'] = proc.memory_info().rss
        load_started = time.perf_counter()
        # Exact repository/revision in every from_pretrained call, with no remote-code or CPU quantization.
        kwargs = dict(revision=REVISION, cache_dir=str(cache), local_files_only=True, trust_remote_code=False)
        tokenizer = AutoTokenizer.from_pretrained(MODEL, use_fast=True, **kwargs)
        config = AutoConfig.from_pretrained(MODEL, num_labels=2, finetuning_task='text-classification', **kwargs)
        config.problem_type = 'single_label_classification'
        model = AutoModelForSequenceClassification.from_pretrained(
            MODEL, config=config, use_safetensors=True, torch_dtype=torch.float32,
            low_cpu_mem_usage=True, ignore_mismatched_sizes=False, **kwargs).to('cpu').eval()
        report['model_load_time_sec'] = time.perf_counter()-load_started
        mem['rss_after_load_bytes'] = proc.memory_info().rss
        require(config._commit_hash == REVISION, 'resolved model revision')
        require(all(p.device.type == 'cpu' and p.dtype == torch.float32 for p in model.parameters()), 'CPU FP32 inference required')
        require(not model.training and config.num_labels == 2, 'evaluation classifier')
        report['revision_verified'] = True
        print('Model/tokenizer loaded. Verified revision:', config._commit_hash, 'device: CPU', flush=True)
        def score(reference, hypothesis, raw=False):
            chunks = chunk_reference(reference)
            require(bool(chunks), 'reference chunking')
            probabilities, details = [], []
            for chunk in chunks:
                batch = tokenize(tokenizer, [chunk], [hypothesis])
                require(all(v.device.type == 'cpu' for v in batch.values()), 'input CPU device')
                with torch.no_grad():
                    logits = model(**batch).logits
                    probs = torch.softmax(logits, dim=-1)
                require(tuple(logits.shape) == (1,2), 'two-class logits')
                probabilities.append(probs[0,1].item())
                if raw:
                    details.append(dict(logits=logits[0].tolist(), softmax=probs[0].tolist()))
            result = max(probabilities)
            require(math.isfinite(result) and 0 <= result <= 1, 'finite support range')
            return result, details
        phase = 'orientation sanity'
        sanity_started = time.perf_counter()
        context = 'The sun rises in the east.'
        supported, supported_raw = score(context, 'The sun rises in the east.', True)
        contradictory, contradictory_raw = score(context, 'The sun rises in the west.', True)
        report['sanity_inference_time_sec'] = time.perf_counter()-sanity_started
        gap = supported-contradictory
        report['orientation'] = dict(supported_score=supported, contradictory_score=contradictory,
                                    delta=gap, supported_raw=supported_raw, contradictory_raw=contradictory_raw,
                                    support_class_index=1, documentation='Frozen official HF scoring path explicitly selects softmax(logits)[:,1]',
                                    status='PASS' if gap >= 0.25 else 'ORIENTATION_SANITY_CHECK_FAILED')
        print('ORIENTATION:',json.dumps(report['orientation']),flush=True)
        require(gap >= 0.25, 'ORIENTATION_SANITY_CHECK_FAILED; no SHROOM inference')
        phase = '12 SHROOM inference'
        elapsed = []
        smoke_started = time.perf_counter()
        with (OUT/'smoke_outputs.jsonl').open('x',encoding='utf-8',newline='\n') as f:
            for r in selected:
                t = time.perf_counter()
                p, _ = score(r['reference_text'],r['whole_hypothesis'])
                elapsed.append(time.perf_counter()-t)
                result = dict(canonical_id=r['canonical_id'],task=r['task'],factcg_support_probability=p)
                report['outputs'].append(result)
                f.write(json.dumps(result,allow_nan=False)+'\n')
                f.flush()
                print(json.dumps(result),flush=True)
        report['shroom_12_inference_time_sec'] = time.perf_counter()-smoke_started
        require(len(report['outputs']) == 12 and
                {r['canonical_id'] for r in report['outputs']} == {r['canonical_id'] for r in selected}, 'no dropped/extra samples')
        require(all(sum(r['task']==t for r in report['outputs'])==4 for t in ['DM','MT','PG']), '4 per task')
        report['mean_sec_per_sample'] = statistics.mean(elapsed)
        report['median_sec_per_sample'] = statistics.median(elapsed)
        report['estimated_561_inference_sec'] = statistics.mean(elapsed)*561
        report['estimated_561_total_sec'] = report['model_load_time_sec']+report['estimated_561_inference_sec']
        report['per_sample_seconds'] = elapsed
        report['range'] = dict(min=min(r['factcg_support_probability'] for r in report['outputs']),
                               max=max(r['factcg_support_probability'] for r in report['outputs']))
        report['recommendation'] = ('LOCAL_FULL_RUN' if report['estimated_561_total_sec'] <= 1800 and
                                     mem['min_available_system_bytes'] >= 1024**3 else 'GPU_FULL_RUN')
        report['status'] = 'PASS'
        report['output_sha256'] = sha(OUT/'smoke_outputs.jsonl')
    except Exception as exc:
        report['status'] = 'FAIL' if phase in ['orientation sanity','12 SHROOM inference'] else 'BLOCKED'
        report['error'] = f'{phase}: {type(exc).__name__}: {exc}'
        print(report['error'],flush=True)
    finally:
        stop.set()
        if monitor:
            monitor.join(timeout=2)
        if 'proc' in locals():
            info = proc.memory_info()
            mem['os_peak_working_set_bytes'] = getattr(info,'peak_wset',None)
            mem['ram_available_end_bytes'] = psutil.virtual_memory().available
            mem['measurement_method'] = 'psutil process RSS sampled every 50 ms; Windows OS peak working set also recorded'
        report['frozen_gpu_package_unchanged'] = all(sha(Path(p))==h for p,h in frozen.items())
        if not report['frozen_gpu_package_unchanged']:
            report['status']='FAIL'
        report['wall_time_sec']=time.perf_counter()-wall
        write(OUT/'LOCAL_SMOKE_REPORT.json',report)
        print('STATUS:',report['status'],flush=True)
        print(report['recommendation'],flush=True)
    return 0 if report['status']=='PASS' else 1

if __name__ == '__main__':
    os.environ['CUDA_VISIBLE_DEVICES']=''
    os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
    os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING']='1'
    sys.exit(main())
