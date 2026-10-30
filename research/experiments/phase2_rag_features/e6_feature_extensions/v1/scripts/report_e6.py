"""Render saved E6 diagnostics; never train, encode or change the locked protocol."""
from e6_common import *


def main():
    lock = verify_lock()
    result = read_json(OUT / 'evaluation/e6_metrics.json')
    assert result['status'] == 'COMPLETED'
    d = result['diagnostics']
    ranking = read_json(OUT / 'config/ranking_consistency.json')
    freeze = read_json(OUT / 'config/feature_freeze.json')
    baseline = read_json(OUT / 'evaluation/baseline_compatibility.json')
    assert baseline['status'] == 'PASS'
    for p, expected in freeze['files'].items():
        assert sha(OUT / p) == expected
    assert sha(OUT / 'evaluation/e6_oof_predictions.csv') == result['oof_sha256']
    assert sha(OUT / 'ranking/reconstructed_top5.jsonl') == freeze['ranking_sha256']
    assert (OUT / 'config/network_attempts.jsonl').stat().st_size == 0
    lines = [
        '# E6 v1 — πραγματικά development-only αποτελέσματα', '',
        '**Κατάσταση: ΟΛΟΚΛΗΡΩΘΗΚΕ.** Μία προκαθορισμένη έκδοση E6, μία εκτέλεση five-fold OOF αξιολόγησης. '
        'Δεν άλλαξαν χαρακτηριστικά, υπερπαράμετροι ή threshold μετά την παρατήρηση του σκορ.', '',
        '## Συνολικό αποτέλεσμα', '',
        '| Μοντέλο | Χαρακτηριστικά | Σωστά / N | OOF accuracy | OOF Spearman |',
        '|---|---:|---:|---:|---:|',
    ]
    for name, count in [('E3', 14), ('E5', 21), ('E6', 25)]:
        m = d['all_rows'][name]
        lines.append(f"| {name} | {count} | {m['correct']}/{m['n']} | {m['accuracy']:.10f} ({m['accuracy']*100:.4f}%) | {m['spearman']:.10f} |")
    lines += ['', '## Αποτελέσματα ανά task και διαθεσιμότητα ορισμού', '',
              '| Ομάδα | N | E3 σωστά / accuracy | E5 σωστά / accuracy | E6 σωστά / accuracy | E3 ρ | E5 ρ | E6 ρ |',
              '|---|---:|---:|---:|---:|---:|---:|---:|']
    groups = [(task, group) for task, group in d['per_task'].items()]
    groups += [('Με ορισμό', d['by_evidence']['1']), ('Χωρίς ορισμό', d['by_evidence']['0'])]
    for title, group in groups:
        accuracy = ' | '.join(f"{group[name]['correct']}/{group[name]['n']} · {group[name]['accuracy']*100:.4f}%" for name in ['E3', 'E5', 'E6'])
        corr = ' | '.join(f"{group[name]['spearman']:.10f}" for name in ['E3', 'E5', 'E6'])
        lines.append(f"| {title} | {group['E6']['n']} | {accuracy} | {corr} |")
    lines += ['', '## Ζευγαρωμένη σύγκριση E6 έναντι E3 και E5', '',
              'Η Δ accuracy και τα διαστήματα δίνονται σε ποσοστιαίες μονάδες (E6 μείον baseline).', '',
              '| Baseline | Διορθώσεις | Νέα λάθη | Καθαρά σωστά | Δ accuracy (π.μ.) | McNemar p | Paired-bootstrap 95% CI (π.μ.) |',
              '|---|---:|---:|---:|---:|---:|---:|']
    for name, p in d['paired'].items():
        b = p['paired_bootstrap_accuracy_difference_e6_minus_baseline']
        lo, hi = b['percentile_95_ci']
        lines.append(f"| {name} | {p['corrected']} | {p['introduced_errors']} | {p['net_correct']:+d} | {b['observed']*100:+.4f} | {p['mcnemar_exact_two_sided_p']:.10f} | [{lo*100:.4f}, {hi*100:.4f}] |")
    lines += ['', 'Exact two-sided McNemar μέσω binomtest στις discordant pairs. Paired bootstrap με 10.000 επαναδειγματοληψίες 561 ζευγαρωμένων γραμμών, '
              'numpy default_rng(42) ξεχωριστά για κάθε baseline και percentile 2,5%/97,5%. Ίδια διαδικασία με το Module 4. '
              'Τα διαστήματα αφορούν τις σταθερές OOF προβλέψεις και δεν περιλαμβάνουν νέα εκπαίδευση μέσα σε κάθε bootstrap replicate. '
              'Δεν έγινε διόρθωση πολλαπλών συγκρίσεων.', '',
              'Τα canonical IDs όλων των διορθώσεων και νέων λαθών περιέχονται στο `evaluation/e6_metrics.json`. '
              'Το `evaluation/paired_row_diagnostics.csv` περιέχει και τις 561 γραμμές με task, fold, evidence flag, labels, '
              'τρεις OOF προβλέψεις και την έκβαση κάθε σύγκρισης.', '',
              '| Ομάδα | Διορθώσεις / νέα λάθη έναντι E3 | Διορθώσεις / νέα λάθη έναντι E5 |',
              '|---|---:|---:|']
    for family, groups in d['corrections_by_group'].items():
        for group, comparisons in groups.items():
            label = group if family == 'task' else ('Με ορισμό' if float(group) == 1 else 'Χωρίς ορισμό')
            entries = ' | '.join(f"{comparisons[name]['corrected']} / {comparisons[name]['introduced_errors']}" for name in ['E3', 'E5'])
            lines.append(f'| {label} | {entries} |')
    lines += ['', '## Ανακατασκευή κατάταξης και provenance', '',
              'Δεν υπήρχε αποθηκευμένο ιστορικό ranking file του Module 4. Με ρητή άδεια του χρήστη ανακατασκευάστηκε το top-5 από '
              'το ίδιο παγωμένο Wiktionary snapshot, χρησιμοποιώντας αυτούσια τη συνάρτηση `select_top5` του αποδεκτού pinned κώδικα. '
              'Ίδιοι υποψήφιοι ορισμοί και eligibility, query `term + "\\n" + src`, candidate `candidate_term + "\\n" + candidate_context`, '
              'ίδια MPNet κανονικοποίηση/dot product και ταξινόμηση κατά φθίνουσα cosine, source_entry_id και evidence_id. '
              'Δεν χρησιμοποιήθηκαν tgt, hyp, labels ή predictions για επιλογή/ανακατάταξη.', '',
              'Αποθηκεύτηκαν 561 εγγραφές στο `ranking/reconstructed_top5.jsonl`, με canonical ID, candidate count, query hash και '
              'ordered top-5 (rank, score, evidence ID, definition και source provenance). Οι γραμμές χωρίς evidence έχουν κενή λίστα.', '',
              f"Έλεγχος συνέπειας: availability και selected sense count ταυτίζονται ακριβώς με E5· μέγιστη απόλυτη διαφορά top-1 cosine "
              f"{ranking['top1_cosine_max_absolute_difference']:.17g}, με προκαθορισμένο atol=1e-12 και rtol=0. PASS σε 561/561 γραμμές. "
              'Η διαφορά είναι στο επίπεδο αναπαράστασης κινητής υποδιαστολής/CSV. '
              '**Η συμφωνία συγκεντρωτικών χαρακτηριστικών αποτελεί έλεγχο συνέπειας και δεν αποδεικνύει από μόνη της ολόκληρη την ιστορική σειρά.**', '',
              'MPNet: `sentence-transformers/all-mpnet-base-v2@e8c3b32edf5434bc2275fc9bab85f82640a19130`, max sequence length 256. '
              'NLI: `microsoft/deberta-large-mnli@7296194b9009373def4f7c5dad292651e4b5cf4e`, max length 512, '
              'truncation/padding, contradiction=0, neutral=1, entailment=2. CPU float32, seed 42, eval/inference mode, local_files_only. '
              'Επαληθεύτηκαν όλα τα καταγεγραμμένα model/tokenizer hashes έναντι του accepted replay provenance. '
              'Οι πλήρεις διαδρομές, hashes και runtime εκδόσεις βρίσκονται στο `config/run_config.json`.', '',
              '## Πρωτόκολλο, χαρακτηριστικά και baselines', '',
              'Το `E6_PROTOCOL.md` και το εγκεκριμένο addendum καταγράφηκαν πριν από inference/αξιολόγηση. '
              'Η κατάταξη πάγωσε πριν από την πρόσβαση στο hyp και ο πίνακας χαρακτηριστικών πριν από τη σύνδεση evaluation labels. '
              f"Χρόνος lock ρυθμίσεων: {lock['locked_utc']}. Ranking freeze: {ranking['frozen_utc']}. "
              f"Feature freeze: {freeze['frozen_utc']}. Ολοκλήρωση αξιολόγησης: {result['completed_utc']}.", '',
              'Τα 21 E5 predictors διατηρήθηκαν αριθμητικά ακριβώς όπως στον accepted evaluator (έλεγχος array equality). '
              'Προστέθηκαν αποκλειστικά cosine ορισμού–hyp και NLI entailment/neutral/contradiction του πρώτου ορισμού. '
              'Premise είναι το candidate_definition και hypothesis το hyp. Για τις 368 γραμμές χωρίς ορισμό τα τέσσερα νέα features '
              'είναι ακριβώς μηδέν και το υπάρχον evidence_available διατηρείται. Σύνολο: 25 predictors.', '',
              'Επαληθεύτηκαν και τα δύο baselines από τις αποθηκευμένες OOF προβλέψεις και τα canonical labels: E3 445/561 και E5 446/561, '
              'με τα ίδια καταγεγραμμένα Spearman. Δεν υπήρξε απόκλιση και δεν επανεκπαιδεύτηκαν τα baselines. '
              'Τα 561 μοναδικά IDs, η σειρά τους και τα locked folds συμφωνούν, με validation μεγέθη 113/112/112/112/112.', '',
              'Χρησιμοποιήθηκε αυτούσια η `run_cv` του Module 4: RandomForestRegressor με 500 δέντρα, random_state=42, n_jobs=-1, '
              'τα ίδια υπόλοιπα defaults, target p_hallucination, clipping [0,1], binary threshold >=0.5. '
              'Το Spearman υπολογίζεται με rounding των προβλέψεων στα 12 δεκαδικά. Μία E6 CV εκτέλεση, πέντε fitted forests. '
              'Runtime: Python 3.11.9, sklearn 1.8.0, numpy 2.4.4, pandas 3.0.2, scipy 1.17.1, '
              'sentence-transformers 5.4.1, transformers 5.5.4, torch 2.11.0.', '',
              '## Αποτελέσματα ανά fold', '',
              '| Fold | N | E3 accuracy | E5 accuracy | E6 accuracy | E6 Spearman |',
              '|---|---:|---:|---:|---:|---:|']
    for fold, g in d['per_fold'].items():
        lines.append(f"| {fold} | {g['E6']['n']} | {g['E3']['accuracy']:.10f} | {g['E5']['accuracy']:.10f} | {g['E6']['accuracy']:.10f} | {g['E6']['spearman']:.10f} |")
    lines += ['', '## Ερμηνεία και περιορισμοί', '']
    for name, p in d['paired'].items():
        b = p['paired_bootstrap_accuracy_difference_e6_minus_baseline']
        lo, hi = b['percentile_95_ci']
        direction = 'αριθμητική βελτίωση' if p['net_correct'] > 0 else ('αριθμητική επιδείνωση' if p['net_correct'] < 0 else 'ίδια accuracy')
        uncertainty = 'Το 95% διάστημα περιλαμβάνει το μηδέν.' if lo <= 0 <= hi else 'Το 95% διάστημα δεν περιλαμβάνει το μηδέν στο συγκεκριμένο paired development δείγμα.'
        lines.append(f"Έναντι {name}: {direction}, καθαρά {p['net_correct']:+d}/561 σωστές προβλέψεις. {uncertainty}")
        lines.append('')
    lines += ['Το αποτέλεσμα αφορά αποκλειστικά το συγκεκριμένο development pool και τα ήδη κλειδωμένα folds. '
              'Δεν τεκμηριώνει γενίκευση ούτε αυτόματη αντικατάσταση του τελικού μοντέλου. '
              'Το E6 διατηρεί τον reference-assisted κλάδο του E5· οι ορισμοί καλύπτουν μόνο DM. '
              'Προβλέψεις χωρίς διαθέσιμο ορισμό μπορούν επίσης να αλλάξουν, επειδή επανεκπαιδεύεται το Random Forest σε διευρυμένο feature space. '
              'Το ίδιο development pool έχει ήδη χρησιμοποιηθεί στα προηγούμενα πειράματα. '
              'Οι ιστορικοί περιορισμοί provenance/label exposure του Module 4 παραμένουν τεκμηριωμένοι στα αρχικά reports και δεν αναιρούνται από το E6.', '',
              '## Παραδοτέα και τελική ακεραιότητα', '',
              '- `scripts/`: ξεχωριστός κώδικας προετοιμασίας, κατασκευής, αξιολόγησης και αναφοράς· `tests/test_e6.py`: πέντε επιτυχημένα offline contract tests.',
              '- `ranking/`: ανακατασκευασμένη σειρά/score/provenance και τα συγκεντρωτικά consistency features.',
              '- `features/e6_added_4_features.csv`, `features/e6_25_features.csv`: 561 γραμμές με τέσσερα νέα και 25 συνολικά predictors αντίστοιχα.',
              '- `evaluation/e6_oof_predictions.csv`, `evaluation/e6_metrics.json`, `evaluation/paired_row_diagnostics.csv`: πραγματικές OOF προβλέψεις και πλήρη diagnostics.',
              '- `config/run_config.json`, `config/ranking_consistency.json`, `config/feature_freeze.json`: κλειδωμένες ρυθμίσεις και provenance.',
              '- `evaluation/baseline_compatibility.json`: πραγματική επαλήθευση των baselines χωρίς retraining.', '',
              f"Και τα {len(lock['protected_sha256'])} προστατευμένα αρχεία συμφωνούν με τα πριν από την εκτέλεση SHA-256. "
              'Τα E3/E5 artifacts παρέμειναν ανέπαφα. Το process-local network log είναι κενό. '
              'Δεν έγιναν νέες εξωτερικές λήψεις, LLM/API calls, official-test access, αλλαγές στα synthetic δεδομένα ή εγκαταστάσεις πακέτων. '
              'Δεν ξεκίνησε άλλο πείραμα.', '',
              'Το αρχικό `config/preflight.json` διατηρεί την ιστορική κατάσταση «ranking missing» πριν από τη μεταγενέστερη άδεια. '
              'Η παρούσα αναφορά και τα completed evaluation artifacts καταγράφουν την τελική κατάσταση.', '']
    (OUT / 'E6_RESULTS.md').write_text('\n'.join(lines), encoding='utf-8')
    write_json(OUT / 'config/completion_manifest.json', {
        'status': 'COMPLETED', 'verified_utc': now(), 'protected_files_unchanged': len(lock['protected_sha256']),
        'network_attempts': 0, 'tests_passed': 5, 'e6_cv_runs': 1,
        'files': {str(p.relative_to(OUT)).replace('\\', '/'): sha(p)
                  for p in sorted(OUT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts},
    })
    print(json.dumps({'report': str(OUT / 'E6_RESULTS.md'), 'status': 'COMPLETED'}))


if __name__ == '__main__':
    main()
