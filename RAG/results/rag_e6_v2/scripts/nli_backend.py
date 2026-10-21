"""Pinned direct NLI with explicit pair direction, masks and truncation audits."""
import random
import numpy as np
import v2_common as c


def load_backend():
    import torch
    from transformers import AutoTokenizer,AutoModelForSequenceClassification
    random.seed(42);np.random.seed(42);torch.manual_seed(42)
    tokenizer=AutoTokenizer.from_pretrained(str(c.OUT/'model'),revision=c.REVISION,
                local_files_only=True,trust_remote_code=False,use_fast=True)
    model=AutoModelForSequenceClassification.from_pretrained(str(c.OUT/'model'),revision=c.REVISION,
                local_files_only=True,trust_remote_code=False,use_safetensors=True,dtype=torch.float32)
    model=model.to('cpu').eval()
    assert {int(k):v for k,v in model.config.id2label.items()}==dict(enumerate(c.LABELS))
    assert model.config.label2id=={v:i for i,v in enumerate(c.LABELS)} and model.config.num_labels==3
    assert tokenizer.is_fast
    assert not model.training and all(p.dtype==torch.float32 for p in model.parameters())
    card=(c.OUT/'model/README.md').read_text(encoding='utf-8')
    assert 'label_names = ["entailment", "neutral", "contradiction"]' in card
    return tokenizer,model


def infer_batch(tokenizer,model,pairs):
    import torch
    premises=[r['premise'] for r in pairs];hypotheses=[r['hypothesis'] for r in pairs]
    # Untruncated tokenization records exact lengths, never adds model inputs/features.
    raw=tokenizer(premises,hypotheses,truncation=False,padding=False,add_special_tokens=True)
    enc=tokenizer(premises,hypotheses,truncation='longest_first',max_length=512,
                  padding=True,return_attention_mask=True,return_tensors='pt')
    assert 'attention_mask' in enc and enc['input_ids'].shape==enc['attention_mask'].shape
    assert enc['input_ids'].shape[1]<=512
    audits=[]
    for i,row in enumerate(pairs):
        before=raw.sequence_ids(i);after=enc.sequence_ids(i)
        original=len(raw['input_ids'][i]);used=int(enc['attention_mask'][i].sum().item())
        lost_p=before.count(0)-after.count(0);lost_h=before.count(1)-after.count(1)
        assert lost_p>=0 and lost_h>=0 and original-used==lost_p+lost_h
        assert used==min(original,512)
        audits.append({'pair_id':row['pair_id'],'canonical_id':row['canonical_id'],'group':row['group'],
                       'original_tokens':original,'encoded_tokens':used,'truncated':original>512,
                       'premise_tokens_removed':lost_p,'hypothesis_tokens_removed':lost_h,
                       'batch_padded_length':int(enc['input_ids'].shape[1])})
    with torch.inference_mode():
        logits=model(**{k:v.to('cpu') for k,v in enc.items()}).logits
        probs=torch.softmax(logits,dim=-1).cpu().numpy()
    assert probs.shape==(len(pairs),3) and np.isfinite(probs).all()
    assert (probs>=0).all() and (probs<=1).all()
    assert np.allclose(probs.sum(axis=1),1,atol=2e-7,rtol=0)
    scores=[{**{k:row[k] for k in ['pair_id','canonical_id','group']},
             **{label:float(probs[i,j]) for j,label in enumerate(c.LABELS)}} for i,row in enumerate(pairs)]
    return scores,audits
