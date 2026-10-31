"""Final-runtime synthetic-only compatibility gate, before real extraction."""
import common as c
import time,traceback
def main():
 log=c.offline('smoke');env=c.runtime('encoding');c.assets()
 import torch
 import structure
 assert structure.contracts()=='PASS'
 samples=[('identical','A red cat sleeps.','A red cat sleeps.'),
 ('omission','A red cat sleeps and a blue dog runs.','A red cat sleeps.'),
 ('addition','A red cat sleeps.','A red cat sleeps and a blue dog runs.'),
 ('number_change','There are 12 apples.','There are 13 apples.'),
 ('negation_added','The train is running.','The train is not running.'),
 ('negation_removed','The train is not running.','The train is running.')]
 start=time.perf_counter();s=c.scorer()
 with torch.inference_mode():p,r,f=s.score(cands=[x[2] for x in samples],refs=[x[1] for x in samples],batch_size=2)
 assert torch.isfinite(torch.stack([p,r,f])).all()
 assert torch.allclose(torch.stack([p[0],r[0],f[0]]),torch.ones(3),atol=2e-5,rtol=0)
 assert p[1]>r[1] and r[2]>p[2]
 assert abs(float(p[1]-r[2]))<2e-5 and abs(float(r[1]-p[2]))<2e-5
 assert log.stat().st_size==0
 c.write(c.HERE/'synthetic_contract.json',{'status':'PASS','runtime':env,'model':c.MODEL,'revision':c.REV,
  'num_layers':s.num_layers,'hash_string':s.hash,'tokenizer_class':type(s._tokenizer).__name__,
  'model_max_length':s._tokenizer.model_max_length,'manual_override':False,'device':'cpu','dtype':'float32',
  'cuda_available':torch.cuda.is_available(),'torch_cuda_build':torch.version.cuda,
  'seconds':time.perf_counter()-start,'real_samples':0,'network_attempts':0,'structure_contracts':'PASS',
  'samples':[{'kind':x[0],'reference':x[1],'hyp':x[2],'P':float(p[i]),'R':float(r[i]),'F1':float(f[i]),
              'structure':structure.features(x[1],x[2])} for i,x in enumerate(samples)]})
 print('Synthetic compatibility and direction contracts PASS',flush=True)
if __name__=='__main__':
 try:main()
 except Exception as e:
  c.write(c.HERE/'synthetic_failure.json',{'error':repr(e),'traceback':traceback.format_exc()});raise
