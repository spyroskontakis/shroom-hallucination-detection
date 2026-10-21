"""Add preregistered overlap and paired diagnostics to locked Module 4 metrics."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import binomtest,spearmanr
from sklearn.metrics import accuracy_score

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def metrics(f,pcol):
 p=f[pcol].to_numpy(float);return {'n':int(len(f)),'accuracy':float(accuracy_score(f.label_bin,(p>=.5).astype(int))),'spearman':float(spearmanr(f.p_hallucination,np.round(p,12)).statistic)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--mixed',type=Path,required=True);ap.add_argument('--e3',type=Path,required=True);ap.add_argument('--e5',type=Path,required=True);ap.add_argument('--overlap',type=Path,required=True);ap.add_argument('--metrics',type=Path,required=True);a=ap.parse_args()
 m=pd.read_csv(a.mixed)[['canonical_id','task','label_bin','p_hallucination']];e3=pd.read_csv(a.e3).rename(columns={'prediction':'e3'});e5=pd.read_csv(a.e5).rename(columns={'prediction':'e5'});o=pd.read_csv(a.overlap).rename(columns={'example_id':'canonical_id'})
 f=m.merge(e3,on='canonical_id',validate='one_to_one').merge(e5,on=['canonical_id','fold_id'],validate='one_to_one').merge(o,on='canonical_id',validate='one_to_one')
 if len(f)!=561:raise ValueError('Expected complete 561-row join')
 exact=f.exact_normalized_definition_tgt_match.astype(bool);c3=(f.e3>=.5)==f.label_bin;c5=(f.e5>=.5)==f.label_bin
 b=int((~c3&c5).sum());c=int((c3&~c5).sum());rng=np.random.default_rng(42);d=(c5.astype(int)-c3.astype(int)).to_numpy();boots=np.array([d[rng.integers(0,len(d),len(d))].mean() for _ in range(10000)])
 result=json.loads(a.metrics.read_text(encoding='utf-8'))
 result['overlap_audit']={'exact_normalized_definition_tgt_match_rows':int(exact.sum()),'all_exact_match_instances':int(f.exact_match_count.sum()),'exact_rows':{'E3':metrics(f[exact],'e3'),'E5':metrics(f[exact],'e5')},'excluding_exact_rows':{'E3':metrics(f[~exact],'e3'),'E5':metrics(f[~exact],'e5')},'corrected_by_e5_exact_rows':int((~c3&c5&exact).sum()),'introduced_errors_exact_rows':int((c3&~c5&exact).sum()),'corrected_by_e5_nonexact_rows':int((~c3&c5&~exact).sum()),'introduced_errors_nonexact_rows':int((c3&~c5&~exact).sum())}
 result['paired_diagnostics']={'e3_correct_e5_wrong':c,'e3_wrong_e5_correct':b,'net_correct_predictions':b-c,'mcnemar_exact_two_sided_p':float(binomtest(b,b+c,.5).pvalue) if b+c else 1.0,'paired_bootstrap_accuracy_difference_e5_minus_e3':{'replicates':10000,'seed':42,'observed':float(d.mean()),'percentile_95_ci':[float(np.quantile(boots,.025)),float(np.quantile(boots,.975))]}}
 result['fold_diagnostics']={str(k):{'E3':metrics(g,'e3'),'E5':metrics(g,'e5')} for k,g in f.groupby('fold_id')}
 result['input_sha256']['exact_overlap_audit']=sha(a.overlap);a.metrics.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 print(json.dumps({'metrics_sha256':sha(a.metrics),'exact_rows':int(exact.sum()),'corrected':b,'introduced':c,'bootstrap_ci':result['paired_diagnostics']['paired_bootstrap_accuracy_difference_e5_minus_e3']['percentile_95_ci']},sort_keys=True))
if __name__=='__main__':main()
