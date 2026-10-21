"""Offline static audit. No experiment imports, execution, installation or networking.

Writes only the public static-check report inside this non-Git candidate.
"""
import ast
import collections
import csv
import hashlib
import io
import ipaddress
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
REPORT = 'manifests/public_release_checks.json'


def main():
    assert not (ROOT / '.git').exists()
    files = sorted(p for p in ROOT.rglob('*') if p.is_file())
    result = dict(scope='All candidate files without size exclusions; no runtime execution',
                  python_count=0, notebooks=0, notebook_cells=0, syntax_errors=[],
                  notebook_errors=[], json_errors=[], privacy_candidates=[], source_dumps=[],
                  markdown_links=[], external_urls=[], csv_review=[], prohibited=[], import_audit=[])
    patterns = {
        'personal_home': r'(?i)(?:[A-Z]:[\\/]+Users[\\/]+[^\s"<>]+|/home/[^/\s"<>]+|/Users/[^/\s"<>]+)',
        'secret_signature': r'(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)',
        'email': r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}',
        'credential_assignment': r'''(?i)(?:api_key|access_token|secret_key|password)\s*[:=]\s*["'][A-Za-z0-9_+/=-]{20,}["']''',
    }
    def walk_json(value, path, pointer=''):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ('source', 'source_code', 'code') and isinstance(item, str) and len(item)>400 and re.search(r'\b(?:def|class) ', item):
                    result['source_dumps'].append(dict(path=path, pointer=pointer+'/'+key))
                walk_json(item, path, pointer+'/'+key)
        elif isinstance(value,list):
            for index,item in enumerate(value): walk_json(item,path,pointer+'/'+str(index))
    for file in files:
        rel=file.relative_to(ROOT).as_posix()
        if file.is_symlink() or file.stat().st_file_attributes & 1024:
            result['prohibited'].append(dict(path=rel,reason='link/reparse'))
        if '.git' in file.relative_to(ROOT).parts or file.suffix.lower() in ('.safetensors','.pt','.pth','.pkl','.bundle','.pyc'):
            result['prohibited'].append(dict(path=rel,reason='forbidden artifact'))
        raw=file.read_bytes()
        try: text=raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            result['prohibited'].append(dict(path=rel,reason='unreviewed binary'));continue
        for category, pattern in patterns.items():
            for match in re.finditer(pattern,text):
                result['privacy_candidates'].append(dict(path=rel, category=category,line=text.count('\n',0,match.start())+1))
        for url in re.findall(r'https?://[^\s"<>`\\)]+',text):
            host=urlsplit(url).hostname
            if host:
                private=False
                try: private=ipaddress.ip_address(host).is_private
                except ValueError: private=host.endswith(('.local','.internal')) or host=='localhost'
                if private: result['privacy_candidates'].append(dict(path=rel,category='private_endpoint'))
                result['external_urls'].append(dict(path=rel,host=host))
        if file.suffix=='.py':
            result['python_count']+=1
            try:
                tree=ast.parse(text,filename=rel)
                imports=[];dynamic=[]
                for node in ast.walk(tree):
                    if isinstance(node,ast.Import): imports.extend(a.name for a in node.names)
                    if isinstance(node,ast.ImportFrom): imports.append('.'*node.level+(node.module or ''))
                    if isinstance(node,ast.Call):
                        name=ast.unparse(node.func)
                        if any(k in name for k in ('import_module','spec_from_file_location','__import__','sys.path')):dynamic.append(dict(line=node.lineno,call=name))
                result['import_audit'].append(dict(path=rel,imports=sorted(set(imports)),dynamic=dynamic,
                    has_relative_path_logic=bool(re.search(r'__file__|sys\.path|\.\./',text))))
            except SyntaxError as e: result['syntax_errors'].append(dict(path=rel,line=e.lineno,message=e.msg))
        if file.suffix in ('.json','.ipynb'):
            try: data=json.loads(text)
            except ValueError as e:result['json_errors'].append(dict(path=rel,message=str(e)));continue
            walk_json(data,rel)
            if file.suffix=='.ipynb':
                result['notebooks']+=1
                if data.get('nbformat')!=4 or not isinstance(data.get('cells'),list) or not isinstance(data.get('metadata'),dict) or not isinstance(data.get('nbformat_minor'),int): result['notebook_errors'].append(dict(path=rel,issue='structure'))
                for i,cell in enumerate(data.get('cells',[])):
                    if cell.get('cell_type') not in ('markdown','raw','code') or not isinstance(cell.get('metadata'),dict) or not isinstance(cell.get('source'),(list,str)):
                        result['notebook_errors'].append(dict(path=rel,cell=i,issue='cell_structure'))
                    if cell.get('outputs') or cell.get('execution_count') is not None or cell.get('attachments'):
                        result['notebook_errors'].append(dict(path=rel,cell=i,issue='outputs/counts/attachments'))
                    if cell.get('cell_type')=='code':
                        result['notebook_cells']+=1
                        source=''.join(cell.get('source',[]))
                        try:
                            from IPython.core.inputtransformer2 import TransformerManager
                            source=TransformerManager().transform_cell(source)
                            ast.parse(source)
                        except Exception as e:result['notebook_errors'].append(dict(path=rel,cell=i,issue=type(e).__name__,message=str(e)))
        if file.suffix=='.csv':
            rows=list(csv.reader(io.StringIO(text)))
            result['csv_review'].append(dict(path=rel,rows=max(0,len(rows)-1),columns=rows[0] if rows else []))
        if file.suffix=='.md':
            body=re.sub(r'```.*?```','',text,flags=re.S)
            # Inline Markdown links plus reference definitions; raw URL reachability is not asserted.
            targets=re.findall(r'(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)',body)
            targets+=re.findall(r'^\s*\[[^\]]+\]:\s*(\S+)',body,re.M)
            for target in targets:
                target=target.strip().strip('<>')
                if re.match(r'[a-zA-Z]+:',target):continue
                target=unquote(target.split(' "')[0])
                path,_,fragment=target.partition('#')
                dest=(file.parent/path).resolve() if path else file
                entry=dict(path=rel,target=target,exists=dest.exists())
                if entry['exists'] and fragment and dest.suffix=='.md':
                    doc=dest.read_text(encoding='utf-8-sig')
                    headings=re.findall(r'^#{1,6}\s+(.+?)\s*#*$',doc,re.M)
                    slugs=[re.sub(r'[^\w\- ]','',h.lower()).replace(' ','-') for h in headings]
                    entry['anchor_exists']=fragment in slugs or f'id="{fragment}"' in doc
                result['markdown_links'].append(entry)
    result['external_urls']=list({(x['path'],x['host']):x for x in result['external_urls']}.values())
    result['notes']=[
        'Static imports are enumerated, not imported or executed. External/dynamic artifacts are not claimed resolvable.',
        'Known historical E8 syntax exception is reviewed separately.',
        'Source paths remain unchanged; candidate source hashes are compared independently to private HEAD.',
        'URL scan checks host types, not HTTP availability. No model/API calls.',
        'Pattern scanning is not a proof against every possible secret. Review candidates before release.',
        'No file-size cutoff; report does not scan its newly written version until the final independent pass.',
        'Notebook structure and all code cells checked with IPython transformation plus AST; nbformat package unavailable, no dependency installation performed.'
    ]
    (ROOT/REPORT).write_text(json.dumps(result,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('import_audit','external_urls','markdown_links','csv_review','notes')}))
    print('markdown_missing',json.dumps([x for x in result['markdown_links'] if not x['exists'] or x.get('anchor_exists') is False]))


if __name__=='__main__':main()
