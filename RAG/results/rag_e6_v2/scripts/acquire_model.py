"""Download only explicitly authorized files of the immutable second-NLI revision."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, subprocess, time

OUT=Path(__file__).resolve().parents[1]
MODEL_ID='MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli'
REVISION='b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7'
FILES=['README.md','config.json','tokenizer_config.json','tokenizer.json','special_tokens_map.json',
       'added_tokens.json','spm.model','model.safetensors']


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()


def main():
    meta=json.loads((OUT/'provenance/pinned_repository_metadata.json').read_text(encoding='utf-8'))
    assert meta['sha']==REVISION
    assert set(FILES)<=set(s['rfilename'] for s in meta['siblings'])
    if (OUT/'provenance/acquisition.json').exists(): raise FileExistsError('Acquisition already completed')
    t0=time.perf_counter(); results={}
    for name in FILES:
        url=f'https://huggingface.co/{MODEL_ID}/resolve/{REVISION}/{name}'
        dest=OUT/'model'/name
        if dest.exists(): raise FileExistsError(dest)
        part=dest.with_name(dest.name+'.part')
        print('Downloading '+name,flush=True)
        subprocess.run(['curl.exe','--fail','--location','--silent','--show-error',
                        '--retry','3','--output',str(part),url],check=True)
        part.replace(dest)
        results[name]={'url':url,'path':dest.relative_to(OUT).as_posix(),'bytes':dest.stat().st_size,'sha256':sha(dest)}
        print(json.dumps({'file':name,'bytes':dest.stat().st_size,'sha256':results[name]['sha256']}),flush=True)
    result={'model_id':MODEL_ID,'revision':REVISION,'repository_sha':meta['sha'],
            'completed_utc':datetime.now(timezone.utc).isoformat(),'duration_seconds':time.perf_counter()-t0,
            'scope':'authorized pinned model/tokenizer/card download only; no remote inference',
            'files':results,'script_sha256':sha(Path(__file__))}
    with (OUT/'provenance/acquisition.json').open('x',encoding='utf-8') as f:
        json.dump(result,f,indent=2);f.write('\n')


if __name__=='__main__': main()
