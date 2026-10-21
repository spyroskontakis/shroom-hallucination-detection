"""Pinned direct NLI with explicit pair direction, masks and truncation audits."""
import random
import numpy as np
import v3_common as c


def load_backend():
    import torch
    from transformers import AutoTokenizer,AutoModelForSequenceClassification
    random.seed(42);np.random.seed(42);torch.manual_seed(42)
    tokenizer=AutoTokenizer.from_pretrained(str(c.OUT/'model'),revision=c.REVISION,
                local_files_only=True,trust_remote_code=False,use_fast=True)
    model=AutoModelForSequenceClassification.from_pretrained(str(c.OUT/'model'),revision=c.REVISION,
                local_files_only=True,trust_remote_code=False,use_safetensors=False,dtype=torch.float32)
    model=model.to('cpu').eval()
    assert type(model).__name__=='DebertaV2ForSequenceClassification'
    assert model.config.architectures==['DebertaV2ForSequenceClassification']
    assert model.config.num_labels==1 and model.classifier.out_features==1
    assert tokenizer.is_fast
    model.requires_grad_(False)
    assert not model.training and all(p.dtype==torch.float32 and not p.requires_grad for p in model.parameters())
    card=(c.OUT/'model/README.md').read_text(encoding='utf-8')
    assert 'scores = 1 / (1 + np.exp(-logits)).flatten()' in card
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
        assert logits.shape==(len(pairs),1)
        raw_logits=logits[:,0].cpu().numpy()
        probs=torch.sigmoid(logits[:,0]).cpu().numpy()
    assert probs.shape==(len(pairs),) and np.isfinite(probs).all() and np.isfinite(raw_logits).all()
    assert (probs>=0).all() and (probs<=1).all()
    scores=[{**{k:row[k] for k in ['pair_id','canonical_id','group']},
             'logit':float(raw_logits[i]),'consistency':float(probs[i])} for i,row in enumerate(pairs)]
    return scores,audits
