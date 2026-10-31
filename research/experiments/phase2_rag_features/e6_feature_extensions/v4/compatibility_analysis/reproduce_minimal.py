"""One-character official tokenization reproducer, no model or SHROOM input."""
import os, sys, json, traceback, inspect, hashlib, socket, importlib.metadata
from pathlib import Path
HERE=Path(__file__).resolve().parent; V4=HERE.parent
sys.path.insert(0,str(V4/'packages'))
for k in ['HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_DATASETS_OFFLINE','HF_HUB_DISABLE_TELEMETRY','PYTHONDONTWRITEBYTECODE']:os.environ[k]='1'
os.environ['MPLCONFIGDIR']=str(HERE/'tmp/matplotlib');os.environ['MPLBACKEND']='Agg'
def blocked(*args,**kwargs):raise RuntimeError('Network disabled during synthetic diagnosis')
socket.socket.connect=blocked;socket.create_connection=blocked;socket.getaddrinfo=blocked
import transformers,tokenizers,torch,bert_score
from bert_score.utils import get_tokenizer,sent_encode
MODEL='microsoft/deberta-large-mnli'; REV='7296194b9009373def4f7c5dad292651e4b5cf4e'
old=json.loads((V4/'provenance/compatibility.json').read_text())
assert Path(old['cache_ref_path']).read_text().strip()==REV
tok=get_tokenizer(MODEL,use_fast=False)
initial_limit=tok.model_max_length
observed=[]
def trace(frame,event,arg):
    if event=='call' and frame.f_code.co_name in ['encode','_encode_plus','set_truncation_and_padding']:
        values={k:str(v) if hasattr(v,'value') else v for k,v in frame.f_locals.items()
                if k in ['text','text_pair','max_length','truncation','padding','truncation_strategy','padding_strategy','stride','add_special_tokens']}
        observed.append({'file':frame.f_code.co_filename,'line':frame.f_code.co_firstlineno,'function':frame.f_code.co_name,'args':values})
    return trace
result={'model_type':MODEL,'checkpoint_revision':REV,'tokenizer_class':type(tok).__name__,
        'tokenizer_module':type(tok).__module__,'tokenizer_mro':[c.__name__ for c in type(tok).__mro__],
        'model_max_length':initial_limit,'python':sys.version,'python_executable':sys.executable,
        'versions':{n:importlib.metadata.version(n) for n in ['bert-score','transformers','tokenizers','torch','huggingface-hub']},
        'bert_score_internal_version':bert_score.__version__,'input':'a','input_characters':1,'input_utf8_bytes':1,
        'real_samples_read':0,'real_features_extracted':0,'rf_fits':0,'evaluations':0}
try:
    sys.settrace(trace)
    ids=sent_encode(tok,'a')
    result.update(status='NO_EXCEPTION',ids=ids)
except Exception as exc:
    result.update(status='REPRODUCED',exception_type=type(exc).__module__+'.'+type(exc).__name__,
                  exception_message=str(exc),traceback=traceback.format_exc(),
                  frames=[{'filename':f.filename,'line':f.lineno,'function':f.name,'source':f.line} for f in traceback.extract_tb(exc.__traceback__)])
finally:sys.settrace(None)
result['observed_calls']=observed
controls=[]
for padding,truncation in [(False,True),(True,True),(False,False)]:
    record={'padding':padding,'truncation':truncation,'max_length':initial_limit}
    try:
        ids=tok.encode('a',add_special_tokens=True,max_length=initial_limit,truncation=truncation,padding=padding)
        record.update(status='PASS',ids=ids,token_count_with_special=len(ids))
    except Exception as exc:record.update(status='FAIL',exception_type=type(exc).__name__,exception_message=str(exc))
    controls.append(record)
result['controls']=controls
assert tok.model_max_length==initial_limit
result['model_max_length_mutated']=False
sources={}
for name,obj in [('sent_encode',sent_encode),('get_tokenizer',get_tokenizer),('tokenizer_class',type(tok)),('encode',tok.encode),('scorer_init',bert_score.BERTScorer.__init__),('scorer_score',bert_score.BERTScorer.score)]:
    lines,start=inspect.getsourcelines(obj); path=Path(inspect.getsourcefile(obj))
    sources[name]={'path':str(path),'start_line':start,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source':''.join(lines)}
result['sources']=sources
name='minimal_current.json' if transformers.__version__=='5.5.4' else 'minimal_pinned.json'
with (HERE/name).open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,ensure_ascii=False)
print(json.dumps({k:v for k,v in result.items() if k not in ['sources','traceback']},indent=2))
assert result['status']=='REPRODUCED' if transformers.__version__=='5.5.4' else result['status']=='NO_EXCEPTION'
