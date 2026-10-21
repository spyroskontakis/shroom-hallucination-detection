# QUICKSTART GUIDE

## Example setup

From the repository root, run `cd solution` first. Examples use Bash syntax.
Dependencies, datasets and model downloads must be provided separately.
These commands are usage examples, not measured thesis experiments.

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Create Example Data
```bash
python create_example_data.py
```
This creates minimal example SHROOM data in `data/raw/`.

### 3. Train on examples (runtime depends on the environment)
```bash
python -m src.main train --train_data data/raw/train_example.jsonl --eval_data data/raw/eval_example.jsonl --output_dir ./output --epochs 2 --batch_size 2
```

### 4. Evaluate
```bash
python -m src.main evaluate --model_path ./output --data_path data/raw/eval_example.jsonl
```

Evaluation reports classification metrics and, where defined, correlation.
Scores on tiny synthetic examples do not establish performance on SHROOM.

---

## With Your SHROOM Dataset

### 1. Add Data
Place your SHROOM JSON or JSONL files in `data/raw/`. Supports both formats:
- `train.model-agnostic.json` or `train.jsonl`
- `eval.model-agnostic.json` or `eval.jsonl` (optional)
- `test.model-agnostic.json` or `test.jsonl` (optional)

### 2. Train
```bash
python -m src.main train --train_data data/raw/train.model-agnostic.json --eval_data data/raw/eval.model-agnostic.json --output_dir ./output --epochs 3 --batch_size 8 --learning_rate 2e-5
```

### 3. Evaluate
```bash
python -m src.main evaluate --model_path ./output --data_path data/raw/test.model-agnostic.json
```

### 4. Pseudo-Label (Optional)
```bash
python -m src.main pseudo_label --model_path ./output --data_path data/raw/unlabeled.jsonl --output_path data/pseudo/labeled.jsonl --confidence_threshold 0.9
```

---

## Troubleshooting

**Out of Memory?**
- Reduce `--batch_size` (e.g., 4)
- Reduce `--max_length` (e.g., 256)

**Slow Training?**
- Use smaller model: `--model_name microsoft/deberta-base`
- Reduce dataset size
- Enable GPU: Ensure CUDA is installed

**Data Format Issues?**
- Each line must be valid JSON
- Required fields: `tgt`/`src`, `hyp`, `label`
- `label` format: "hallucinated" or "not_hallucinated"

---

## Project Structure

```
├── data/
│   ├── raw/          ← Put your JSONL files here
│   ├── processed/    ← Output of preprocessing
│   └── pseudo/       ← Pseudo-labeled data
├── src/
│   ├── data/         ← Loading & preprocessing
│   ├── models/       ← Model architecture
│   ├── training/     ← Training, evaluation, pseudo-labeling
│   ├── utils/        ← Metrics, seeds
│   └── main.py       ← CLI entry point
├── configs/
│   └── base.yaml     ← Configuration
├── output/           ← Model checkpoints
├── requirements.txt
└── README.md
```

---

## Additional interfaces and limitations

The supported ensemble command is `ensemble_meta`, implemented in
`src/training/ensemble_meta_train.py`:

```bash
python -m src.main ensemble_meta \
  --model_paths ./output_model1 ./output_model2 \
  --train_data data/raw/train.jsonl \
  --eval_data data/raw/eval.jsonl \
  --output_dir ./ensemble_output
```

The checkpoint paths must already exist. The CLI does not accept `--fp16`,
`--gradient_accumulation_steps`, `--use_focal_loss` or `--device`.

The historical `train_best_pipeline.py` script is not a validated end-to-end
reproduction: it does not use its NLI checkpoint for subsequent SHROOM training,
and its required `test_data` argument is unused. Its printed performance estimates
are not measurements. See [README](README.md#historical-orchestration-example)
for the supported invocation and limitations, and [thesis results](../docs/RESULTS.md)
for documented experiments.
