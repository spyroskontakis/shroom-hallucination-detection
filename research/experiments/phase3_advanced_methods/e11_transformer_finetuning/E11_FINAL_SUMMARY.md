# E11 final frozen summary

**PASS — suite frozen from authoritative repository artifacts.** No training, new-model evaluation, API calls, tuning or official-test access occurred during finalization.

| Experiment | Human | Synthetic | Contrastive | Correct/561 | Accuracy | Spearman |
|---|---|---|---|---:|---:|---:|
| E11-A | Yes | No | No | 460 | 0.8199643493761141 | 0.7172565081322899 |
| E11-B | feasibility only | pseudo-label ensemble | No | — | — | — |
| E11-C | Yes | Yes | No | 466 | 0.8306595365418895 | 0.7270182116026076 |
| E11-D | Yes | No | Yes | 459 | 0.8181818181818182 | 0.7006748393613571 |
| E11-E | Yes | Yes | Yes | 466 | 0.8306595365418895 | 0.7150820586520120 |
| E10 | feature-based reference | — | — | 475 | 0.8467023172905526 | 0.7828092941190203 |

## Descriptive conclusions

1. Synthetic supervision helped: E11-C versus E11-A gained 6 correct, +0.010695187166 accuracy and +0.009761703470 Spearman.
2. Contrastive learning did not help human-only training: E11-D versus E11-A lost 1 correct, -0.001782531194 accuracy and -0.016581668771 Spearman.
3. Contrastive learning did not improve synthetic-supervision training: E11-E tied E11-C at 466/561 and identical accuracy, with -0.011936152951 Spearman.
4. **E11-C is the best E11 variant overall:** tied highest accuracy with E11-E and highest Spearman.
5. No E11 variant exceeded E10 on either metric. These are descriptive comparisons; no statistical significance claim is made.

## E11-B feasibility branch

FactCG / MiniCheck / HHEM / NLI scores fed five fold-specific logistic teachers. At the frozen confidence thresholds (p(H) ≥ .95 or ≤ .05), accepted rows before balancing were 0 / 50 / 0 / 44 / 41. Every task/fold lacked at least one accepted class. Required per-task 50/50 balancing retained 0 / 0 / 0 / 0 / 0 rows. Therefore no final student training or OOF evaluation was performed, and Accuracy/Spearman are not applicable—not zero.
The four detector datasets each cover 28,649 unlabeled inputs; human MiniCheck covers 561. B teacher fits are separate from student fits.

## Synthetic supervision

Frozen teacher: **gpt-5.6-sol**, medium reasoning. Frozen pool: **12,000 candidates**. Original outcomes: **11,887 definitive binary labels** (5,111 hallucination; 6,776 not_hallucination), **109 uncertain**, and **four technical failures**. The original teacher ledger has 11,996 terminal responses; its billing-blocked audit status is preserved.
The four PG failures received separate Azure / Microsoft Foundry gpt-5-mini judgments: **one hallucination and three not_hallucination**. They were never merged into the homogeneous gpt-5.6-sol pool. Uncertain outcomes were also excluded.
Identical-input exclusions: **82 rows = 76 redundant rows + six conflicting-label rows across three groups**. C and E use exactly the same prepared bytes and exclusions.

| Fold | Validation-overlap exclusions | Synthetic rows for C/E | Human training | Held out |
|---|---:|---:|---:|---:|
| 1 | 18 | 11787 | 448 | 113 |
| 2 | 14 | 11791 | 449 | 112 |
| 3 | 10 | 11795 | 449 | 112 |
| 4 | 18 | 11787 | 449 | 112 |
| 5 | 15 | 11790 | 449 | 112 |

Leakage filtering uses the frozen normalized content/source rules. Undocumented upstream semantic derivations cannot be proven absent.

Final fold fits: A = five human-only; D = five human-only; C = five synthetic Stage-1 plus five human Stage-2; E = five synthetic Stage-1 plus five human Stage-2. These are final CV fit counts, separate from B’s five logistic teacher fits and any historical smoke checks.

## Frozen contrastive objective

```text
weighted CE + 0.1 × mean[
  (1-y)(1-cos(a,b)) +
  y * max(0, cos(a,b))
]
```
y=1 means hallucination; lambda=0.1; margin=0; no temperature. Mean-pooled final-layer representations exclude special/padding tokens and retain textual prefixes. Cosine uses L2 normalization (float32, eps=1e-8). The two representations share the original cross-encoder context. The implementation is identical in D/E; E applies it in both stages.

## Task-level results

| Experiment | Task | Correct/total | Accuracy | Spearman |
|---|---|---:|---:|---:|
| E11-C | DM | 169/211 | 0.8009478672985783 | 0.7100092641415214 |
| E11-C | MT | 190/216 | 0.8796296296296297 | 0.7530345044540484 |
| E11-C | PG | 107/134 | 0.7985074626865671 | 0.6414990114741199 |
| E11-D | DM | 165/211 | 0.7819905213270142 | 0.6653189488032746 |
| E11-D | MT | 190/216 | 0.8796296296296297 | 0.7306895059974191 |
| E11-D | PG | 104/134 | 0.7761194029850746 | 0.6001639041522990 |
| E11-E | DM | 170/211 | 0.8056872037914692 | 0.7068963952073648 |
| E11-E | MT | 190/216 | 0.8796296296296297 | 0.7417281785098279 |
| E11-E | PG | 106/134 | 0.7910447761194029 | 0.6260045856509603 |

MT consistently had the highest accuracy (190/216 in C, D and E). PG remained more difficult, especially in Spearman, which was the lowest task ranking score in all three variants.

## Reproducibility and verification

Model: `MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli`. Exact revision: `b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7`. Pinned fast tokenizer, longest-first paired truncation, maximum 512 tokens. DM/MT reference = tgt; PG reference = src. Seed 42.
AdamW, LR 1e-5, weight decay .01, batch 8, gradient accumulation 2 (effective 16), evaluation batch 16, BF16 on one A100-80GB per fold, clip norm 1. Linear warmup for ceil(.1 × updates), then linear decay to zero. Weighted CE uses N/(2 × class count) from each stage/fold training split. Human adaptation uses five epochs; synthetic Stage 1 uses one fixed epoch. Final checkpoints only, threshold .5, no early stopping or search.
Python 3.11.12 and PyTorch 2.2.1+cu121 are recorded for all student variants. C/D/E explicitly record CUDA 12.1, Transformers 4.38.1, NumPy 1.26.4 and tokenizers 0.15.2. A uses the same frozen software lock; its fold statuses explicitly record Python/PyTorch. A/D used A100-SXM4-80GB and A100 80GB PCIe; C/E used A100-SXM4-80GB. Full runtime records and GPU sets are in the JSON.
Fold definition: `codex/canonical_fold_assignments.csv`; SHA256 `f5a5964923806a23dd34a8bcc137f3cf489437e033d645e9d0845bf40792eb5d`. Canonical human SHA256 `754b66c6c4eca2e92902d0408db4854e922d7dfb396953a0cc043c5477bd6a9b`.
Synthetic teacher protocol **content** SHA256: `792bbe4ef1d0752e606c81dc511684f7bb0a051b2a5c24a937c49d7cb928f818`. The source manifest separately records its JSON file-byte hash. Definitive export SHA256: `b071f6f01db297393cff6c64e7614ad9c241e8da28379a21740b0e5d3d50ccea`.
D/E contrastive implementation SHA256: `62f8f95a535ab6667a75f49e28986cb3fc9457fa72ede7cd09496bae117d1b67`.
Finalization: **111 offline tests passed, zero skipped; 35 named verification groups passed**, including the two independent read-only B validators. All **686 prior E11/E10 files** remained byte-for-byte unchanged; interpreter caches are excluded from artifact accounting.
Existing A/C/D/E OOF vectors were replayed using the unchanged authoritative metric function; no model was loaded to generate predictions. Five local A checkpoints were rehashed. Prior independent remote rehash records for C (10), D (5), E (10) were matched to local return records and initialization chains. No remote checkpoint API was called during this freeze.
Historical final suites recorded C=79, D=94, E=111 passing tests; these overlapping runs are not additive. Historical protection audits recorded C unchanged, D=507 files unchanged and E=550 files unchanged. Full checkpoint and source hashes are retained in the JSON summary/manifest.

## Final artifacts

- `E11_FINAL_SUMMARY.md` and `E11_FINAL_SUMMARY.json`: consolidated aggregate report.
- `E11_FINAL_TABLE.csv`: six aggregate rows only; retained locally under the existing global CSV ignore rule.
- `E11_FINAL_MANIFEST.json`: output, source, verification and checkpoint hashes.
- `E11_FINAL_SHA256SUMS.txt`: final file hashes, including the manifest (avoids self-reference).

Prior artifacts are preserved. No new training, APIs, official-test access, tuning, commit, push or E11-F.
