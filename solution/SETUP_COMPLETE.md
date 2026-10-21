# Project Setup Summary

## ✅ Complete Project Structure Created

Source files are under `solution/`. The data/output directories below are runtime
locations, not a claim that datasets or checkpoints are included. Commands use Bash syntax.

### Directory Tree
```

├── data/
│   ├── raw/              # Place your SHROOM JSON or JSONL files here
│   ├── processed/        # Preprocessed data (auto-generated)
│   └── pseudo/           # Pseudo-labeled data (auto-generated)
│
├── src/
│   ├── __init__.py
│   ├── main.py           # CLI entry point
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py     # JSON/JSONL loading utilities
│   │   └── preprocess.py # SHROOM preprocessing logic
│   ├── models/
│   │   ├── __init__.py
│   │   └── entailment_model.py  # DeBERTa-based entailment model
│   ├── training/
│   │   ├── __init__.py
│   │   ├── train.py      # HuggingFace Trainer-based training
│   │   ├── evaluate.py   # Evaluation with metrics
│   │   └── pseudo_label.py  # Pseudo-label generation
│   └── utils/
│       ├── __init__.py
│       ├── metrics.py    # Accuracy, F1, precision, recall, Spearman
│       └── seed.py       # Reproducibility management
│
├── configs/
│   └── base.yaml         # Default hyperparameters & configuration
│
├── requirements.txt      # All dependencies
├── README.md             # Full documentation
├── QUICKSTART.md         # Quick reference guide
├── .gitignore            # Git ignore patterns
└── create_example_data.py  # Script to create example SHROOM data
```

## 📦 Core Features

### 1. Data Loading (`src/data/loader.py`)
- ✅ Load JSONL/JSON files
- ✅ Save preprocessed data
- ✅ Flexible for any SHROOM format

### 2. Preprocessing (`src/data/preprocess.py`)
- ✅ Automatically map SHROOM fields:
  - `premise` = tgt (DM/MT) or src (PG)
  - `hypothesis` = hyp
  - `label` = binary (1=hallucinated, 0=not)
- ✅ Task type auto-detection
- ✅ DataFrame export

### 3. Model (`src/models/entailment_model.py`)
- ✅ HuggingFace transformer backbone (default: DeBERTa-large)
- ✅ Binary sequence classification head
- ✅ Easy model/tokenizer loading
- ✅ Input format: (premise, hypothesis) pairs

### 4. Training (`src/training/train.py`)
- ✅ HuggingFace Trainer API with checkpointing
- ✅ Automatic GPU/CPU detection
- ✅ Config file support (YAML)
- ✅ Eval loop during training (if eval data provided)
- ✅ Metrics: accuracy, precision, recall, F1

### 5. Evaluation (`src/training/evaluate.py`)
- ✅ Comprehensive metrics calculation
- ✅ Spearman correlation (if probabilities available)
- ✅ Per-example confidence scores
- ✅ Terminal-friendly output

### 6. Pseudo-Labeling (`src/training/pseudo_label.py`)
- ✅ Generate predictions with confidence thresholds
- ✅ Confidence filtering (configurable threshold)
- ✅ Statistics summary
- ✅ Save high-confidence examples

### 7. Utilities
- ✅ Metric computation (`src/utils/metrics.py`)
- ✅ Seed management for reproducibility (`src/utils/seed.py`)

## 🚀 Quick Start

### Step 1: Install dependencies (from the repository root)
```bash
cd solution
pip install -r requirements.txt
```

### Step 2: Create Example Data (for testing)
```bash
python create_example_data.py
```
This creates minimal SHROOM data in `data/raw/train_example.jsonl` and `data/raw/eval_example.jsonl`

### Step 3: Train Model
```bash
python -m src.main train \
  --train_data data/raw/train_example.jsonl \
  --eval_data data/raw/eval_example.jsonl \
  --output_dir ./output \
  --epochs 2 \
  --batch_size 2
```

### Step 4: Evaluate
```bash
python -m src.main evaluate \
  --model_path ./output \
  --data_path data/raw/eval_example.jsonl
```

### Step 5: Generate Pseudo-Labels
```bash
python -m src.main pseudo_label \
  --model_path ./output \
  --data_path data/raw/eval_example.jsonl \
  --output_path data/pseudo/labeled.jsonl \
  --confidence_threshold 0.9
```

## 📊 With Your Real SHROOM Data

1. **Add data files** to `data/raw/`:
   - `train.jsonl`
   - `eval.jsonl` (optional)
   - `test.jsonl` (optional)

2. **Train model**:
   ```bash
   python -m src.main train \
     --train_data data/raw/train.jsonl \
     --eval_data data/raw/eval.jsonl \
     --output_dir ./output
   ```

3. **Example training command**:
   ```bash
   python -m src.main train \
     --config configs/base.yaml \
     --train_data data/raw/train.jsonl \
     --output_dir ./output_v1 \
     --epochs 5 \
     --batch_size 16 \
     --learning_rate 1e-5 \
     --model_name microsoft/deberta-large \
     --max_length 512 \
     --seed 42
   ```

## 🛠️ Code Quality

- ✅ **Type Hints**: Full type annotations throughout
- ✅ **Docstrings**: Every function documented with purpose & args
- ✅ **Modularity**: Clean separation of concerns
- Model and dataset loaders may contact Hugging Face unless artifacts are already available.
- ✅ **GPU/CPU Ready**: Automatic device detection
- ✅ **Reproducibility**: Seed management; exact replay depends on the environment

## 📋 Configuration

For training, only keys explicitly read by `train()` take effect; YAML values override
matching CLI values. `--train_data` remains required by the CLI. Set `--seed` and
pseudo-label `--confidence_threshold` on their respective CLI commands.
See [configuration details](README.md#configuration). Historical YAML example:
```yaml
train_data: data/raw/train.jsonl
eval_data: data/raw/eval.jsonl
model_name: microsoft/deberta-large
epochs: 3
batch_size: 8
learning_rate: 2e-5
max_length: 512
confidence_threshold: 0.8
seed: 42
```

## 💡 Tips for Your MSc Thesis

1. **Baseline Experiments**: Try small models first (deberta-base)
2. **Data Preprocessing**: Check the mapping in `preprocess_shroom()` matches your SHROOM variant
3. **Hyperparameter Tuning**: Use config files to track experiments
4. **Evaluation**: Use both binary classification + correlation metrics
5. **Ablations**: Easily swap models via `--model_name` parameter
6. **Reproducibility**: Always set `--seed` for consistent results

## 📚 References

- **SHROOM**: https://huggingface.co/datasets/mxval/SHROOM
- **DeBERTa**: https://huggingface.co/microsoft/deberta-large
- **HuggingFace Transformers**: https://huggingface.co/transformers/
- **PyTorch**: https://pytorch.org/

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| Out of Memory | Reduce `--batch_size` or `--max_length` |
| Slow Training | Use `deberta-base`, reduce epochs, or subset data |
| CUDA Not Found | Install PyTorch with CUDA support or use `--device cpu` |
| Data Format Error | Check JSONL format: one JSON object per line |
| Label Mapping Wrong | Verify label values in `preprocess_shroom()` |

---

**You're all set! Ready to run your first experiment.**

See `QUICKSTART.md` for minimal commands or `README.md` for full documentation.
