"""Summarize saved rows and the explicit 97-case qualitative review, without fitting."""
from pathlib import Path
import json,statistics,collections,csv,hashlib
OUT=Path(__file__).resolve().parent
def read(n):return json.loads((OUT/n).read_text(encoding='utf-8'))
def put(n,v):
    with (OUT/n).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
def esc(s):return str(s).replace('|','\\|').replace('\n',' ')
def main():
    rows=read('diagnostics_intermediate.json');q=read('quantitative_summary.json');a=read('input_verification.json')
    selected=[r for r in rows if r['correctness_group']!='both_correct'];notes=read('qualitative_notes.json')
    assert len(selected)==len(notes)==97 and [n[0] for n in notes]==list(range(1,98))
    for r in rows:r.update(qualitative_reviewed=0,qualitative_tags='',qualitative_note='')
    for r,(i,t,n) in zip(selected,notes):r.update(qualitative_reviewed=1,qualitative_tags=t,qualitative_note=n)
    assert sum(r['qualitative_reviewed'] for r in rows)==97
    tagged={r['canonical_id']:{'tags':r['qualitative_tags'].split(';'),'note':r['qualitative_note']} for r in selected}
    put('qualitative_review_by_id.json',tagged)
    put('diagnostic_table.json',{'columns':list(rows[0]),'rows':rows})
    tags=collections.Counter(t for r in selected for t in r['qualitative_tags'].split(';'))
    common=collections.Counter(t for r in selected if r['correctness_group']=='both_wrong' for t in r['qualitative_tags'].split(';'))
    high=lambda r:float(r['nli2_ref_hyp_entailment'])>=.9 and float(r['hhem_ref_hyp_consistency'])>=.9
    false_negative=[r for r in rows if r['correctness_group']=='both_wrong' and r['frozen_binary_label']==1]
    signals={'high_nli_and_hhem_common_false_negatives':len([r for r in false_negative if high(r)]),
             'common_false_negatives':len(false_negative),
             'high_signal_ids':[r['canonical_id'] for r in false_negative if high(r)],
             'tags_reviewed97':dict(tags),'tags_common78':dict(common)}
    changes=[r for r in selected if r['correctness_group'] in ['v3_corrected','v3_new_error']]
    signals['changes_both_margins_le_0_10']=sum(r['v2_distance_to_0_5']<=.1 and r['v3_distance_to_0_5']<=.1 for r in changes)
    signals['changes_at_least_one_margin_le_0_10']=sum(min(r['v2_distance_to_0_5'],r['v3_distance_to_0_5'])<=.1 for r in changes)
    # Reference is a stored source-specific choice. This is a diagnostic, not new extraction for learning.
    signals['same_tgt_hyp_groups']=[[(r['canonical_id'],r['fold'],r['correctness_group']) for r in selected if r['tgt']==x['tgt'] and r['hyp']==x['hyp']]
                                   for x in selected if x['canonical_id'].startswith('HDEV_0150')]
    put('qualitative_summary.json',signals)
    lines=['# Διαγνωστική ανάλυση E6-v2 και E6-v3','',
           'Η προσθήκη HHEM αλλάζει την ορθότητα 19 γραμμών: 10 διορθώσεις και 9 νέα λάθη, με καθαρό +1. '
           'Το μεγαλύτερο υπόλοιπο είναι τα 78 κοινά λάθη. Η ανάγνωση και των 97 περιπτώσεων δείχνει δύο διαφορετικά ζητήματα: '
           'πραγματικές απώλειες/μεταβολές σημασίας που οι evaluators συχνά δέχονται, και περιπτώσεις όπου τα κείμενα ή οι ανθρώπινες ψήφοι '
           'δεν στηρίζουν εύκολη διάγνωση. Οι δεύτερες δεν επιτρέπεται να μετατραπούν αυθαίρετα σε «λάθος ετικέτες».','',
           '**Exploratory, development-only σε επαναχρησιμοποιημένο σύνολο.** Δεν έγινε νέο πείραμα, training, inference, retrieval ή API call. '
           'Η ανάλυση αφορά αποθηκευμένες OOF προβλέψεις και δεν αποτελεί ανεξάρτητη αξιολόγηση.','',
           '## 1. Επαλήθευση και αρχεία','',
           '| Έλεγχος | Παρατηρημένο |','|---|---:|',
           '| Canonical IDs / locked folds | 561 / 5 |','| E6-v2 σωστά | 473/561 |','| E6-v3 σωστά | 474/561 |',
           '| Και τα δύο σωστά | 464 |','| Και τα δύο λάθος | 78 |','| Διορθώσεις v3 | 10 |','| Νέα λάθη v3 | 9 |','',
           'Η σύνδεση έγινε με canonical ID, με έλεγχο μοναδικότητας, πλήρους πληθυσμού και folds. '
           'Οι συνεχείς προβλέψεις συγκρίθηκαν ακριβώς με το αποθηκευμένο paired_row_diagnostics. '
           'Οι binary προβλέψεις επαληθεύτηκαν με το αρχικό ≥0.5 και τα labels/p_hallucination με το canonical manifest. '
           'Τα 34 παλιά features διατηρούνται αριθμητικά ακριβώς στα 36 του v3. Τα A/C ζεύγη και οι HHEM scores συμφωνούν με τα αποθηκευμένα αρχεία.', '',
           f"Επαληθεύτηκαν SHA-256 για **{len(a['protected_sha256'])} προηγούμενα αρχεία** στην αρχή και επανελέγχονται στο τελικό manifest της ανάλυσης. "
           'Τα πρωτόκολλα, completion manifests και προηγούμενες αναφορές δεν ενημερώθηκαν. Όλα τα νέα αρχεία βρίσκονται στο error_analysis/.', '',
           'Παραδοτέο: **E6_DIAGNOSTIC_TABLE.csv**, 561 γραμμές, με ολόκληρα src/tgt/hyp, επιλεγμένο ορισμό/evidence ID, '
           'task/fold, ανθρώπινο p και frozen label, αρχική λίστα ψήφων, συνεχείς/binary προβλέψεις, ομάδα ορθότητας, αποστάσεις από 0.5, '
           'και τα 36 αποθηκευμένα features. Περιλαμβάνονται τα αρχικά NLI, το δεύτερο NLI A/B/C, HHEM reference/definition και raw logits. '
           'Οι στήλες qualitative_* είναι χωριστές ερμηνευτικές σημειώσεις, όχι νέες ετικέτες ή features εκπαίδευσης. Οι 464 μη επιλεγμένες γραμμές '
           'έχουν qualitative_reviewed=0· δεν θεωρούνται ελεγμένες ως προς την ποιότητα κειμένου.', '',
           'Δεν λείπει κανένα src/tgt/hyp ή λίστα ψήφων. Λείπει εξωτερικός ορισμός σε 368 γραμμές: κενό CSV πεδίο, '
           'evidence_available=0 και καταγραφή στο missing_fields. Τα μηδενικά definition scores είναι ο προβλεπόμενος fallback, '
           'όχι αποτέλεσμα inference και όχι ένδειξη βέβαιης αντίφασης. Το raw definition logit μένει κενό. '
           'Το HDEV_0002_3d51bbb57230 έχει tgt="."· διατηρήθηκε ακριβώς και σημειώθηκε ως placeholder, όχι επινοημένος ορισμός. '
           'Υπάρχουν επίσης alias/inflection/circular references που είναι μη κενά αλλά ενδέχεται να είναι πληροφοριακά ανεπαρκή.', '',
           'Πηγές: codex/canonical_human_development_manifest.csv, canonical_fold_assignments.csv, '
           'E6-v2 inputs/definition_reference_mapping.json και nli_pairs_label_free.json, τα δύο παγωμένα feature CSV, '
           'τα δύο OOF CSV, E6-v3 evaluation/paired_row_diagnostics.csv και features/hhem_pair_scores.csv. '
           'Ακριβή paths/hashes και εκτελέσιμος κώδικας αναπαραγωγής διατηρούνται στα υποστηρικτικά αρχεία αυτού του φακέλου.', '',
           '## 2. Πληθυσμοί και error rates','',
           'Κάθε ποσοστό λάθους είναι errors/N της αντίστοιχης πλήρους ομάδας των 561, όχι ποσοστό μεταξύ των 97 εξεταζόμενων λαθών/αλλαγών.', '']
    def table(title,groups):
        lines.extend([f'### {title}','', '| Ομάδα | N | Λάθη v2 | Error rate v2 | Λάθη v3 | Error rate v3 | Κοινά λάθη | Διορθώσεις | Νέα λάθη |',
                      '|---|---:|---:|---:|---:|---:|---:|---:|---:|'])
        for key,s in groups.items():
            lines.append(f"| {key} | {s['n']} | {s['v2_errors']} | {s['v2_error_rate']:.2%} | {s['v3_errors']} | {s['v3_error_rate']:.2%} | {s['both_wrong']} | {s['v3_corrected']} | {s['v3_new_error']} |")
        lines.append('')
    table('Ανά task',q['by_task']);table('Διαθεσιμότητα ορισμού',{'Χωρίς ορισμό':q['by_evidence']['0'],'Με ορισμό':q['by_evidence']['1']})
    lines+=['**Όλοι οι 193 ορισμοί είναι DM.** MT και PG δεν έχουν κανέναν. Επομένως το υψηλότερο συνολικό error rate '
            'στις γραμμές με ορισμό δεν αποδεικνύει ότι ο ορισμός βλάπτει. Η ορθή περιγραφική σύγκριση εντός DM δίνεται παρακάτω. '
            'Ούτε αυτή είναι αιτιώδης: οι 18 DM χωρίς ορισμό μπορεί να είναι δυσκολότεροι/διαφορετικοί όροι.', '']
    table('Task × ορισμός (0=χωρίς, 1=με)',q['by_task_evidence'])
    table('Κάθε διαθέσιμη τιμή ανθρώπινου p_hallucination',q['by_human_probability'])
    table('Συμφωνία annotators',{'Ομοφωνία':q['by_disagreement']['0'],'Διαφωνία':q['by_disagreement']['1']})
    lines+=['Οι αποθηκευμένες ψήφοι είναι διαθέσιμες για όλους: 493 γραμμές με 5 ψήφους και 68 με 3. '
            'Επαληθεύτηκε ότι το ποσοστό ψήφων Hallucination ισούται με το αποθηκευμένο p. '
            'Οι τιμές 1/3 και 2/3 εμφανίζονται ως τα ακριβή αποθηκευμένα decimals στον πίνακα· δεν δημιουργήθηκαν νέες κλάσεις.', '',
            '**68/78 κοινά λάθη** έχουν διαφωνία (δείκτης σύνθεσης των κοινών λαθών). '
            'Τα 46/78 βρίσκονται στις τιμές p=0.4 ή 0.6. Στον πλήρη πληθυσμό αυτών των δύο τιμών, '
            'το v3 έχει 49/144 λάθη (34.03%), έναντι 10/229 (4.37%) στις ομόφωνες γραμμές. '
            'Και τα 9 νέα λάθη έχουν διαφωνία. Αυτό δείχνει συσχέτιση με οριακή ανθρώπινη κρίση, όχι ότι κάθε τέτοια ετικέτα είναι εσφαλμένη.', '',
            '## 3. Απόσταση από το σταθερό threshold','',
            'Ορίζεται d=|OOF prediction−0.5|. Πρόκειται για αριθμητική απόσταση από το όριο απόφασης, **όχι βαθμονομημένη εμπιστοσύνη**. '
            'Τα bins είναι περιγραφικά, δεν χρησιμοποιήθηκαν για επιλογή ή αλλαγή threshold. Σε κάθε στήλη μοντέλου ο παρονομαστής '
            'είναι ο δικός του πληθυσμός που βρίσκεται στο συγκεκριμένο διάστημα.', '',
            '| d | N v2 | Λάθη v2 / N | N v3 | Λάθη v3 / N |','|---|---:|---:|---:|---:|']
    for name,label in [('0_to_0.05','[0, 0.05]'),('0.05_to_0.10','(0.05, 0.10]'),('0.10_to_0.20','(0.10, 0.20]'),('above_0.20','>0.20')]:
        x=q['margins']['v2'][name];z=q['margins']['v3'][name]
        lines.append(f"| {label} | {x['n']} | {x['v2_errors']}/{x['n']} ({x['v2_error_rate']:.2%}) | {z['n']} | {z['v3_errors']}/{z['n']} ({z['v3_error_rate']:.2%}) |")
    lines+=['','| Ομάδα | N | Διάμεσο d v2 | Διάμεσο d v3 |','|---|---:|---:|---:|']
    for g in ['both_correct','both_wrong','v3_corrected','v3_new_error']:
        x=q['margins']['v2'][g];z=q['margins']['v3'][g]
        lines.append(f"| {g} | {x['n']} | {x['median']:.6f} | {z['median']:.6f} |")
    lines+=['',f"Στις 19 αλλαγές, {signals['changes_both_margins_le_0_10']}/19 έχουν d≤0.10 και στα δύο μοντέλα, "
            f"ενώ {signals['changes_at_least_one_margin_le_0_10']}/19 σε τουλάχιστον ένα. "
            'Όμως 54/78 κοινά λάθη του v3 έχουν d>0.10, και 28/78 έχουν d>0.20. '
            'Άρα το υπόλοιπο δεν περιορίζεται σε λίγες προβλέψεις που βρίσκονται δίπλα στο threshold. '
            'Δεν έγινε sweep ορίου ή υπολογισμός υποθετικής βελτίωσης από άλλο threshold.', '',
            '## 4. Ποιοτικά μοτίβα: παρατηρήσεις και αβεβαιότητα','',
            'Διαβάστηκαν και οι 78 κοινές αστοχίες και οι 19 αλλαγές, με src/tgt/hyp, διαθέσιμο ορισμό, ψήφους και scores. '
            'Οι σημειώσεις είναι μία ερμηνευτική ανάγνωση χωρίς δεύτερο ανεξάρτητο annotator. Τα tags επικαλύπτονται και καταγράφουν '
            'όψεις του κειμένου, όχι αποδεδειγμένες αιτίες σφάλματος. Το πλήρες μητρώο 97 περιπτώσεων βρίσκεται στο παράρτημα και στο CSV.', '',
            '### Σχέσεις και κάλυψη περιεχομένου που διαφεύγουν παρά υψηλά scores','',
            'Συγκεκριμένα παραδείγματα κοινών false negatives:', '',
            '| ID | Reference → hyp (σύντομο απόσπασμα) | Παρατήρηση | NLI2 entailment / HHEM ref |',
            '|---|---|---|---|',
            '| HDEV_0452_e0e32cb329e4 | We **all** love you → We love you **all** | Το all μετακινείται από υποκείμενο σε αντικείμενο | 0.982 / 0.923 |',
            '| HDEV_0350_ed417a3f5146 | Listening is not **his** forte → ability to listen **to him** | Αντιστροφή σημασιολογικού ρόλου | 0.917 / 0.986 |',
            '| HDEV_0531_581fed84fb7e | order to **board the ship** → orders **the ship on board** | Αλλαγή ρόλου του ship | 0.981 / 0.996 |',
            '| HDEV_0443_fe65c7fd6a4c | **remind you** → **remember** | Αλλαγή ενέργειας και αποδέκτη | 0.941 / 0.999 |',
            '| HDEV_0317_993524fd873e; HDEV_0484_13ea852c4bbb | called him **names** → called him | Παράλειψη της λέξης που σχηματίζει το ιδίωμα | 0.995 / 0.881; 0.997 / 0.998 |',
            '| HDEV_0391_b2659165b367 | near **the pond** → play around | Απώλεια κρίσιμου χωρικού περιορισμού | 0.944 / 0.609 |',
            '| HDEV_0521_dbcda3883593 | five, six, seven, eight → **a number between** five and eight | Ακολουθία πολλών αριθμών γίνεται μία τιμή εύρους | 0.798 / 0.968 |','',
            f"Σε **{signals['high_nli_and_hhem_common_false_negatives']}/{len(false_negative)} κοινά false negatives**, NLI2 reference entailment και HHEM reference "
            'είναι και τα δύο ≥0.9. Το 0.9 χρησιμοποιείται μόνο ως περιγραφικό φίλτρο εδώ. Υψηλή συμφωνία δύο evaluators δεν αρκεί '
            'για να αποκλείσει υποστηριζόμενη μόνο εν μέρει ή αλλαγμένη σχέση. Δεν εξάγεται αιτιώδης εξήγηση του RF από αυτά τα scores.', '',
            '### DM: σημασία στο συμφραζόμενο και επάρκεια του ορισμού','',
            'Το DM έχει τα περισσότερα κοινά λάθη (39) και το μεγαλύτερο συνολικό error rate του v3 (42/211). '
            'Στο HDEV_0039_4c1429fba334 το condoled chief χάνει Grand Council/Confederacy και γίνεται γενικός Native American chief. '
            'Στο HDEV_0160_0aa56695a651 το transportive χάνει serving to transport και γίνεται pertaining to transport. '
            'Και στα δύο, η γενικότητα μπορεί να είναι λογικά συμβατή με το reference χωρίς να αποτελεί επαρκή definition.', '',
            'Κυκλικοί/μορφολογικοί ορισμοί εμφανίζονται σε HDEV_0041_42fda0e8fe9e (The nock of an arrow), '
            'HDEV_0135_d65b9d22ccf2 (Alternative form of Anglo-Indian English), HDEV_0185_f90c56d6efe5 (Alternative form of all-cargo). '
            'Δεν έχουν όλοι το ίδιο label, άρα η κυκλικότητα δεν πρέπει να γίνει χειροποίητος κανόνας hallucination. '
            'Στο HDEV_0501_f3ea1577ef3d, το reference see walking, simulator είναι ασθενές αλλά η hyp device that simulates walking εύλογη· το v3 εισάγει λάθος.', '',
            '### Ακατάλληλος εξωτερικός ορισμός','',
            '| ID | Συμφραζόμενο / αποθηκευμένος ορισμός | Παρατήρηση |','|---|---|---|',
            '| HDEV_0029_4a764da5d0c6 | smoking toke / give a gratuity | Άσχετη σημασία casino· HHEM definition σχεδόν 0 |',
            '| HDEV_0495_79caccfcd7d2 | ναυτικό pigstick / pigs hunted for sport | Άσχετο θεματικό πεδίο |',
            '| HDEV_0173_c13463fbad38 | pervert one’s words / a perverted person | Ρήμα έναντι ονοματικού ορισμού |',
            '| HDEV_0162_76576f764096 | weary way / to make or become weary | Επίθετο και αιτιακός ρόλος έναντι ρήματος |',
            '| HDEV_0010_105de38d60f4 | ingenuity / an ingenuous action | Πιθανή διαφορετική σημασία, όχι το inventive problem-solving του tgt |',
            '| HDEV_0066_a1a4480126a7 | idiomatic slam dunk / to perform a slam dunk | Κυκλικό/μη κατάλληλο για τη συγκεκριμένη ιδιωματική χρήση |','',
            'Αυτές είναι έξι συγκεκριμένες ενδείξεις από τις επιλεγμένες 97 περιπτώσεις, όχι εκτίμηση συχνότητας κακών ορισμών στους 193. '
            'Δεν εξετάστηκαν συστηματικά όλοι οι ορισμοί των 464 both-correct. Δεν έγινε reranking. Η availability σημαίνει παρουσία, όχι ποιότητα.', '',
            '### Προσθήκες, άρνηση και γλωσσική ποιότητα','',
            'Στο HDEV_0311_6bc1ac73803c προστίθεται I’ll be right there, στο HDEV_0276_c4aa2407900f προστίθεται in the last year '
            'και died γίνεται killed. Παρά τις ορατές διαφορές, τα frozen labels είναι 0. Στο HDEV_0260_b4c26b7aeb70 το μικρό '
            'as we can see έχει label 1. Άρα η έκταση μιας προσθήκης δεν εξηγεί από μόνη της το annotation.', '',
            'Το HDEV_0114_b22b4aba394f χάνει το not completely cosmopolitan σε κυκλικό ορισμό. '
            'Αντίθετα, τα HDEV_0214_6a1a853abe66 και HDEV_0274_f84c99976fbf κρατούν την άρνηση· η παρουσία άρνησης δεν αποδεικνύει '
            'σφάλμα χειρισμού της. Οι αριθμοί δεν αναδεικνύονται ως κυρίαρχο ξεχωριστό μοτίβο: το HDEV_0521 δείχνει μεταβολή εύρους/πληθικότητας, '
            'ενώ η διόρθωση HDEV_0426_19131419bfaf διατηρεί one square meter / about one watt. '
            'Δεν ελέγχεται εδώ η εξωτερική πραγματολογική ορθότητα της ίδιας της πηγής.', '',
            'Αδέξιες διατυπώσεις όπως HDEV_0221_56b430431412 (kind of your time) και HDEV_0274 (word of the word) '
            'μπορεί να μειώνουν γλωσσική ποιότητα χωρίς νέο γεγονός. Δεν ταυτίζονται grammar, informativeness και hallucination.', '',
            '### Annotator disagreement και ασάφεια reference','',
            'HDEV_0124_a7534fc3e3f8: quality or state of being rational → quality of being rational, αλλά p=0.6. '
            'HDEV_0003_530e1aebd9d8 και HDEV_0057_06ee5a42d09e: πολύ κοντινές παραφράσεις, ομόφωνο label 0, αλλά δύο false positives. '
            'Αντίστροφα, HDEV_0181_cbd09f87b3cd (climb down/back → climb again) έχει p=0.2. '
            'Τα παραδείγματα υποδεικνύουν ζητήματα ορίων του annotation, όχι άδεια επανετικετοποίησης.', '',
            'HDEV_0528_9a43fd1a1005: το γαλλικό l’ δεν καθορίζει από μόνο του φύλο· tgt him και hyp her μπορεί να είναι δύο '
            'δυνατές αποδόσεις χωρίς επιπλέον πλαίσιο. Οι evaluators συγκρίνουν με το συγκεκριμένο tgt, δημιουργώντας πιθανή reference-induced απόκλιση. '
            'Στο HDEV_0299_153fa59143c2 η hyp football συμφωνεί με το tgt football, ενώ το src έχει soccer· το v3 παρ’ όλα αυτά εισάγει λάθος.', '',
            'Δεν εξισώνεται NLI neutral με hallucination. Στις διορθώσεις HDEV_0239_d49c203a9e3c και HDEV_0278_6682ff7079d4 '
            'τα NLI2 neutral είναι 0.991/0.978, ενώ HHEM 0.946/0.975 και label 0. Υπάρχουν επίσης false negatives με υψηλό entailment, '
            'όπως στα παραδείγματα σχέσεων παραπάνω.', '',
            '### Τι δείχνουν οι 19 αλλαγές','',
            'Και οι 19 έχουν αναλυτική σημείωση στο παράρτημα. Οι διορθώσεις περιλαμβάνουν τόσο εύλογες παραφράσεις όσο και κυκλικές/γενικές απαντήσεις. '
            'Τα νέα λάθη περιλαμβάνουν HDEV_0358_32089e1c6619 (put it anywhere → wherever you go, HHEM 0.982), '
            'HDEV_0538_f9038a3e99ed (αδιαφορία → μη εμπλοκή, HHEM 0.997) και HDEV_0299 (soccer/football, HHEM 0.047). '
            'Αυτό δεν στηρίζει έναν απλό κανόνα «ακολούθησε το HHEM». Η προσθήκη features αλλάζει και τα δέντρα του RF, '
            'επομένως κάθε αλλαγή πρόβλεψης δεν αποδίδεται αποκλειστικά σε ένα επιμέρους HHEM score.', '',
            'Τα HDEV_0150_3f30690a6d38 και HDEV_0498_901cecdbe33b έχουν ίδιο tgt/hyp hatfish και ίδια αποθηκευμένα NLI2 scores και πρακτικά ίδια HHEM scores (διαφορά reference consistency περίπου 1,5×10⁻⁸), '
            'με διαφορετική τυπογραφία src, ψήφους και canonical IDs. Τα HDEV_0317/HDEV_0484 είναι επίσης πολύ όμοιο σημασιολογικό παράδειγμα. '
            'Τα canonical IDs δεν εγγυώνται ανεξαρτησία των ποιοτικών μηχανισμών. Τα folds παραμένουν ανέπαφα.', '',
            '## 5. Μία κύρια επόμενη παρέμβαση — πρόταση, δεν εκτελέστηκε','',
            '**Ένα μικρό, προκαθορισμένο block δομικής κάλυψης και σχέσεων reference–hyp**, που θα επισημαίνει '
            'παράλειψη κύριας ενέργειας/ορίσματος και μετατόπιση ποσοδείκτη ή σημασιολογικού ρόλου. '
            'Αφετηρία είναι τα saved reference/hyp, με τις ίδιες task-specific επιλογές reference. '
            'Στόχος δεν είναι να προσθέσει άλλον γενικό neural evaluator, αλλά να εκθέσει στο RF την τοπική διαφορά '
            'που χάνεται σε μία συνολική σημασιολογική βαθμολογία.', '',
            '**Στήριξη από παρατηρήσεις:** all στο HDEV_0452, his/to him στο HDEV_0350, board the ship στο HDEV_0531, '
            'remind/remember στο HDEV_0443 και η παράλειψη names στα HDEV_0317/HDEV_0484. '
            '**Υπόθεση:** ρητή τοπική/δομική αντιστοίχιση θα μπορούσε να προσφέρει συμπληρωματική πληροφορία ακόμη όταν entailment/consistency είναι υψηλά. '
            'Αυτό δεν έχει δοκιμαστεί. Οι ήδη υπάρχοντες NLI2 A/B scores παρέχουν κατεύθυνση, επομένως μια απλή επανάληψη reverse NLI δεν αρκεί ως νέα ιδέα.', '',
            '**Πρακτικότητα CPU:** token/lemma alignment και λίγα προκαθορισμένα checks λειτουργούν χωρίς νέο μεγάλο encoder. '
            'Για σχέσεις υποκειμένου/αντικειμένου θα χρειαζόταν κατάλληλος CPU dependency parser ή σαφώς περιορισμένες επιφανειακές ενδείξεις. '
            'Δεν ελέγχθηκε ή εγκαταστάθηκε parser εδώ, ούτε μετρήθηκε ο χρόνος του. Η αναμενόμενη επιβάρυνση για 561 σύντομα ζεύγη είναι '
            'μικρότερη από ακόμη μία πλήρη neural εξαγωγή· η εκτίμηση είναι τεχνική υπόθεση, όχι benchmark. '
            'Ο κίνδυνος είναι σφάλματα parsing, ψευδείς διαφορές από σωστές παραφράσεις και ασθενή DM references. '
            'Οι ενδείξεις θα ήταν features, ποτέ αυτόματη αναταξινόμηση ετικετών. Πριν από οποιαδήποτε μελλοντική αξιολόγηση απαιτείται '
            'ξεχωριστή έγκριση και πάγωμα της ακριβούς υλοποίησης. Δεν προτείνεται αλλαγή threshold ή τωρινών artifacts.', '',
            '## Παράρτημα: πλήρης εξέταση των 97 περιπτώσεων','',
            'BW=both_wrong, C=v3_corrected, N=v3_new_error. Οι σημειώσεις δεν είναι νέα gold annotations. '
            'Κάθε πλήρες κείμενο και score βρίσκεται στο CSV. Στις 464 both-correct δεν έγινε ποιοτική ανασκόπηση.', '',
            '| # | Canonical ID | Task / ομάδα | p | v2 → v3 | Παρατήρηση / αβεβαιότητα |',
            '|---:|---|---|---:|---|---|']
    short={'both_wrong':'BW','v3_corrected':'C','v3_new_error':'N'}
    for i,r in enumerate(selected,1):
        lines.append(f"| {i} | {r['canonical_id']} | {r['task']} / {short[r['correctness_group']]} | {float(r['p_hallucination']):.3g} | {float(r['v2_oof']):.4f} → {float(r['v3_oof']):.4f} | {esc(r['qualitative_note'])} |")
    lines+=['','Τα tags είναι πολυετικετικά και μετρήθηκαν μόνο στο επιλεγμένο review set:', '',
            '| Tag | Στις 97 εξετασμένες | Στα 78 κοινά λάθη |','|---|---:|---:|']
    for t,n in sorted(tags.items()):lines.append(f'| {t} | {n} | {common[t]} |')
    lines+=['','Οι παραπάνω συχνότητες είναι counts του review set, όχι error rates ή εκτιμήσεις επιπολασμού σε όλα τα 561 δείγματα. '
            'Δεν χρησιμοποιήθηκαν για δημιουργία/επιλογή νέων features στην παρούσα εργασία.','']
    with (OUT/'E6_ERROR_ANALYSIS.md').open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines))
    print(json.dumps(signals,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
