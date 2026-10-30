"""Fixed pairwise cosine embedding objective; no learned projection or sampling."""

def sequence_masks(encoded):
    masks = []
    for i in range(len(encoded['input_ids'])):
        ids = encoded.sequence_ids(i)
        a, b = [s == 0 for s in ids], [s == 1 for s in ids]
        if not any(a) or not any(b):
            raise ValueError('both truncated sequences must retain tokens')
        masks.append((a, b))
    return masks


def pair_loss(hidden, mask_a, mask_b, labels, margin=0.0):
    import torch
    import torch.nn.functional as F
    if not bool(((mask_a.sum(1) > 0) & (mask_b.sum(1) > 0)).all()):
        raise ValueError('empty sequence representation')
    if bool((mask_a & mask_b).any()) or not bool(((labels == 0) | (labels == 1)).all()):
        raise ValueError('invalid masks or labels')
    def pool(mask):
        return (hidden.float() * mask.unsqueeze(-1)).sum(1) / mask.sum(1, keepdim=True)
    similarity = F.cosine_similarity(pool(mask_a), pool(mask_b), dim=-1, eps=1e-8)
    return torch.where(labels == 0, 1 - similarity, (similarity - margin).clamp_min(0)).mean()
