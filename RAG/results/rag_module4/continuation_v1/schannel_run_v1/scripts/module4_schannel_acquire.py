"""curl/Schannel transport adapter for frozen Module 4 Wiktionary acquisition."""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys, tempfile, time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[6]
CONT=ROOT/'RAG'/'results'/'rag_module4'/'continuation_v1'
sys.path.insert(0,str(CONT/'scripts'))
import module4_build_wiktionary_lexicon as frozen_wiki

CURL=Path(r'C:\WINDOWS\system32\curl.exe')
ENDPOINT='https://en.wiktionary.org/w/api.php'
USER_AGENT='SHROOM-Thesis-Module4/1.0 (academic reproducibility study)'
TRANSIENT_EXITS={6,7,18,22,28,35,52,55,56}
TLS_EXIT=60

class GlobalTLSFailure(BaseException): pass

def sha256_bytes(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def sanitize_error(value:str)->str:return ' '.join(value.replace('\r',' ').replace('\n',' ').split())[:1000]

def curl_args(url:str,body:Path,headers:Path,timeout:int=30)->list[str]:
    args=[str(CURL),'-q','--silent','--show-error','--request','GET','--proto','=https','--proto-redir','=https','--max-time',str(timeout),'--max-redirs','0','--fail-with-body','--user-agent',USER_AGENT,'--output',str(body),'--dump-header',str(headers),'--write-out','{"http_code":%{http_code},"ssl_verify_result":%{ssl_verify_result},"remote_ip":"%{remote_ip}","size_download":%{size_download}}',url]
    forbidden={'-k','--insecure','--proxy-insecure','--ssl-no-revoke','--ssl-revoke-best-effort'}
    if forbidden.intersection(args):raise RuntimeError('Forbidden curl option')
    return args

def parse_headers(raw:bytes)->dict[str,str]:
    result={}
    for line in raw.decode('iso-8859-1','replace').splitlines():
        if ':' in line:
            k,v=line.split(':',1);lk=k.strip().lower()
            if lk in {'date','retry-after','content-type'}:result[lk]=v.strip()
    return result

def validate_json(data:bytes,purpose:str)->dict[str,Any]:
    obj=json.loads(data.decode('utf-8'))
    if not isinstance(obj,dict) or 'error' in obj:raise ValueError('MediaWiki API error or invalid object')
    if purpose=='siteinfo' and not isinstance(obj.get('query',{}).get('general'),dict):raise ValueError('Missing query.general')
    if purpose=='revision_identity' and not isinstance(obj.get('query',{}).get('pages'),list):raise ValueError('Missing query.pages')
    if purpose=='frozen_revision_content' and not isinstance(obj.get('parse',{}).get('text'),str):raise ValueError('Missing parse.text')
    return obj

class SchannelFetcher:
    def __init__(self,log_path:Path,max_attempts:int=3):
        self.log_path=log_path;self.max_attempts=max_attempts;self.last=0.0
        self.log_path.parent.mkdir(parents=True,exist_ok=True)
    def _log(self,event):
        self.log_path.parent.mkdir(parents=True,exist_ok=True)
        with self.log_path.open('a',encoding='utf-8',newline='') as f:f.write(json.dumps(event,sort_keys=True)+'\n')
    def get(self,url:str,purpose:str,term_key:str,batch_identity:str)->bytes:
        delay=1-(time.monotonic()-self.last)
        if delay>0:time.sleep(delay)
        for attempt in range(self.max_attempts):
            with tempfile.TemporaryDirectory(dir=self.log_path.parent) as td:
                body=Path(td)/'body.part';headers=Path(td)/'headers.part';started=datetime.now(timezone.utc).isoformat()
                result=subprocess.run(curl_args(url,body,headers),shell=False,capture_output=True,text=True,timeout=35)
                meta={}
                try:meta=json.loads(result.stdout or '{}')
                except Exception:pass
                hdr=parse_headers(headers.read_bytes()) if headers.exists() else {}
                data=body.read_bytes() if body.exists() else b''
                event={'timestamp_utc':started,'logical_source':'English Wiktionary','endpoint':ENDPOINT,'url':url,'request_purpose':purpose,'requested_term':term_key,'batch_identity':batch_identity,'attempt_number':attempt+1,'curl_exit_code':result.returncode,'http_status':meta.get('http_code'),'ssl_verify_result':meta.get('ssl_verify_result'),'remote_ip':meta.get('remote_ip'),'response_size':len(data),'response_sha256':sha256_bytes(data) if data else None,'tls_backend':'Schannel','tls_verification':'enabled','http_date':hdr.get('date'),'status':'FAILED','failure_reason':sanitize_error(result.stderr)}
                if result.returncode==TLS_EXIT:
                    event['failure_reason']='CERTIFICATE_VALIDATION_FAILED: '+event['failure_reason'];self._log(event);raise GlobalTLSFailure(event['failure_reason'])
                if result.returncode==0 and meta.get('http_code')==200:
                    try:validate_json(data,purpose)
                    except Exception as exc:event['failure_reason']='JSON_OR_API_VALIDATION_FAILED: '+repr(exc);self._log(event);raise
                    event['status']='SUCCESS';event['failure_reason']=None;event['tls_verification']='enabled_and_passed';self._log(event);self.last=time.monotonic();return data
                self._log(event)
                if attempt+1>=self.max_attempts or result.returncode not in TRANSIENT_EXITS:raise RuntimeError(event['failure_reason'] or f'curl exit {result.returncode}')
                wait=1 if attempt==0 else 2
                ra=hdr.get('retry-after')
                if ra and ra.isdigit():wait=max(wait,int(ra))
                time.sleep(wait)
        raise AssertionError('unreachable')

def preflight(out:Path)->dict[str,Any]:
    url=ENDPOINT+'?action=query&meta=siteinfo&siprop=general&format=json'
    fetcher=SchannelFetcher(out/'network_requests.jsonl',max_attempts=1);data=fetcher.get(url,'siteinfo','__HOST_PREFLIGHT__','preflight')
    return {'result':'PASS','response_size':len(data),'response_sha256':sha256_bytes(data),'local_utc':datetime.now(timezone.utc).isoformat()}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--inputs',type=Path,required=True);ap.add_argument('--output-dir',type=Path,required=True);ap.add_argument('--mode',choices=['preflight','acquire','offline-build'],required=True);args=ap.parse_args()
    if args.mode=='preflight':print(json.dumps(preflight(args.output_dir/'raw_sources'),sort_keys=True));return
    _rows,terms=frozen_wiki.load_inputs(args.inputs)
    if args.mode=='acquire':
        fetcher=SchannelFetcher(args.output_dir/'raw_sources'/'network_requests.jsonl',3);failures=frozen_wiki.acquire(args.output_dir/'raw_sources',terms,fetcher);print(json.dumps({'term_count':len(terms),'failed_terms':failures},sort_keys=True))
    else:print(json.dumps(frozen_wiki.offline_build(args.output_dir/'raw_sources',terms,args.output_dir/'module4_external_lexical_snapshot.jsonl',args.output_dir/'module4_dev_term_manifest.csv'),sort_keys=True))
if __name__=='__main__':main()
