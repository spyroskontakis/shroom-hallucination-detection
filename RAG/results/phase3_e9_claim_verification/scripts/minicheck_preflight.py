"""Read-only hardware/dependency gate after E9-A; never loads model weights."""
import ctypes
import importlib.util
import json
import platform
from datetime import datetime, timezone
import torch
import e9_common as c


def main():
    a = c.read_json(c.OUT / 'evaluation/E9-A_metrics.json')
    c.require(a['status'] == 'COMPLETED' and a['rf_fits'] == 5, 'E9-A must finish first')
    class Memory(ctypes.Structure):
        _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [
            (name, ctypes.c_ulonglong) for name in ['total', 'available', 'page_total',
            'page_available', 'virtual_total', 'virtual_available', 'extended']]
    memory = Memory()
    memory.length = ctypes.sizeof(Memory)
    c.require(platform.system() == 'Windows', 'Reassess gate for another operating system')
    c.require(ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)), 'Memory query failed')
    hardware = dict(platform=platform.platform(), torch=torch.__version__,
                    cuda_built=torch.version.cuda, cuda_available=torch.cuda.is_available(),
                    gpu_count=torch.cuda.device_count(), ram_total_bytes=memory.total,
                    ram_available_bytes=memory.available)
    deps = {name: importlib.util.find_spec(name) is not None
            for name in ['minicheck', 'vllm', 'flash_attn']}
    c.require(not hardware['cuda_available'], 'Hardware changed; reassess preflight')
    reason = ('Native Windows with CPU-only PyTorch and no CUDA device; minicheck and vllm '
              'are absent. The authors document the exact 7B MiniCheck/vLLM interface as '
              'Linux-only. Available RAM is insufficient even for an unquantized 7B '
              'two-byte-per-parameter weights estimate (14 GB), before runtime overhead. '
              'The frozen protocol prohibits quantization, substitution or OOM redesign.')
    report = dict(status='BLOCKED_MINICHECK', model='bespokelabs/Bespoke-MiniCheck-7B',
                  timestamp_utc=datetime.now(timezone.utc).isoformat(), hardware=hardware,
                  dependencies=deps, reason=reason, model_loaded=False, model_downloaded=False,
                  rf_fits=0, official_test_accessed=False,
                  sources=['https://github.com/Liyan06/MiniCheck#installation',
                           'https://huggingface.co/bespokelabs/Bespoke-MiniCheck-7B'],
                  memory_estimate_note='14 GB is a conservative weights-only estimate, not a vendor minimum; the published 48 GB benchmark is not a minimum requirement.')
    c.require(memory.available < 14_000_000_000, 'Memory changed; reassess report')
    c.write_json(c.OUT / 'reports/minicheck_preflight.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
