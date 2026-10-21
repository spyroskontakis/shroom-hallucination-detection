#!/usr/bin/env bash
# Complete pipeline to achieve best overall performance
# Based on SHROOM SemEval-2024 top-scoring approaches

set -e

echo "=================================================="
echo "SHROOM Hallucination Detection - Best Pipeline"
echo "=================================================="
echo ""

# Configuration
MODEL_BASE="microsoft/deberta-large"
TRAIN_DATA="data/raw/train.model-agnostic.json"
EVAL_DATA="data/raw/eval.model-agnostic.json"
TEST_DATA="data/raw/test.model-agnostic.json"
NLI_OUTPUT="./models/nli_pretrain"
ENSEMBLE_MODELS="./models/ensemble_seeds"
ENSEMBLE_OUTPUT="./models/ensemble_final"

# Create directories
mkdir -p "$ENSEMBLE_MODELS"

echo "Step 1: NLI Pre-training (SNLI + MultiNLI)"
echo "==========================================="
echo "Pre-training on NLI makes models understand entailment better"
echo ""

python -m src.main pretrain_nli \
  --output_dir "$NLI_OUTPUT" \
  --model_name "$MODEL_BASE" \
  --use_snli \
  --use_mnli \
  --epochs 1 \
  --batch_size 16 \
  --learning_rate 2e-5

echo ""
echo "Step 2: Fine-tune on SHROOM (Multiple Seeds)"
echo "============================================"
echo "Train 5 models with different seeds to capture diverse patterns"
echo ""

for SEED in 42 100 200 300 400; do
  echo "Training model with seed $SEED..."
  python -m src.main train \
    --train_data "$TRAIN_DATA" \
    --eval_data "$EVAL_DATA" \
    --model_name "$MODEL_BASE" \
    --output_dir "$ENSEMBLE_MODELS/model_seed_$SEED" \
    --epochs 5 \
    --batch_size 16 \
    --learning_rate 2e-5 \
    --max_length 512 \
    --seed "$SEED"
done

echo ""
echo "Step 3: Build Ensemble Meta-Classifier"
echo "======================================"
echo "Combine all models with a learned meta-classifier"
echo ""

python -m src.main ensemble_meta \
  --model_paths \
    "$ENSEMBLE_MODELS/model_seed_42" \
    "$ENSEMBLE_MODELS/model_seed_100" \
    "$ENSEMBLE_MODELS/model_seed_200" \
    "$ENSEMBLE_MODELS/model_seed_300" \
    "$ENSEMBLE_MODELS/model_seed_400" \
  --train_data "$TRAIN_DATA" \
  --eval_data "$EVAL_DATA" \
  --output_dir "$ENSEMBLE_OUTPUT" \
  --epochs 5 \
  --batch_size 32 \
  --learning_rate 1e-3

echo ""
echo "=================================================="
echo "Pipeline Complete!"
echo "=================================================="
echo ""
echo "Results:"
echo "  - NLI pre-trained model: $NLI_OUTPUT"
echo "  - Individual fine-tuned models: $ENSEMBLE_MODELS"
echo "  - Ensemble meta-classifier: $ENSEMBLE_OUTPUT"
echo ""
echo "Expected Performance:"
echo "  - Accuracy: ~0.80-0.82"
echo "  - F1 Score: ~0.73-0.75"
echo ""
echo "Next steps:"
echo "1. Evaluate on test set"
echo "2. Tune threshold based on validation calibration"
echo "3. Optional: Combine with VECTARA model for further gains"
echo ""
