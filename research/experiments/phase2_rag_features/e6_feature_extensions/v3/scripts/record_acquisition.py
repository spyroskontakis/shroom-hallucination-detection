"""Verify authorized pinned download; record exact sources and content hashes."""
if "_H2_CTX" not in globals():
    raise RuntimeError("Historical source: use the pinned cross-experiment context; direct execution/import is disabled")
import v3_common as c

def main():
    api=c.read_json(c.OUT/'provenance/hf_revision_api.json')
    assert api['sha']==c.REVISION and api['id']==c.MODEL_ID
    names=['README.md','config.json','added_tokens.json','special_tokens_map.json','spm.model',
           'tokenizer.json','tokenizer_config.json','pytorch_model.bin']
    assert set(names).issubset({s['rfilename'] for s in api['siblings']})
    config=c.read_json(c.OUT/'model/config.json')
    assert config['architectures']==['DebertaV2ForSequenceClassification'] and len(config['id2label'])==1
    card=(c.OUT/'model/README.md').read_text(encoding='utf-8')
    assert 'scores = 1 / (1 + np.exp(-logits)).flatten()' in card
    files={n:{'path':'model/'+n,'bytes':(c.OUT/'model'/n).stat().st_size,'sha256':c.sha(c.OUT/'model'/n),
              'url':f'https://huggingface.co/{c.MODEL_ID}/resolve/{c.REVISION}/{n}'} for n in names}
    headers=(c.OUT/'provenance/weights_headers.txt').read_text(encoding='utf-8')
    import re
    linked=re.search(r'x-linked-etag:\s*"?([a-f0-9]{64})',headers,re.I)
    assert linked and linked[1]==files['pytorch_model.bin']['sha256']
    c.write_json(c.OUT/'provenance/acquisition.json',{'created_utc':c.now(),'model_id':c.MODEL_ID,
                 'revision':c.REVISION,'historical_name':'hhem-1.0-open','files':files,
                 'weight_sha256_matches_hub_linked_etag':True,
                 'declared_training_datasets':api['cardData']['datasets'],
                 'base_model':'microsoft/deberta-v3-base','training_claims_source':'pinned model card',
                 'contamination_independently_audited':False,'architecture':config['architectures'],
                 'outputs':1,'score':'sigmoid(raw output logit), once; high means supported',
                 'historical_transform_evidence':'README.md Usage with Transformers AutoModel: scores = 1 / (1 + np.exp(-logits)).flatten()',
                 'remote_code':False,'download_tool':'curl.exe pinned revision URLs only'})
    print({'acquisition':'PASS','weight_bytes':files['pytorch_model.bin']['bytes']},flush=True)

if __name__=='__main__':main()
