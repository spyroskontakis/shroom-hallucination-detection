"""Pre-freeze adaptation of the accepted local E6-v2 implementation; never edits it."""
from pathlib import Path
out=Path(__file__).resolve().parent
old=out.parent.parent/'rag_e6_v2/scripts'

def save(name,text):
    with (out/name).open('x',encoding='utf-8',newline='\n') as f:f.write(text)

common=(old/'v2_common.py').read_text(encoding='utf-8')
common=common.replace('E6-v2','E6-v3').replace("V1=ROOT", "V2=ROOT/'RAG/results/rag_e6_v2'\nV1=ROOT")
begin=common.index("MODEL_ID=");end=common.index('\n\n\ndef now')
common=common[:begin]+'''MODEL_ID='vectara/hallucination_evaluation_model'
REVISION='58383384656cbaec2949a75a41f20e891e90a73b'
NEW=['hhem_ref_hyp_consistency','hhem_definition_hyp_consistency']
'''+common[end:]
common=common.replace("log=OUT/f'config/network_attempts_{phase}.jsonl'", "from uuid import uuid4\n    log=OUT/f'config/network_attempts_{phase}_{uuid4().hex}.jsonl'")
save('v3_common.py',common)

smoke=(old/'smoke_nli.py').read_text(encoding='utf-8').replace('v2_common','v3_common').replace('nli_backend','hhem_backend')
save('smoke_hhem.py',smoke)

backend=(old/'nli_backend.py').read_text(encoding='utf-8').replace('v2_common','v3_common')
backend=backend.replace('use_safetensors=True','use_safetensors=False')
begin=backend.index('    assert {int(k)');end=backend.index('    return tokenizer,model')
backend=backend[:begin]+'''    assert type(model).__name__=='DebertaV2ForSequenceClassification'
    assert model.config.architectures==['DebertaV2ForSequenceClassification']
    assert model.config.num_labels==1 and model.classifier.out_features==1
    assert tokenizer.is_fast
    model.requires_grad_(False)
    assert not model.training and all(p.dtype==torch.float32 and not p.requires_grad for p in model.parameters())
    card=(c.OUT/'model/README.md').read_text(encoding='utf-8')
    assert 'scores = 1 / (1 + np.exp(-logits)).flatten()' in card
'''+backend[end:]
begin=backend.index('        probs=torch.softmax')
backend=backend[:begin]+'''        assert logits.shape==(len(pairs),1)
        raw_logits=logits[:,0].cpu().numpy()
        probs=torch.sigmoid(logits[:,0]).cpu().numpy()
    assert probs.shape==(len(pairs),) and np.isfinite(probs).all() and np.isfinite(raw_logits).all()
    assert (probs>=0).all() and (probs<=1).all()
    scores=[{**{k:row[k] for k in ['pair_id','canonical_id','group']},
             'logit':float(raw_logits[i]),'consistency':float(probs[i])} for i,row in enumerate(pairs)]
    return scores,audits
'''
save('hhem_backend.py',backend)

evaluation=(old/'evaluate_v2.py').read_text(encoding='utf-8')
evaluation=evaluation.replace('E6-v2','E6-v3').replace('E6-v1','E6-v2').replace('e6_v2','e6_v3').replace('e6_v1','e6_v2')
evaluation=evaluation.replace('v2_common','v3_common').replace('c.V1','c.V2').replace('e6_25_features.csv','e6_v2_34_features.csv').replace('e6_v3_34_features.csv','e6_v3_36_features.csv').replace('[:,:26]','[:,:35]')
evaluation=evaluation.replace("saved=pd.read_csv(c.V2/'evaluation/e6_oof_predictions.csv')", "saved=pd.read_csv(c.V2/'evaluation/e6_v2_oof_predictions.csv',float_precision='round_trip')")
evaluation=evaluation.replace("c.V2/'evaluation/e6_metrics.json'","c.V2/'evaluation/e6_v2_metrics.json'").replace("['all_rows']['E6']","['all_rows']['E6-v2']").replace("observed['correct']==453","observed['correct']==473")
begin=evaluation.index('    fresh=pd.read_csv');end=evaluation.index('    return f,lock,check')
evaluation=evaluation[:begin]+'''    baseline_rows=pd.read_csv(c.V2/'evaluation/paired_row_diagnostics.csv',float_precision='round_trip')
    assert baseline_rows.canonical_id.tolist()==ids
    for key in ['fold_id','label_bin','p_hallucination','E6-v2']:
        assert np.array_equal(baseline_rows[key],f[key]),key
    check={'status':'PASS','metrics':observed,'canonical_ids_folds':'exact match',
           'e6_v2_features_unchanged':True,'new_baseline_fits':0,
           'prediction_and_row_diagnostics_exact':True}
'''+evaluation[end:]
save('evaluate_v3.py',evaluation)
print('Adapted common/backend/smoke/evaluation into E6-v3 only')
