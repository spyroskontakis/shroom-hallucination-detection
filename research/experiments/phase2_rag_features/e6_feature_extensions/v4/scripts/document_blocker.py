"""Finalize a failed compatibility gate; no model loading, extraction or training."""
import json
import base64
import csv
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import v4_common as c
import structure


def text_file(name, text):
    path = c.OUT / name
    path.resolve().relative_to(c.OUT)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(text)


def main():
    log = c.offline('document_blocker')
    runtime = c.versions()
    protected = c.verify_inputs()['protected_sha256']
    compat = c.read_json(c.OUT/'provenance/compatibility.json')
    assert compat['status'] == 'BLOCKED_COMPATIBILITY'
    assert compat['real_pairs_scored'] == compat['rf_fits'] == 0
    for asset in compat['model_files'].values():
        assert c.sha(asset['path']) == asset['sha256']
    wheel = c.OUT/'provenance/bert_score-0.3.13-py3-none-any.whl'
    assert c.sha(wheel) == compat['wheel_sha256']
    count = 0
    with (c.OUT/'packages/bert_score-0.3.13.dist-info/RECORD').open(newline='', encoding='utf-8') as f:
        for name, digest, size in csv.reader(f):
            if digest:
                path = c.OUT/'packages'/name
                assert c.sha(path) == base64.urlsafe_b64decode(digest.split('=', 1)[1]+'==').hex()
                assert path.stat().st_size == int(size)
                count += 1
    assert count == 84
    v3 = c.read_json(c.V3/'config/run_config.json')
    checks = c.read_json(c.OUT/'config/input_checks.json')
    base = pd.read_csv(c.V3/'features/e6_v3_36_features.csv', float_precision='round_trip')
    ids = base.canonical_id.tolist()
    assert len(ids) == len(set(ids)) == 561
    assert base.columns.tolist() == ['canonical_id'] + v3['features']
    assert checks['old_features'] == v3['features']
    assert np.isfinite(base.iloc[:, 1:].to_numpy(float)).all()

    def aligned(path):
        frame = pd.read_csv(path, float_precision='round_trip')
        assert len(frame) == frame.canonical_id.nunique() == 561
        assert set(frame.canonical_id) == set(ids)
        return frame.set_index('canonical_id').loc[ids].reset_index()

    oof = aligned(c.V3/'evaluation/e6_v3_oof_predictions.csv')
    rows = aligned(c.V3/'evaluation/paired_row_diagnostics.csv')
    gold = aligned(c.CANONICAL)
    folds = aligned(c.FOLDS)
    local_folds = aligned(c.OUT/'inputs/locked_outer_folds.csv')
    for frame in [rows, folds, local_folds]:
        assert np.array_equal(oof.fold_id, frame.fold_id)
    for key in ['task', 'label_bin', 'p_hallucination']:
        assert np.array_equal(rows[key], gold[key])
    assert np.array_equal(oof.prediction, rows['E6-v3'])
    p = oof.prediction.to_numpy()
    assert np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all()
    binary = (p >= .5).astype(int)
    assert np.array_equal(binary, rows['E6-v3_binary'])
    correct = binary == gold.label_bin.to_numpy(int)
    assert np.array_equal(correct, rows['E6-v3_correct'])
    metrics = {'n': 561, 'correct': int(correct.sum()), 'accuracy': float(correct.mean()),
               'spearman': float(spearmanr(gold.p_hallucination, np.round(p, 12)).statistic)}
    expected = c.read_json(c.V3/'evaluation/e6_v3_metrics.json')['diagnostics']['all_rows']['E6-v3']
    assert metrics == expected and metrics['correct'] == 474
    pairs = c.read_json(c.OUT/'inputs/coverage_pairs_label_free.json')
    assert [pair['canonical_id'] for pair in pairs] == ids
    for pair, row in zip(pairs, gold.to_dict('records')):
        assert set(pair) == {'pair_id', 'canonical_id', 'group', 'premise', 'hypothesis'}
        assert pair['premise'] == row['src' if row['task'] == 'PG' else 'tgt']
        assert pair['hypothesis'] == row['hyp']
    c.write_json(c.OUT/'config/baseline_verification.json', {
        'status': 'PASS', 'metrics': metrics, 'new_baseline_fits': 0,
        'ids_folds_labels_predictions_exact': True,
        'fold_counts': {str(k): int(v) for k,v in folds.fold_id.value_counts().sort_index().items()},
        'saved_feature_matrix_sha256': c.sha(c.V3/'features/e6_v3_36_features.csv'),
        'source_36_features_verified': True, 'v4_combined_matrix_exists': False})
    c.write_json(c.OUT/'config/structure_spec.json', structure.SPEC)
    c.write_json(c.OUT/'config/structural_contracts.json', {
        'status': structure.contracts(), 'artificial_only': True,
        'real_rows_extracted': 0, 'neural_smoke_status': 'BLOCKED'})
    features = v3['features'] + c.NEW
    assert len(features) == len(set(features)) == 43
    c.write_json(c.OUT/'config/feature_schema.json', {
        'status': 'PLANNED_NOT_EXTRACTED', 'id_column': 'canonical_id',
        'original_features': v3['features'], 'new_features': c.NEW, 'ordered_features': features})
    request = c.Path(__import__('os').environ['SHROOM_DIAGNOSTIC_REQUEST'])
    with (c.OUT/'provenance/user_request.txt').open('xb') as f:
        f.write(request.read_bytes())
    config = {
        'status': 'BLOCKED_BEFORE_BULK_SCORING', 'execution_allowed': False,
        'created_utc': c.now(), 'experiment': 'E6-v4', 'baseline': 'E6-v3',
        'features': features, 'random_forest': v3['random_forest'], 'runtime': runtime,
        'target': 'p_hallucination', 'clip': [0,1], 'threshold': .5,
        'spearman_round_decimals': 12, 'bootstrap': v3['bootstrap'],
        'bootstrap_rng': 'numpy.random.default_rng(42)', 'bootstrap_unit': 'paired canonical row',
        'mcnemar': 'exact two-sided binomtest(corrected, corrected+introduced, 0.5)',
        'reference_by_task': {'DM': 'tgt', 'MT': 'tgt', 'PG': 'src'}, 'candidate': 'hyp',
        'model_id': c.MODEL_ID, 'revision': c.REVISION, 'tokenizer_revision': c.REVISION,
        'num_layers': 18, 'layer_source': 'official model2layers mapping; no SHROOM tuning',
        'idf': False, 'rescale_with_baseline': False, 'all_layers': False,
        'use_fast_tokenizer': False, 'device': 'cpu', 'dtype': 'float32', 'batch_size': 2,
        'torch_threads': 4, 'torch_interop_threads': 4,
        'planned_rf_fits_if_gate_passed': 5, 'actual_rf_fits': 0, 'baseline_fits': 0,
        'real_pairs_scored': 0, 'feature_matrix_frozen': False,
        'truncation': {'status': 'BLOCKED_NO_REAL_TOKENIZATION',
                       'observed_tokenizer_max_length': compat['tokenizer_max_length'],
                       'model_max_position_embeddings': 512, 'real_truncation_count': None},
        'statistics_scope': 'adaptive exploratory development-only; descriptive statistics only'}
    c.write_json(c.OUT/'config/run_config.json', config)
    rf_text = json.dumps(v3['random_forest'], ensure_ascii=False, indent=2)
    spec_text = json.dumps(structure.SPEC, ensure_ascii=False, indent=2)
    protocol = f'''# E6-v4 protocol — blocked compatibility gate

Status: **BLOCKED_BEFORE_BULK_SCORING**. This document preserves the predetermined specification and the observed technical stop. It is recorded after the artificial compatibility attempt, before any SHROOM scoring or RF fit. It does not certify a passed smoke test or a frozen feature matrix. `execution_allowed=false`.

Use the 561 frozen canonical IDs and five locked folds (113,112,112,112,112). Preserve all 36 E6-v3 features numerically and in their exact saved order, then append the seven ordered names in `config/feature_schema.json` (43 total). The source matrix is verified; no combined matrix has been produced.

Reference is tgt for DM/MT and src for PG; candidate is hyp. Use exact frozen strings. The projected extraction input contains only pair_id, canonical_id, group, premise, hypothesis. No labels, OOF predictions or definitions enter the new feature extraction. Labels are read separately for saved baseline verification only.

Official BERTScore distribution 0.3.13, unmodified wheel, checkpoint/tokenizer `{c.MODEL_ID}@{c.REVISION}`. Official mapping supplies num_layers=18; idf=False, rescale_with_baseline=False, all_layers=False, use_fast_tokenizer=False. CPU float32, batch_size=2, four intra/inter-op threads. No selection using SHROOM results. Precision measures candidate coverage by reference; recall measures reference coverage by candidate.

Required artificial smoke cases: identical sentence, omission, addition, number change, negation added/removed. Official matching-function direction assertion passed before the neural smoke call; neural smoke tokenization failed with OverflowError. The six neural cases have no scores. Separate deterministic structural contracts pass. No fallback tokenizer limit, package patch, checkpoint substitution or dependency downgrade is authorized by this protocol.

Frozen intended structural rules, used only on artificial inputs:

```json
{spec_text}
```

Length ratio is min(counts)/max(counts), both empty=1, one empty=0. Number-presence mismatch is XOR of nonempty number sets; number-set mismatch is set inequality (both empty=0). Negation mismatch is XOR of literal marker presence. These are surface indicators, not semantic judgments. The numeric rule deliberately retains ambiguous comma formats; it is not a general numeric parser. Lexicon is exactly the user-specified list plus suffix, without additions from labels or error analysis.

Full fixed RandomForestRegressor parameters, copied from E6-v3:

```json
{rf_text}
```

Only after a passed compatibility gate, full extraction, per-ID finiteness/truncation checks, exact 36-column equality and a frozen 43-column matrix would five outer-fold fits be permitted. Target p_hallucination; clip [0,1]; binary prediction >=0.5. No baseline fits, tuning, feature selection, router, task-specific models or post-score changes.

Intended evaluation: overall/fold/task/evidence accuracy and Spearman (predictions rounded to 12 decimals for Spearman), corrections/new errors against saved E6-v3, exact two-sided McNemar, paired row bootstrap with 10,000 resamples using numpy.random.default_rng(42), percentile quantiles 0.025/0.975. Definition availability is descriptive and all definitions concern DM. Intervention was selected after error analysis: adaptive exploratory development-only, descriptive statistics, no independent confirmatory test.

**Stopping rule applied:** the user's section 3 requires stopping if the official library is incompatible. See `provenance/compatibility.json` and `E6_V4_RESULTS.md`. No feature matrix or evaluation is frozen. The documentation manifest seals this blocked state only.

All new files remain inside rag_e6_v4. Prior artifacts, error analysis and untracked changes are preserved. No official-test, synthetic changes, retrieval, remote inference, commit/push/tag or other experiment.
'''
    text_file('E6_V4_PROTOCOL.md', protocol)
    report = f'''# E6-v4 — τεχνική αναφορά διακοπής

**Κατάσταση: BLOCKED_BEFORE_BULK_SCORING. Η αξιολόγηση δεν εκτελέστηκε.**

Η επίσημη `bert-score==0.3.13` απέτυχε στο τεχνητό smoke test με `OverflowError: int too big to convert`. Εφαρμόστηκε η ρητή οδηγία της ενότητας 3: «Αν η επίσημη αντιστοίχιση δεν είναι διαθέσιμη ή η βιβλιοθήκη είναι ασύμβατη, σταμάτησε πριν από scoring και τεκμηρίωσε το τεχνικό εμπόδιο».

## Επαληθευμένο baseline και κατάσταση αποτελεσμάτων

| Έκδοση | Correct | Accuracy | Spearman | Νέα RF fits |
|---|---:|---:|---:|---:|
| E6-v3, αποθηκευμένο baseline | 474/561 | {metrics['accuracy']:.10f} | {metrics['spearman']:.10f} | 0 |
| E6-v4 | Δεν υπολογίστηκε | — | — | 0 |

Επαληθεύτηκαν τα 561 μοναδικά IDs, τα folds, οι ανθρώπινες δυαδικές ετικέτες και το p_hallucination έναντι του canonical manifest. Οι αποθηκευμένες προβλέψεις v3 ταυτίζονται αριθμητικά ανά ID/fold με τα paired diagnostics και αναπαράγουν το καταγεγραμμένο αποτέλεσμα. Δεν έγινε baseline fit. Οι πέντε validation πληθυσμοί είναι 113,112,112,112,112.

## Συγκεκριμένο τεχνικό εμπόδιο

Το επίσημο BERTScore καλεί `tokenizer.encode(..., max_length=tokenizer.model_max_length, truncation=True)` στο `packages/bert_score/utils.py`, συνάρτηση `sent_encode`. Στο υπάρχον περιβάλλον transformers 5.5.4 / tokenizers 0.22.2, ο φορτωμένος DebertaTokenizer έχει `model_max_length={compat['tokenizer_max_length']}`, δηλαδή την τιμή sentinel μη καθορισμένου ορίου. Το checkpoint δηλώνει `max_position_embeddings=512`, αλλά το παγωμένο tokenizer_config.json δεν ορίζει model_max_length.

Η μεταβίβαση της τιμής sentinel στο backend `enable_truncation` προκαλεί OverflowError πριν παραχθούν BERTScore τιμές για τα τεχνητά κείμενα. Η αποτυχία αφορά τον συγκεκριμένο συνδυασμό επίσημου package, pinned tokenizer και υπάρχοντος runtime· δεν αποδεικνύει ασυμβατότητα σε κάθε άλλο περιβάλλον. Το πλήρες traceback βρίσκεται στο `provenance/compatibility.json` και το αρχικό console log στο `provenance/compatibility_console.txt`.

Δεν εφαρμόστηκε χειροκίνητο max_length=512, τροποποίηση της βιβλιοθήκης, αλλαγή checkpoint/tokenizer ή downgrade. Η επίσημη αντιστοίχιση layer υπάρχει και δίνει **18**· η αποτυχία αφορά tokenization, όχι επιλογή layer.

## Provenance

- Model/tokenizer: `{c.MODEL_ID}`, revision `{c.REVISION}`, ακριβώς το cached checkpoint του αρχικού E3. Επαληθεύτηκαν και τα πέντε pinned model/tokenizer αρχεία έναντι του αποθηκευμένου provenance E6-v1.
- Official wheel: `bert_score-0.3.13-py3-none-any.whl`, SHA-256 `{compat['wheel_sha256']}`. Επαληθεύτηκαν 84 hashed RECORD entries και μεγέθη. Το package παραμένει ατροποποίητο μέσα στον φάκελο v4.
- Distribution metadata: 0.3.13. Το ίδιο upstream wheel δηλώνει εσωτερικά `__version__=0.3.12`. Καταγράφονται και οι δύο τιμές χωρίς διόρθωση του upstream κώδικα.
- Πραγματικό official BERTScore hash string: `{compat['scorer_hash']}`. Το hash string δεν περιλαμβάνει το model revision· το πλήρες provenance το καταγράφει χωριστά.
- idf=False, rescale_with_baseline=False, num_layers=18 από την επίσημη αντιστοίχιση. CPU float32, batch size 2, τέσσερα intra/inter-op threads. Πλήρεις εκδόσεις στο configuration.
- Έγινε μόνο λήψη του απαιτούμενου package wheel/metadata για τοπική χρήση, χωρίς εγκατάσταση/αλλαγή των κοινών dependencies. Το checkpoint ήταν ήδη cached. Το compatibility test είχε αποκλεισμένο δίκτυο και μηδενικές απόπειρες δικτύου. Δεν έγιναν retrieval, απομακρυσμένο inference ή LLM/API calls.

## Έλεγχοι και μη παραχθέντα παραδοτέα

Οι 36 αρχικές στήλες επαληθεύτηκαν ως προς hash, σειρά, πεπερασμένες τιμές και 561 IDs. Δεν δημιουργήθηκε νέα μήτρα για να πιστοποιηθεί ισότητα του πρώτου block μέσα σε αυτήν. Αποθηκεύτηκε μόνο το προβλεπόμενο schema των 43 χαρακτηριστικών και τα ακριβή label-free reference/hyp inputs. Η αντιστοίχιση reference=tgt για DM/MT, src για PG ελέγχθηκε και έναντι των canonical strings.

Τα deterministic structural contracts σε τεχνητά κείμενα πέρασαν. Στο αρχικό compatibility test πέρασε η assertion κατεύθυνσης της επίσημης greedy matching συνάρτησης σε τεχνητά orthogonal embeddings (precision=1, recall=2/3). Αυτό δεν υποκαθιστά τα neural smoke tests: ίδια πρόταση, omission, addition, αλλαγή αριθμού και προσθήκη/αφαίρεση άρνησης δεν απέδωσαν neural scores λόγω της αποτυχίας tokenization.

**Πραγματικά δείγματα με νέα χαρακτηριστικά: 0. Πραγματικά BERTScore pairs: 0. RF fits E6-v4: 0. Πρόσθετα baseline fits: 0.** Η πλήρης εξαγωγή δεν άρχισε, επομένως ο χρόνος πλήρους εξαγωγής και το πλήθος truncated πραγματικών δειγμάτων είναι μη διαθέσιμα, όχι μετρημένα μηδενικά.

Δεν υπάρχουν επτά νέα χαρακτηριστικά ανά ID, μήτρα 43 χαρακτηριστικών, 561 E6-v4 OOF predictions ή paired diagnostics v4. Δεν μπορούν να υπολογιστούν metrics ανά fold/task/evidence, διορθώσεις/νέα λάθη, McNemar ή bootstrap έναντι v3. Δεν αποδίδονται πλασματικές τιμές και δεν επαναχρησιμοποιούνται baseline predictions ως v4.

Το `E6_V4_PROTOCOL.md`, το configuration, το ordered schema, οι deterministic κανόνες, ο κώδικας ελέγχου και το provenance τεκμηριώνουν το μπλοκαρισμένο στάδιο. Το πρωτόκολλο καταγράφηκε μετά την απόπειρα τεχνητού compatibility test, πριν από οποιοδήποτε SHROOM scoring ή fit. Δεν δηλώνεται επιτυχές execution freeze ή feature-matrix freeze.

## Ακεραιότητα και ερευνητικό όριο

Ο τελικός έλεγχος SHA-256 επαλήθευσε **{len(protected)} προστατευμένα αρχεία**, περιλαμβανομένων προηγούμενων πειραμάτων και error analysis. Οι νέες εγγραφές περιορίστηκαν στον φάκελο E6-v4. Δεν έγινε official-test access, αλλαγή synthetic δεδομένων, commit/push/tag ή άλλο πείραμα.

Η προτεινόμενη επέκταση παραμένει adaptive exploratory development-only επειδή επιλέχθηκε μετά την ανάλυση σφαλμάτων. Δεν υπάρχει μετρημένη βελτίωση ή υποβάθμιση v4. Αν μπορούσε να εκτελεστεί με εγκεκριμένη συμβατή διαδικασία, οι προβλεπόμενοι στατιστικοί έλεγχοι θα ήταν descriptive exploratory statistics, χωρίς ανεξάρτητη confirmatory ερμηνεία.
'''
    # Recheck protected artifacts before sealing the report; no model execution here.
    assert len(c.verify_inputs()['protected_sha256']) == len(protected)
    assert log.stat().st_size == 0
    c.write_json(c.OUT/'config/integrity_audit.json', {
        'status': 'PASS', 'checked_utc': c.now(), 'protected_files': len(protected),
        'prior_artifacts_unchanged': True, 'wheel_record_entries_verified': count,
        'baseline_verified': True, 'real_pairs_scored': 0, 'e6_v4_rf_fits': 0,
        'baseline_rf_fits': 0, 'full_extraction_seconds': None,
        'real_truncation_count': None, 'evaluation_status': 'NOT_RUN'})
    text_file('E6_V4_RESULTS.md', report)
    files = {}
    for folder in ['config', 'inputs', 'provenance', 'scripts', 'packages']:
        for path in (c.OUT/folder).rglob('*'):
            if path.is_file():
                files[path.relative_to(c.OUT).as_posix()] = c.sha(path)
    for name in ['E6_V4_PROTOCOL.md', 'E6_V4_RESULTS.md']:
        files[name] = c.sha(c.OUT/name)
    c.write_json(c.OUT/'config/blocked_state_manifest.json', {
        'status': 'BLOCKED_BEFORE_BULK_SCORING', 'sealed_utc': c.now(), 'files': files,
        'scope': 'blocked documentation and prepared inputs, not successful experiment completion',
        'excluded': ['runtime_tmp cache/temp files', 'this self-referential manifest'],
        'execution_allowed': False, 'feature_matrix_frozen': False})
    print(json.dumps({'status': 'BLOCKED_BEFORE_BULK_SCORING', 'baseline': metrics,
                      'protected_files': len(protected), 'manifest_files': len(files)}, indent=2))


if __name__ == '__main__':
    main()
