"""Label-free technical smoke; select CPU float32 batch=2 before feature freeze."""
if "_H2_CTX" not in globals():
    raise RuntimeError("Historical source: use the pinned cross-experiment context; direct execution/import is disabled")
import time
import v2_common as c


def main():
    log=c.offline('smoke')
    c.verify_inputs();acq=c.verify_models();runtime=c.versions()
    import torch
    from nli_backend import load_backend,infer_batch
    # Execution choice based on available hardware, not labels or task accuracy.
    device='cpu';dtype='float32';batch_size=2
    tokenizer,model=load_backend()
    texts=[('A person opened a window.','The window is open.'),
           ('The train arrives at noon.','The garden has flowers.'),
           ('Long technical smoke sentence. '*150,'Another technical smoke sentence. '*130),
           ('Short text.','Short text.')]
    pairs=[{'pair_id':f'smoke{i}','canonical_id':f'SMOKE{i}','group':'SMOKE',
            'premise':p,'hypothesis':h} for i,(p,h) in enumerate(texts)]
    t0=time.perf_counter();scores=[];audits=[]
    for i in range(0,len(pairs),batch_size):
        s,a=infer_batch(tokenizer,model,pairs[i:i+batch_size]);scores+=s;audits+=a
    assert any(a['truncated'] for a in audits)
    assert log.stat().st_size==0
    c.write_json(c.OUT/'config/smoke.json',{'status':'PASS','completed_utc':c.now(),
                 'device':device,'dtype':dtype,'batch_size':batch_size,'cuda_available':torch.cuda.is_available(),
                 'cuda_device_count':torch.cuda.device_count(),'torch_threads':torch.get_num_threads(),
                 'torch_interop_threads':torch.get_num_interop_threads(),
                 'runtime':runtime,'tokenizer_class':type(tokenizer).__name__,'tokenizer_fast':tokenizer.is_fast,
                 'model_class':type(model).__name__,'parameter_dtypes':sorted({str(p.dtype) for p in model.parameters()}),
                 'attention_implementation':model.config._attn_implementation,
                 'id2label':model.config.id2label,'label2id':model.config.label2id,
                 'pair_count':4,'pairs':pairs,'scores':scores,'truncation':audits,
                 'inference_seconds':time.perf_counter()-t0,'labels_accessed':False,'accuracy_computed':False,
                 'network_attempts':0,'acquisition_sha256':c.sha(c.OUT/'provenance/acquisition.json')})
    print({'smoke':'PASS','device':device,'dtype':dtype,'batch_size':batch_size,
           'inference_seconds':time.perf_counter()-t0},flush=True)


if __name__=='__main__':main()
