"""Offline test suites only. Does not import launchers or start fits."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main(final=False):
    suites=[]
    for folder,pattern in [(HERE.parent,'test_*.py'),(HERE.parent/'e11c','test_e11c*.py'),(HERE.parent/'e11c_training','test_*.py'),(HERE.parent/'e11d_training','test_*.py'),(HERE,'test_*.py')]:
        result=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(folder),'-p',pattern,'-v'],capture_output=True,text=True)
        log=result.stdout+result.stderr
        name=('final_' if final else 'pre_')+folder.name+'.log'
        (HERE/'private').mkdir(exist_ok=True)
        (HERE/'private'/name).write_text(log,encoding='utf-8')
        match=re.search(r'Ran (\d+) tests?',log);skip=re.search(r'OK \(skipped=(\d+)\)',log)
        suites.append({'directory':str(folder),'pattern':pattern,'exit_code':result.returncode,'tests':int(match.group(1)) if match else 0,'skipped':int(skip.group(1)) if skip else 0,'log_sha256':__import__('hashlib').sha256((HERE/'private'/name).read_bytes()).hexdigest()})
        print(json.dumps(suites[-1]),flush=True)
    total=sum(s['tests'] for s in suites);skipped=sum(s['skipped'] for s in suites)
    ok=all(s['exit_code']==0 and s['tests']>0 for s in suites) and (not final or skipped==0)
    report={'status':'PASS' if ok else 'FAIL','total_tests':total,'passed':total-skipped,'skipped':skipped,'suites':suites}
    target=HERE/('FINAL_TESTS.json' if final else 'PRETRAINING_TESTS.json')
    target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(report['status'],report['passed'],'passed;',skipped,'skipped',flush=True)
    if not ok:raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--final',action='store_true');args=parser.parse_args();main(args.final)
