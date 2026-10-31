"""Lightweight HF adapter for the official FactCG semantics (MIT; see upstream/LICENSE).

Reference: derenlei/FactCG at 41f185413312ed9b3904ec03963fe899693498e0.
No Lightning/training imports. The released HF inference uses unscaled class-1
softmax, a fixed instruction string, and max pooling over reference chunks.
"""
from factcg_common import MODEL, REVISION, SETTINGS, require

INSTRUCTION_TEMPLATE = '{text_a}\n\nChoose your answer: based on the paragraph above can we conclude that "{text_b}"?\n\nOPTIONS:\n- Yes\n- No\nI think the answer is '

def chunk_reference(src):
    # Same sentence and word tokenization, newline joins and empty leading chunk
    # behavior as upstream Inferencer.chunking_src; no hypothesis decomposition.
    import nltk
    chunks, chunk, size = [], '', 0
    for sentence in nltk.sent_tokenize(src):
        count = len(nltk.word_tokenize(sentence))
        if size + count <= 550:
            chunk = '\n'.join([chunk, sentence]).strip('\n')
            size += count
        else:
            chunks.append(chunk.strip('\n'))
            chunk, size = sentence, count
    if size > 0:
        chunks.append(chunk.replace(' \n ', '\n').strip('\n').strip())
    return chunks

def tokenize(tokenizer, references, hypotheses):
    texts = [INSTRUCTION_TEMPLATE.format(text_a=a, text_b=b) for a, b in zip(references, hypotheses)]
    tokenizer.pad_token = tokenizer.eos_token
    # Upstream's normal DeBERTa path; exceptions stop instead of invoking its
    # broad exception fallback (which references an undefined logging module).
    return tokenizer(texts, max_length=2048, truncation='only_first',
                     padding='longest', return_tensors='pt')

def load(cache_dir):
    import torch
    from transformers import AutoConfig, AutoTokenizer, AutoModelForSequenceClassification
    kwargs = dict(revision=REVISION, cache_dir=str(cache_dir), trust_remote_code=False)
    config = AutoConfig.from_pretrained(MODEL, num_labels=2, finetuning_task='text-classification', **kwargs)
    require(config.model_type == 'deberta-v2' and config.num_labels == 2, 'released classifier architecture')
    config.problem_type = 'single_label_classification'
    tokenizer = AutoTokenizer.from_pretrained(MODEL, use_fast=True, **kwargs)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL, config=config, use_safetensors=True, torch_dtype=torch.float32,
        ignore_mismatched_sizes=False, **kwargs).to('cuda:0').eval()
    require(next(model.parameters()).dtype == torch.float32 and next(model.parameters()).device.type == 'cuda', 'CUDA float32 model')
    require(config._commit_hash == REVISION, 'resolved revision')
    return tokenizer, model

def score(tokenizer, model, reference, whole_hypothesis):
    import torch
    chunks = chunk_reference(reference)
    require(bool(chunks), 'reference produced no official chunks')
    probabilities, lengths = [], []
    for chunk in chunks:
        text = INSTRUCTION_TEMPLATE.format(text_a=chunk, text_b=whole_hypothesis)
        lengths.append(len(tokenizer(text, truncation=False)['input_ids']))
        inputs = tokenize(tokenizer, [chunk], [whole_hypothesis])
        inputs = {k: v.to('cuda:0') for k, v in inputs.items()}
        with torch.no_grad():
            probabilities.append(torch.softmax(model(**inputs).logits, dim=-1)[0, 1].item())
    return max(probabilities), dict(reference_chunks=len(chunks),
                                   max_untruncated_tokens=max(lengths),
                                   truncated_chunks=sum(n > 2048 for n in lengths))
