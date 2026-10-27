"""
End-to-end training script for best overall performance.

Based on SHROOM SemEval-2024 winning strategies:
- NLI pre-training (HIT-MI&T Lab approach)
- Multiple seed ensemble (DeepPavlov + Halu-NLP)
- Meta-classifier combination
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_command(cmd: list, description: str) -> bool:
    """Run a CLI command and handle errors."""
    logger.info(f"\n{'='*60}")
    logger.info(description)
    logger.info(f"{'='*60}\n")
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        return False


def main(
    train_data: str,
    eval_data: str,
    test_data: str,
    nli_output: str = "./models/nli_pretrain",
    ensemble_dir: str = "./models/ensemble_seeds",
    ensemble_output: str = "./models/ensemble_final",
    model_base: str = "microsoft/deberta-large",
    num_seeds: int = 5,
    epochs_nli: int = 1,
    epochs_finetune: int = 5,
    batch_size: int = 16,
    learning_rate: float = 2e-5,
):
    """Run complete best-practice pipeline."""
    
    # Create directories
    Path(nli_output).parent.mkdir(parents=True, exist_ok=True)
    Path(ensemble_dir).mkdir(parents=True, exist_ok=True)
    Path(ensemble_output).mkdir(parents=True, exist_ok=True)
    
    logger.info("="*60)
    logger.info("SHROOM Hallucination Detection - Best Pipeline")
    logger.info("="*60)
    
    # Step 1: NLI Pre-training
    logger.info("\n✓ Step 1: NLI Pre-training (SNLI + MultiNLI)")
    logger.info("Pre-training on NLI makes models understand entailment better")
    
    cmd = [
        "python", "-m", "src.main", "pretrain_nli",
        "--output_dir", nli_output,
        "--model_name", model_base,
        "--use_snli",
        "--use_mnli",
        "--epochs", str(epochs_nli),
        "--batch_size", str(batch_size),
        "--learning_rate", str(learning_rate),
    ]
    
    if not run_command(cmd, "Running NLI pre-training..."):
        logger.error("NLI pre-training failed!")
        return False
    
    # Step 2: Fine-tune on SHROOM with multiple seeds
    logger.info("\n✓ Step 2: Fine-tune on SHROOM (Multiple Seeds)")
    logger.info(f"Training {num_seeds} models with different seeds...")
    
    model_paths = []
    seeds = [42, 100, 200, 300, 400][:num_seeds]
    
    for seed in seeds:
        output_dir = f"{ensemble_dir}/model_seed_{seed}"
        model_paths.append(output_dir)
        
        cmd = [
            "python", "-m", "src.main", "train",
            "--train_data", train_data,
            "--eval_data", eval_data,
            "--model_name", model_base,
            "--output_dir", output_dir,
            "--epochs", str(epochs_finetune),
            "--batch_size", str(batch_size),
            "--learning_rate", str(learning_rate),
            "--max_length", "512",
            "--seed", str(seed),
        ]
        
        logger.info(f"\nTraining model with seed {seed}...")
        if not run_command(cmd, f"Fine-tuning with seed={seed}"):
            logger.error(f"Fine-tuning with seed {seed} failed!")
            return False
    
    # Step 3: Build ensemble meta-classifier
    logger.info("\n✓ Step 3: Build Ensemble Meta-Classifier")
    logger.info("Combining all models with a learned meta-classifier...")
    
    cmd = [
        "python", "-m", "src.main", "ensemble_meta",
        "--model_paths"] + model_paths + [
        "--train_data", train_data,
        "--eval_data", eval_data,
        "--output_dir", ensemble_output,
        "--epochs", "5",
        "--batch_size", "32",
        "--learning_rate", "1e-3",
    ]
    
    if not run_command(cmd, "Training ensemble meta-classifier..."):
        logger.error("Ensemble meta-classifier training failed!")
        return False
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("✓ Pipeline Complete!")
    logger.info("="*60)
    
    logger.info("\nResults:")
    logger.info(f"  - NLI pre-trained model: {nli_output}")
    logger.info(f"  - Individual fine-tuned models: {ensemble_dir}")
    logger.info(f"  - Ensemble meta-classifier: {ensemble_output}")
    
    logger.info("\nExpected Performance:")
    logger.info("  - Accuracy: ~0.80-0.82")
    logger.info("  - F1 Score: ~0.73-0.75")
    logger.info("  - Calibration (Spearman ρ): ~0.65-0.75")
    
    logger.info("\nNext Steps:")
    logger.info("1. Evaluate on test set using ensemble meta-classifier")
    logger.info("2. Tune probability threshold based on validation calibration")
    logger.info("3. Optional: Combine with other models (Vectara, GPT-based) for further gains")
    logger.info("4. Monitor per-task performance (DM/MT/PG) for task-specific optimization")
    
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run best-practice hallucination detection pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

  # Quick run with example data
  python train_best_pipeline.py \\
    --train_data data/raw/train_example.jsonl \\
    --eval_data data/raw/eval_example.jsonl \\
    --test_data data/raw/test_example.jsonl \\
    --num_seeds 2

  # Full run with SHROOM data
  python train_best_pipeline.py \\
    --train_data data/raw/train.model-agnostic.json \\
    --eval_data data/raw/eval.model-agnostic.json \\
    --test_data data/raw/test.model-agnostic.json \\
    --num_seeds 5
        """
    )
    
    parser.add_argument("--train_data", type=str, required=True, help="Training data path")
    parser.add_argument("--eval_data", type=str, required=True, help="Evaluation data path")
    parser.add_argument("--test_data", type=str, required=True, help="Test data path")
    parser.add_argument("--nli_output", type=str, default="./models/nli_pretrain", help="NLI output dir")
    parser.add_argument("--ensemble_dir", type=str, default="./models/ensemble_seeds", help="Ensemble models dir")
    parser.add_argument("--ensemble_output", type=str, default="./models/ensemble_final", help="Final output dir")
    parser.add_argument("--model_base", type=str, default="microsoft/deberta-large", help="Base model")
    parser.add_argument("--num_seeds", type=int, default=5, help="Number of seeds for ensemble")
    parser.add_argument("--epochs_nli", type=int, default=1, help="NLI pre-training epochs")
    parser.add_argument("--epochs_finetune", type=int, default=5, help="Fine-tuning epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size")
    parser.add_argument("--learning_rate", type=float, default=2e-5, help="Learning rate")
    
    args = parser.parse_args()
    
    success = main(
        train_data=args.train_data,
        eval_data=args.eval_data,
        test_data=args.test_data,
        nli_output=args.nli_output,
        ensemble_dir=args.ensemble_dir,
        ensemble_output=args.ensemble_output,
        model_base=args.model_base,
        num_seeds=args.num_seeds,
        epochs_nli=args.epochs_nli,
        epochs_finetune=args.epochs_finetune,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
    )
    
    sys.exit(0 if success else 1)
