# Hallucination Detection Using Entailment

An entailment-based system for detecting hallucinations in NLP model outputs using the SHROOM dataset.

## Project Structure

```
├── data/
│   ├── raw/              # Raw SHROOM dataset
│   ├── processed/        # Preprocessed data
│   └── pseudo/           # Pseudo-labeled data
├── src/
│   ├── data/
│   │   ├── loader.py     # Data loading utilities
│   │   ├── preprocess.py # SHROOM field mapping
│   ├── models/
│   │   ├── entailment_model.py  # Base entailment model
│   ├── training/
│   │   ├── train.py      # Training script
│   │   ├── evaluate.py   # Evaluation script
│   │   ├── ensemble_meta_train.py # Ensemble meta-classifier
│   │   └── pseudo_label.py      # Pseudo-labeling
│   ├── utils/
│   │   ├── metrics.py    # Metrics computation
│   │   └── seed.py       # Seed management
│   └── main.py           # CLI entry point
├── configs/
│   └── base.yaml         # Default configuration
├── requirements.txt
└── README.md
```

## Installation

Run the examples from `research/prototypes/entailment_prototype/` (`cd research/prototypes/entailment_prototype` from the repository root).
Commands below use Bash continuation syntax. Data and model files are external
inputs, not included in this repository. These examples are not E1-E11 results;
see the [experiment index](../../../docs/EXPERIMENTS.md) and [results](../../../docs/RESULTS.md).

```bash
pip install -r requirements.txt
```

## Quickstart

### 1. Prepare Data

Place your SHROOM dataset JSON or JSONL files in `data/raw/`. The loader automatically detects the format:
- `train.model-agnostic.json` or `train.jsonl` - Training set
- `eval.model-agnostic.json` or `eval.jsonl` - Validation set (optional)
- `test.model-agnostic.json` or `test.jsonl` - Test set

Expected SHROOM format:
```json
{
  "src": "source text",
  "tgt": "target text",
  "hyp": "hypothesis text",
  "label": "hallucinated or not hallucinated",
  "task": "DM/MT/PG"
}
```

### 2. Train Model

```bash
# Basic training
python -m src.main train --train_data data/raw/train.model-agnostic.json --eval_data data/raw/eval.model-agnostic.json --output_dir ./output

# With custom config
python -m src.main train --config configs/base.yaml --train_data data/raw/train.jsonl

# Custom parameters
python -m src.main train --train_data data/raw/train.model-agnostic.json --eval_data data/raw/eval.model-agnostic.json --model_name microsoft/deberta-large --epochs 5 --batch_size 16 --learning_rate 1e-5 --output_dir ./output
```

**Training Metrics:**
- Accuracy
- Precision
- Recall
- F1 Score

### 3. Evaluate Model

```bash
# Evaluate on test set
python -m src.main evaluate --model_path ./output --data_path data/raw/test.model-agnostic.json

# Evaluation metrics include:
# - Accuracy
# - Precision (binary)
# - Recall (binary)
# - F1 Score
# - Spearman Correlation (with probabilities)
```

### 4. Generate Pseudo-Labels

Use a trained model to generate pseudo-labels for unlabeled data:

```bash
# Basic pseudo-labeling
python -m src.main pseudo_label --model_path ./output --data_path data/raw/unlabeled.jsonl --output_path data/pseudo/labeled.jsonl

# With confidence threshold
python -m src.main pseudo_label --model_path ./output --data_path data/raw/unlabeled.jsonl --output_path data/pseudo/labeled.jsonl --confidence_threshold 0.9
```

Output includes:
- `pseudo_label`: Predicted label (0 or 1)
- `pseudo_confidence`: Model confidence score
- `high_confidence`: Boolean flag for high-confidence predictions

## Architecture

### Model
- **Base**: Pre-trained transformer (default: DeBERTa-large)
- **Task**: Binary sequence classification
- **Input**: (premise, hypothesis) pairs
- **Output**: Binary classification logits + probabilities

### Preprocessing
Maps SHROOM fields:
- **premise** = `tgt` (DM/MT) or `src` (PG)
- **hypothesis** = `hyp`
- **label** = 1 (hallucinated) or 0 (not hallucinated)

### Training
- HuggingFace Trainer API
- Loss: Cross-entropy
- Optimizer: AdamW with weight decay
- LR scheduler: Linear with warmup

## Supported options and ensemble training

The CLI provides `train`, `evaluate`, `pseudo_label`, `pretrain_nli` and
`ensemble_meta`. Use `python -m src.main COMMAND --help` for their arguments.
`--fp16`, `--gradient_accumulation_steps`, `--use_focal_loss` and `--device`
are not exposed by this CLI. The preprocessing module maps SHROOM fields;
it does not implement the previously described pruning/curriculum helpers.

The meta-classifier is implemented in `src/training/ensemble_meta_train.py`.
It combines two logits per base model using a hidden layer of size 128,
ReLU, dropout 0.2 and a two-output layer. Example with existing base checkpoints:

```bash
python -m src.main ensemble_meta \
  --model_paths ./output_model1 ./output_model2 \
  --train_data data/raw/train.jsonl \
  --eval_data data/raw/eval.jsonl \
  --output_dir ./ensemble_output
```

This is an interface example, not evidence of an improvement over a baseline.

## Configuration

`train` reads these YAML keys: `train_data`, `eval_data`, `model_name`,
`output_dir`, `epochs`, `batch_size`, `learning_rate`, `max_length`, `task_type`.
Values present in the YAML override the corresponding CLI values. The parser
still requires `--train_data` when `--config` is supplied. Set `--seed` on the CLI.

```yaml
model_name: microsoft/deberta-large
epochs: 3
batch_size: 8
learning_rate: 2e-5
max_length: 512
```

Additional settings in the historical base YAML are not automatically consumed.
For example, warmup and weight decay are currently fixed in the training code;
adding scheduler, dropout or focal-loss keys does not enable those features.
Use `--confidence_threshold` with `pseudo_label`, not as a training YAML option.
Reduce `--batch_size` or `--max_length` if memory is insufficient. Device selection
is automatic; seed configuration alone does not guarantee exact replay.

## Citation

If you use this project, please cite:

```bibtex
@inproceedings{shroom,
  title={SHROOM: A Shared-task on Hallucination and Related Observable Inconsistency Measures},
  year={2023}
}
```

## References

- [SHROOM Dataset](https://github.com/google-research-datasets/SHROOM)
- [DeBERTa](https://huggingface.co/microsoft/deberta-large)
- [HuggingFace Transformers](https://huggingface.co/transformers/)
- [PyTorch](https://pytorch.org/)

## Baseline Checkpoint

`exp_baseline_v1` is the repository's baseline reference point using simple entailment classification.

**Historically recorded baseline metrics** (not remeasured during this review):
- Accuracy: 0.6247
- Precision: 0.5393
- Recall: 0.5385
- F1: 0.5389
- Spearman correlation: 0.2277

## Historical orchestration example

`train_best_pipeline.py` orchestrates NLI pre-training, multiple independent
SHROOM training runs and meta-classifier training. It is retained as historical
code, not as a validated reproduction of E1-E11.

```bash
python train_best_pipeline.py \
  --train_data data/raw/train.model-agnostic.json \
  --eval_data data/raw/eval.model-agnostic.json \
  --test_data data/raw/test.model-agnostic.json \
  --num_seeds 5
```

Limitations visible in the source:
- The SHROOM runs use `model_base`, not the preceding NLI checkpoint.
- `test_data` is required by the parser but is not used for evaluation.
- The fixed seed list contains five entries; larger `num_seeds` values do not add runs.
- The performance estimates printed by the script are hard-coded expectations,
  not measured outputs. No accuracy, F1 or speed improvement is promised here.

### Detailed Step-by-Step

**Step 1: NLI Pre-training**
```bash
python -m src.main pretrain_nli \
  --output_dir ./models/nli_pretrain \
  --model_name microsoft/deberta-large \
  --use_snli \
  --use_mnli \
  --epochs 1 \
  --batch_size 16 \
  --learning_rate 2e-5
```

**Step 2: Train the base model with five seeds (does not load Step 1 output)**
```bash
for SEED in 42 100 200 300 400; do
  python -m src.main train \
    --train_data data/raw/train.model-agnostic.json \
    --eval_data data/raw/eval.model-agnostic.json \
    --output_dir ./models/ensemble_seeds/model_seed_$SEED \
    --epochs 5 \
    --batch_size 16 \
    --learning_rate 2e-5 \
    --seed $SEED
done
```

**Step 3: Train Ensemble Meta-Classifier**
```bash
python -m src.main ensemble_meta \
  --model_paths \
    ./models/ensemble_seeds/model_seed_42 \
    ./models/ensemble_seeds/model_seed_100 \
    ./models/ensemble_seeds/model_seed_200 \
    ./models/ensemble_seeds/model_seed_300 \
    ./models/ensemble_seeds/model_seed_400 \
  --train_data data/raw/train.model-agnostic.json \
  --eval_data data/raw/eval.model-agnostic.json \
  --output_dir ./models/ensemble_final \
  --epochs 5 \
  --batch_size 32 \
  --learning_rate 1e-3
```

---

For measured thesis results and their evaluation scope, see [RESULTS](../../../docs/RESULTS.md).
