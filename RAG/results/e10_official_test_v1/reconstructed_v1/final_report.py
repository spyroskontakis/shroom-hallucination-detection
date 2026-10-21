"""Read-only validation of frozen outputs and creation of final result reports."""
import collections,hashlib,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE))
from predict_and_score import validated_predictions,contract
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def main():
    contract();predictions,prediction_hash=validated_predictions()
    for name,h in read(HERE/'PRESCORING_CODE_LOCK.json')['files'].items():assert sha(HERE/name)==h
    result=read(HERE/'E10_OFFICIAL_TEST_METRICS.json');assert result['prediction_sha256']==prediction_hash
    reconstruction=read(HERE/'E10_RECONSTRUCTION_MANIFEST.json');coverage=reconstruction['coverage']
    train=read(HERE/'E10_OFFICIAL_TEST_TRAIN_MANIFEST.json')
    features=read(HERE/'E10_OFFICIAL_TEST_FEATURES_MANIFEST.json')
    assert sha(HERE/'E10_OFFICIAL_TEST_FEATURES.csv')==features['features_sha256']==predictions['features_sha256']
    assert sha(HERE/'E10_FINAL_RF.joblib')==read(HERE/'RF_FIT_COMPLETED.json')['model_sha256']
    published=read(HERE/'PUBLISHED_COMPARISON_SOURCES.json')
    assert train['training_examples']==561 and not train['strict_547_pool_used']
    assert features['rows']==result['overall']['n']==1500 and result['RF_fits']==1
    assert result['no_tuning_after_scoring']
    assert result['scoring_completed_unix']>=predictions['frozen_unix']
    for source,h in reconstruction['frozen_resources'].items():assert sha(ROOT/source)==h
    for stage in ['base14','rag11','nli2','hhem']:
        m=read(HERE/'cpu_features'/f'{stage}_complete.json')
        for p,h in m['outputs'].items():assert sha(HERE/p)==h
    overall=result['overall']
    lines=['# E10 reconstructed retrospective official-test results','',
      '**FINAL STATUS: PASS**','',
      f"On a reconstructed retrospective evaluation using the official labeled model-agnostic SHROOM test set, E10 achieved **{overall['correct']}/1500**, Accuracy **{overall['accuracy']:.15f}**, and Spearman rho **{overall['spearman']:.15f}**.",'',
      'This is not an independent/untouched holdout evaluation, an official competition submission, or an official ranking claim.','',
      '| Population | n | Correct | Accuracy | Spearman rho |','|---|---:|---:|---:|---:|',
      f"| Overall | 1500 | {overall['correct']} | {overall['accuracy']:.15f} | {overall['spearman']:.15f} |"]
    for task,m in result['by_task'].items():lines.append(f"| {task} | {m['n']} | {m['correct']} | {m['accuracy']:.15f} | {m['spearman']:.15f} |")
    lines+=['','Confusion matrices use rows = gold [NH, H], columns = predicted [NH, H].','',f"Overall: `{overall['confusion_matrix_NH_H']}`.",f"Gold counts: `{overall['gold_counts']}`. Predicted counts: `{overall['predicted_counts']}`.",'',
      '## Frozen predictions and training','',
      'One final RandomForestRegressor was fit on all 561 frozen labeled examples (493 validation + 68 trial), using the unchanged ordered 37-feature E10 training matrix, all frozen RF parameters, seed 42, original regression target, clipping and threshold 0.5. The strict 547-row proposal was not used. The 14 MT shared source/target pairs remain a limitation; their hypotheses differ and there is no exact test-example overlap.','',
      f'Prediction SHA256: `{prediction_hash}`.','',
      'All 1,500 predictions were frozen before official gold was loaded by the scoring stage. Input allowlists exclude labels and gold probabilities. Feature ordering, population identity, finite/range checks and original missing-definition zeros passed. Spearman uses the unchanged evaluator, rounding predictions to 12 decimals. No tuning, feature changes, alternate models or new predictions followed test scoring.','',
      '## Resource reconstruction','',
      f"557 missing terms were processed. {coverage['reconstructed_terms_with_senses']} have reconstructed usable senses; {coverage['unavailable_terms']} have no usable retrieved definition ({coverage['confirmed_no_sense_terms']} confirmed no-sense and {coverage['technical_failure_terms']} technical failures).",
      f"DM coverage: {coverage['DM_with_reconstructed_definitions']} with reconstructed definitions, {coverage['DM_with_frozen_definitions']} with existing frozen definitions, {coverage['DM_original_missing_definition_behavior']} using original missing-definition behavior.",'',
      'The sole methodological deviation is Wiktionary content reconstruction in 2026. The endpoint, revision-bound retrieval, parser, normalization, deduplication, ranking and original fallback behavior are unchanged. Existing frozen dictionary resources and all source experiment artifacts remain unchanged. Parser replay reproduced the original 462-sense snapshot byte-for-byte. Full per-term raw/processed hashes, URLs and timestamps are in the reconstruction manifest.','',
      '## Descriptive comparison with published systems','',
      'The following rounded model-agnostic scores are from the organizer paper, Table 1(a). They are descriptive references only. This evaluation occurred after the competition, test labels were public, prior exploratory test use existed, and dictionary resources were reconstructed in 2026. No official rank is inferred.','',
      '| Published system | Accuracy | Spearman rho | E10 minus published Accuracy | E10 minus published rho |',
      '|---|---:|---:|---:|---:|']
    for r in published['published_rounded_scores']:
        lines.append(f"| {r['team']} | {r['accuracy']:.3f} | {r['spearman']:.3f} | {overall['accuracy']-r['accuracy']:+.6f} | {overall['spearman']-r['spearman']:+.6f} |")
    lines+=['',f"Source: [Mickus et al., SemEval-2024 Task 6, Table 1(a)]({published['source']}). Deltas use rounded published values, not unpublished exact team scores.",'',
      '## Execution and preservation','',
      'NLI1, MPNet, NLI2 and HHEM used the original local CPU environment and pinned backends. FactCG used the original pinned CUDA float32 adapter on one Modal A100-80GB. No student training, E9-B/E11 alternative, tuning, commit or push was performed. All new work resides in this directory.','',
      'See `cpu_features/*_complete.json` and `factcg_return.json` for timing/runtime evidence, `TEST_RESULTS.txt` for validation, and `E10_OFFICIAL_TEST_SHA256SUMS.txt` for artifact hashes.']
    with (HERE/'E10_OFFICIAL_TEST_RESULTS.md').open('x',encoding='utf-8') as f:f.write('\n'.join(lines)+'\n')
    (HERE/'git_status_short.txt').write_bytes(subprocess.check_output(['git','status','--short'],cwd=ROOT))
    files=sorted(p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='E10_OFFICIAL_TEST_SHA256SUMS.txt')
    (HERE/'E10_OFFICIAL_TEST_SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.relative_to(HERE).as_posix()+'\n' for p in files),encoding='utf-8')
    print('FINAL STATUS: PASS\nEvaluation type: reconstructed retrospective official-test evaluation\nTraining examples: 561\nTest examples: 1500')
    print(json.dumps({'overall':overall,'by_task':result['by_task'],'reconstruction':coverage,'Prediction SHA256':prediction_hash,'deviations':['Wiktionary material reconstructed in 2026'],'No tuning after test scoring':'YES'},indent=2))
if __name__=='__main__':main()
