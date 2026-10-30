"""Report one completed fixed run and preserve the original blocker history."""
import common as c
import subprocess
import numpy as np,pandas as pd
from evaluate import metric,paired
def main():
 log=c.offline('report');runtime=c.runtime('evaluation');lock=c.verify_freeze();integrity=c.protected()
 complete=c.read(c.HERE/'evaluation_completed.json');assert complete['RF_fits']==5 and complete['OOF_evaluations']==1
 assert len(list(c.HERE.glob('fit_*_started.json')))==len(list(c.HERE.glob('fit_*_completed.json')))==5
 assert not list(c.HERE.glob('*failure.json'))
 result=c.read(c.V4/'evaluation/e6_v4_metrics.json');extraction=c.read(c.HERE/'extraction_contracts.json')
 frame=pd.read_csv(c.V4/'evaluation/paired_row_diagnostics.csv',float_precision='round_trip')
 oof=pd.read_csv(c.V4/'evaluation/e6_v4_oof_predictions.csv',float_precision='round_trip')
 assert len(frame)==frame.canonical_id.nunique()==len(oof)==561
 assert frame.canonical_id.tolist()==oof.canonical_id.tolist() and np.array_equal(frame.fold_id,oof.fold_id)
 assert np.array_equal(frame['E6-v4'],oof.prediction)
 assert metric(frame,'E6-v4')==result['diagnostics']['all_rows']['E6-v4']
 assert metric(frame,'E6-v3')==result['diagnostics']['all_rows']['E6-v3']
 assert paired(frame)==result['paired']
 for p,h in c.read(c.HERE/'feature_freeze.json')['files'].items():assert c.sha(c.V4/p)==h,p
 cached=[r for p in sorted((c.HERE/'chunks').glob('*.json')) for r in c.read(p)]
 assert len(cached)==561 and [r['canonical_id'] for r in cached]==frame.canonical_id.tolist()
 logs=list(c.HERE.glob('network_*.jsonl'));assert len(logs)==5 and all(p.stat().st_size==0 for p in logs)
 initial=c.read(c.HERE/'initial_integrity.json')
 status=subprocess.check_output(['git','status','--short'],cwd=c.ROOT,text=True)
 branch=subprocess.check_output(['git','branch','--show-current'],cwd=c.ROOT,text=True).strip()
 assert status==initial['git_status'] and branch==initial['branch']
 old=result['diagnostics']['all_rows']['E6-v3'];new=result['diagnostics']['all_rows']['E6-v4'];p=result['paired']
 lo,hi=p['bootstrap']['percentile_95_ci'];amendhash=c.sha(c.V4/'E6_V4_PROTOCOL_AMENDMENT_01.md')
 audit={'status':'PASS','utc':c.now(),**integrity,'old_report_archived_sha256':c.sha(c.HERE/'E6_V4_RESULTS_PHASE1_ARCHIVE.md'),
  'original_protocol_sha256':c.sha(c.V4/'E6_V4_PROTOCOL.md'),'amendment_sha256':amendhash,
  'execution_config_sha256':c.sha(c.HERE/'run_config.json'),'exact_encoding_versions':lock['encoding_runtime']['packages'],
  'evaluation_runtime':runtime,'network_attempts':0,'real_feature_rows':len(cached),'RF_fits':5,
  'baseline_fits':0,'OOF_evaluations':1,'official_test_access':False,'git_branch':branch,'git_status':status,
  'old_v4_report_update':'authorized; original preserved byte-for-byte in phase1 archive',
  'no_post_score_design_change':True}
 c.write(c.HERE/'final_integrity.json',audit)
 def fmt(x):return 'undefined' if x is None else f'{x:.10f}'
 table=[]
 for group,label in [('per_fold','Fold '),('per_task',''),('per_evidence','Evidence '),('DM_evidence','DM evidence ')]:
  for k,v in result['diagnostics'][group].items():
   a,b=v['E6-v3'],v['E6-v4']
   table.append(f"| {label}{k} | {b['n']} | {a['correct']} | {b['correct']} | {fmt(a['accuracy'])} | {fmt(b['accuracy'])} | {fmt(a['spearman'])} | {fmt(b['spearman'])} |")
 summary='\n'.join(table)
 stats='\n'.join(f"| {name} | {v['min']:.10f} | {v['max']:.10f} | {v['mean']:.10f} |" for name,v in extraction['statistics'].items())
 if p['net_correct']>0:
  interpretation='Το E6-v4 βελτίωσε την accuracy στο επαναχρησιμοποιημένο development σύνολο. Πρόκειται αποκλειστικά για development-only improvement του συνολικού block επτά χαρακτηριστικών· δεν απομονώνεται η συμβολή BERTScore από εκείνη των δομικών δεικτών.'
 elif p['net_correct']<0:
  interpretation='Το E6-v4 είχε χαμηλότερη accuracy από το E6-v3. Καταγράφεται το αρνητικό development-only αποτέλεσμα χωρίς redesign ή δεύτερο run. Η σύγκριση αφορά συνολικά τα επτά πρόσθετα χαρακτηριστικά και δεν απομονώνει τη συμβολή κάθε μέρους.'
 else:
  interpretation='Το νέο block δεν παρείχε πρόσθετη βελτίωση στην accuracy. Καταγράφεται το ίδιο correct count χωρίς redesign ή δεύτερο run· η σύγκριση αφορά το σύνολο των επτά νέων χαρακτηριστικών.'
 text=f'''# E6-v4 — τελικά αποτελέσματα

**PASS / COMPLETED. Μία προκαθορισμένη five-fold OOF αξιολόγηση, 561 δείγματα, 43 χαρακτηριστικά, ακριβώς 5 RF fits, 0 baseline fits. Adaptive exploratory development-only.**

| Έκδοση | Χαρακτηριστικά | Correct/N | Accuracy | Spearman |
|---|---:|---:|---:|---:|
| E6-v3 | 36 | {old['correct']}/561 | {old['accuracy']:.10f} | {old['spearman']:.10f} |
| E6-v4 | 43 | {new['correct']}/561 | {new['accuracy']:.10f} | {new['spearman']:.10f} |

Δ accuracy = **{p['accuracy_difference']:+.10f}**, δηλαδή **{100*p['accuracy_difference']:+.6f} ποσοστιαίες μονάδες**, net correct **{p['net_correct']:+d}/561**.

## Phase 1 — initial compatibility failure

Η αρχική official BERTScore προσπάθεια σταμάτησε πριν από πραγματικά features, RF fits ή αξιολόγηση με `OverflowError: int too big to convert`. Το ακριβές αρχικό report διατηρείται στο `execution/E6_V4_RESULTS_PHASE1_ARCHIVE.md` με το αρχικό SHA-256 `{initial['original_results_sha256']}`. Το αρχικό `E6_V4_PROTOCOL.md`, `config/run_config.json`, traceback και blocked-state manifest δεν ξαναγράφηκαν.

## Phase 2 — diagnosis

Το σφάλμα αναπαράχθηκε με το συνθετικό `a`. Η sentinel τιμή tokenizer.model_max_length περνούσε στο truncation backend του transformers 5.5.4/tokenizers 0.22.2. Το πρόβλημα ήταν environment compatibility. Η πλήρης διάγνωση και το ανεξάρτητο synthetic test διατηρούνται στο `compatibility_analysis/E6_V4_COMPATIBILITY_ANALYSIS.md`. Δεν προέκυψε E6-v4 score σε αυτή τη φάση.

## Phase 3 — amendment και pinned environment

Το νέο `E6_V4_PROTOCOL_AMENDMENT_01.md` αποθηκεύτηκε πριν από πραγματική εξαγωγή, fitting ή evaluation. SHA-256: **`{amendhash}`**. Επιλέχθηκε μόνο environment pinning, χωρίς custom BERTScore ή manual tokenizer max_length override.

Encoding: Python 3.11.9, official bert-score distribution 0.3.13 (upstream internal version 0.3.12), transformers 4.30.2, tokenizers 0.13.3, huggingface-hub 0.25.2, torch 2.11.0. Χρησιμοποιήθηκε το υπάρχον isolated venv με system-site-packages για αμετάβλητες κοινές εξαρτήσεις. Ο venv δεν προστέθηκε στο Git. RF evaluation: το αρχικό shroom_ensemble runtime με scikit-learn 1.8.0, numpy 2.4.4, scipy 1.17.1, pandas 3.0.2 και την πλήρη configuration E6-v3.

Model/tokenizer: `microsoft/deberta-large-mnli@{c.REV}`, το ίδιο pinned E3 checkpoint. Official mapping num_layers=18, idf=False, rescale_with_baseline=False, all_layers=False, use_fast_tokenizer=False, lang=None. Hash: `{lock['bertscore']['hash_string']}`. CPU float32, batch=2, torch threads4/4. Το 512 προήλθε αυτόματα από την επίσημη mapping του tokenizer. Όλα τα assets υπήρχαν ήδη τοπικά· δεν έγινε λήψη μοντέλου.

Επαναλήφθηκαν έξι synthetic cases (identity, omission, addition, number change, negation added/removed). **PASS** για finite P/R/F1, κατεύθυνση precision/recall και deterministic structural contracts. Μηδενικές απόπειρες δικτύου, κανένα override. Τα αποτελέσματα και οι ακριβείς τιμές βρίσκονται στο `execution/synthetic_contract.json`.

Το pre-extraction manifest `execution/run_config.json` πάγωσε protocol/amendment/report hashes, πακέτα, model provenance, inputs/IDs/folds, schema, πλήρη RF configuration, extraction/evaluator/reporter source hashes. Οι σφραγισμένες ρυθμίσεις δεν άλλαξαν μετά το score.

## Phase 4 — final frozen E6-v4 execution

Ακριβώς 561 canonical rows (493 development_model_agnostic + 68 trial, η ήδη εγκεκριμένη canonical development δεξαμενή), ίδιοι locked folds, ίδια σειρά 36 αρχικών χαρακτηριστικών με αριθμητική ισότητα και επτά νέες στήλες. Reference=tgt για DM/MT, src για PG, candidate=hyp. Τα exact saved label-free strings πέρασαν στην επίσημη API με την κανονική εσωτερική strip/tokenization. Το unchanged structure.py εφαρμόστηκε αποκλειστικά στους τέσσερις deterministic δείκτες.

Η εξαγωγή δεν διάβασε labels ή OOF predictions ως inputs. Η μήτρα πάγωσε πριν γίνει join των ανθρώπινων targets για RF/evaluation. Βασικό baseline ελέγχθηκε ξανά ανά ID/fold και αναπαρήγαγε ακριβώς 474/561 και το καταγεγραμμένο Spearman, χωρίς fit.

Missing values={extraction['missing_values']}, invalid values={extraction['invalid_values']}, NaN/Inf={extraction['nonfinite']}. Truncated references={extraction['reference_truncated']}, hypotheses={extraction['hyp_truncated']}; empty references={extraction['empty_references']}, hypotheses={extraction['empty_hyp']}. Οι original/used token lengths ανά ID και πλευρά αποθηκεύτηκαν στο `features/truncation_audit.csv`. Επαληθεύτηκε used=min(original,512).

Πλήρης εξαγωγή και συμβόλαια: **{extraction['seconds_total']:.3f}s**, περιλαμβάνει model load **{extraction['model_load_seconds']:.3f}s**. RF/evaluation διαδικασία: **{result['seconds']:.3f}s**. Οι χρόνοι δεν περιλαμβάνουν προηγούμενη διάγνωση ή ανθρώπινο χρόνο συγγραφής. 561/561 σειρές υπολογίστηκαν μία φορά και αποθηκεύτηκαν σε fixed chunks. Μία configuration, πέντε outer-fold RF fits, prediction clip [0,1], binary>=0.5. Δεν έγινε tuning ή δεύτερη variant.

| Νέο χαρακτηριστικό | Min | Max | Mean |
|---|---:|---:|---:|
{stats}

## Ανά fold, task και evidence

| Ομάδα | N | v3 correct | v4 correct | v3 accuracy | v4 accuracy | v3 Spearman | v4 Spearman |
|---|---:|---:|---:|---:|---:|---:|---:|
{summary}

Evidence 1=διαθέσιμος ορισμός, 0=χωρίς ορισμό. Οι εξωτερικοί ορισμοί αφορούν **αποκλειστικά DM** και εδώ χρησιμοποιούνται μόνο ως περιγραφική υποομάδα· δεν μπήκαν στα επτά νέα features. Το no-evidence σύνολο περιλαμβάνει επίσης MT/PG και δεν είναι αιτιώδης σύγκριση επίδρασης retrieval. Παρατίθεται επιπλέον DM-only διαχωρισμός.

## Paired diagnostics — descriptive exploratory statistics

**{p['corrected']} διορθώσεις**, **{p['regressions']} νέα λάθη**, net **{p['net_correct']:+d}**. Και τα δύο σωστά: {p['both_correct']}. Και τα δύο λάθος: {p['both_wrong']}.

Exact two-sided McNemar: **p={p['mcnemar_exact_two_sided_p']:.10f}**.

Paired-bootstrap 95% CI για accuracy(v4)-accuracy(v3): **[{lo:+.10f}, {hi:+.10f}]**, ή **[{lo*100:+.6f}, {hi*100:+.6f}] ποσοστιαίες μονάδες**.

Χρησιμοποιήθηκε ακριβώς η υπάρχουσα διαδικασία: binomtest(corrected, corrected+regressions,0.5), δύο όψεις· 10.000 paired resamples 561 κοινών row indices με numpy.default_rng(42), quantile 0.025/0.975. Το bootstrap αφορά παγωμένες OOF προβλέψεις και δεν επανεκπαιδεύει μοντέλα. Spearman: ανθρώπινο p_hallucination έναντι predictions rounded στα 12 δεκαδικά, accuracy με unrounded prediction>=0.5. Όλα τα IDs διορθώσεων/νέων λαθών βρίσκονται στο metrics JSON και οι 561 γραμμές στο paired_row_diagnostics.csv.

{interpretation}

Η παρέμβαση επιλέχθηκε μετά την exploratory ανάλυση σφαλμάτων E6-v2/v3. **Adaptive exploratory development-only** σε επαναχρησιμοποιημένο σύνολο. McNemar και bootstrap είναι **descriptive exploratory statistics**, χωρίς ανεξάρτητη confirmatory ερμηνεία ή διόρθωση για την adaptive επιλογή. Δεν χρησιμοποιήθηκε official test. Δεν έγινε επόμενο πείραμα.

## Integrity, παραδοτέα και Git

Τελικό audit **PASS**: 1784/1784 προστατευμένα αρχεία, E6-v3, διάγνωση και αρχικό πρωτόκολλο/config ανέπαφα. Τα 108 παλαιά v4 hashes επαληθεύτηκαν πριν από την εξουσιοδοτημένη ενημέρωση της αναφοράς· ο μοναδικός παλαιός τροποποιημένος στόχος είναι το παρόν E6_V4_RESULTS.md, με byte-identical ιστορικό archive. Αμετάβλητα όλα τα υπόλοιπα 107. Network attempts=**0**, real feature rows=**561**, RF fits=**5**, baseline fits=**0**, OOF evaluations=**1**. Δεν έγινε official-test access, retrieval, API/LLM call, αλλαγή synthetic δεδομένων ή git add/commit/push/tag.

Νέα αρχεία: amendment, `execution/` κώδικας/config/manifests/smoke/cache/logs/audits και archive, `features/` επτά νέα features και πλήρης μήτρα 43, `evaluation/` 561 OOF predictions, fold caches, metrics και paired diagnostics. Τροποποιήθηκε μόνο η παρούσα τελική αναφορά. Τα ακριβή νέα paths/hashes καταγράφονται στο `execution/completion_manifest.json`. Ο venv της διάγνωσης επαναχρησιμοποιήθηκε χωρίς αλλαγή.

Branch `{branch}`, git status:

```text
{status.rstrip()}
```

Η ένδειξη Git παραμένει ίδια επειδή ο v4 φάκελος ήταν ήδη untracked. **STOP μετά το E6-v4.**
'''
 assert c.sha(c.V4/'E6_V4_RESULTS.md')==initial['original_results_sha256']
 (c.V4/'E6_V4_RESULTS.md').write_text(text,encoding='utf-8')
 c.protected(allow_updated_report=True);c.verify_freeze()
 files={}
 for directory in [c.HERE,c.V4/'features',c.V4/'evaluation']:
  for path in directory.rglob('*'):
   if path.is_file() and 'tmp' not in path.relative_to(c.V4).parts and '__pycache__' not in path.parts:
    files[path.relative_to(c.V4).as_posix()]=c.sha(path)
 for name in ['E6_V4_RESULTS.md','E6_V4_PROTOCOL_AMENDMENT_01.md']:files[name]=c.sha(c.V4/name)
 c.write(c.HERE/'completion_manifest.json',{'status':'COMPLETED','created_utc':c.now(),'files':files,'excluded':['execution/tmp','self manifest'],'RF_fits':5,'OOF_evaluations':1,'real_feature_rows':561})
 print({'status':'PASS','amendment_sha256':amendhash,'E6-v3':old,'E6-v4':new,'paired':{k:v for k,v in p.items() if not k.endswith('_ids')},'integrity':integrity},flush=True)
if __name__=='__main__':main()
