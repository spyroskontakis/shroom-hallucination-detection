"""Main entry point for the project."""

import argparse
import sys
import torch
from typing import Optional

from src.training.evaluate import evaluate
from src.training.pseudo_label import generate_pseudo_labels
from src.training.train import train
from src.training.ensemble_meta_train import train_meta_classifier
from src.data.nli_loader import combine_nli_datasets


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Hallucination Detection Using Entailment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

  # Train model
  python -m src.main train --train_data data/raw/train.jsonl \\
    --eval_data data/raw/eval.jsonl --output_dir ./output

  # Evaluate model
  python -m src.main evaluate --model_path ./output --data_path data/raw/test.jsonl

  # Generate pseudo-labels
  python -m src.main pseudo_label --model_path ./output \\
    --data_path data/raw/unlabeled.jsonl --output_path data/pseudo/labeled.jsonl
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Train command
    train_parser = subparsers.add_parser("train", help="Train model")
    train_parser.add_argument("--config", type=str, default=None, help="Path to config YAML")
    train_parser.add_argument("--train_data", type=str, required=True, help="Training data JSONL")
    train_parser.add_argument("--eval_data", type=str, default=None, help="Evaluation data JSONL")
    train_parser.add_argument("--model_name", type=str, default="microsoft/deberta-large", help="Model name")
    train_parser.add_argument("--output_dir", type=str, default="./output", help="Output directory")
    train_parser.add_argument("--epochs", type=int, default=3, help="Epochs")
    train_parser.add_argument("--batch_size", type=int, default=8, help="Batch size")
    train_parser.add_argument("--learning_rate", type=float, default=2e-5, help="Learning rate")
    train_parser.add_argument("--max_length", type=int, default=512, help="Max sequence length")
    train_parser.add_argument("--task_type", type=str, default=None, help="Task type (DM/MT/PG)")
    train_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    # Evaluate command
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate model")
    eval_parser.add_argument("--model_path", type=str, required=True, help="Model checkpoint path")
    eval_parser.add_argument("--data_path", type=str, required=True, help="Data JSONL file")
    eval_parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    eval_parser.add_argument("--max_length", type=int, default=512, help="Max sequence length")
    eval_parser.add_argument("--model_name", type=str, default=None, help="Fallback base model name")
    eval_parser.add_argument("--task_type", type=str, default=None, help="Task type (DM/MT/PG)")
    eval_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    # Pseudo-label command
    pseudo_parser = subparsers.add_parser("pseudo_label", help="Generate pseudo-labels")
    pseudo_parser.add_argument("--model_path", type=str, required=True, help="Model checkpoint path")
    pseudo_parser.add_argument("--data_path", type=str, required=True, help="Input data JSONL file")
    pseudo_parser.add_argument("--output_path", type=str, required=True, help="Output JSONL file")
    pseudo_parser.add_argument("--confidence_threshold", type=float, default=0.8, help="Confidence threshold")
    pseudo_parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    pseudo_parser.add_argument("--max_length", type=int, default=512, help="Max sequence length")
    pseudo_parser.add_argument("--model_name", type=str, default=None, help="Fallback base model name")
    pseudo_parser.add_argument("--task_type", type=str, default=None, help="Task type (DM/MT/PG)")
    pseudo_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    # NLI pre-training command
    nli_parser = subparsers.add_parser("pretrain_nli", help="Pre-train on NLI data (SNLI/MultiNLI)")
    nli_parser.add_argument("--output_dir", type=str, required=True, help="Output directory")
    nli_parser.add_argument("--model_name", type=str, default="microsoft/deberta-large", help="Base model")
    nli_parser.add_argument("--use_snli", action="store_true", default=True, help="Use SNLI")
    nli_parser.add_argument("--use_mnli", action="store_true", default=True, help="Use MultiNLI")
    nli_parser.add_argument("--use_paws", action="store_true", default=False, help="Use PAWS")
    nli_parser.add_argument("--snli_ratio", type=float, default=1.0, help="SNLI fraction to use")
    nli_parser.add_argument("--mnli_ratio", type=float, default=1.0, help="MultiNLI fraction to use")
    nli_parser.add_argument("--snli_max", type=int, default=None, help="Max SNLI samples")
    nli_parser.add_argument("--mnli_max", type=int, default=None, help="Max MultiNLI samples")
    nli_parser.add_argument("--epochs", type=int, default=1, help="Training epochs")
    nli_parser.add_argument("--batch_size", type=int, default=16, help="Batch size")
    nli_parser.add_argument("--learning_rate", type=float, default=2e-5, help="Learning rate")
    nli_parser.add_argument("--max_length", type=int, default=512, help="Max sequence length")
    nli_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    # Ensemble meta-classifier training command
    ensemble_parser = subparsers.add_parser("ensemble_meta", help="Train ensemble meta-classifier")
    ensemble_parser.add_argument("--model_paths", type=str, nargs="+", required=True, help="Base model paths")
    ensemble_parser.add_argument("--train_data", type=str, required=True, help="Training data JSONL")
    ensemble_parser.add_argument("--eval_data", type=str, default=None, help="Evaluation data JSONL")
    ensemble_parser.add_argument("--output_dir", type=str, default="./ensemble_output", help="Output dir")
    ensemble_parser.add_argument("--epochs", type=int, default=5, help="Epochs")
    ensemble_parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    ensemble_parser.add_argument("--learning_rate", type=float, default=1e-3, help="Learning rate")
    ensemble_parser.add_argument("--max_length", type=int, default=512, help="Max sequence length")
    ensemble_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "train":
        train(
            config_path=args.config,
            train_data=args.train_data,
            eval_data=args.eval_data,
            model_name=args.model_name,
            output_dir=args.output_dir,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            max_length=args.max_length,
            seed=args.seed,
            task_type=args.task_type,
        )
    
    elif args.command == "evaluate":
        metrics = evaluate(
            model_path=args.model_path,
            data_path=args.data_path,
            batch_size=args.batch_size,
            max_length=args.max_length,
            device="cuda" if torch.cuda.is_available() else "cpu",
            model_name=args.model_name,
            task_type=args.task_type,
            seed=args.seed,
        )
        print("\nResults:", metrics)
    
    elif args.command == "pseudo_label":
        generate_pseudo_labels(
            model_path=args.model_path,
            data_path=args.data_path,
            output_path=args.output_path,
            confidence_threshold=args.confidence_threshold,
            batch_size=args.batch_size,
            max_length=args.max_length,
            model_name=args.model_name,
            task_type=args.task_type,
            seed=args.seed,
        )
    
    elif args.command == "pretrain_nli":
        import json
        from pathlib import Path
        from transformers import AutoTokenizer, TrainingArguments, Trainer, DataCollatorWithPadding
        from datasets import Dataset
        from src.models.entailment_model import EntailmentModel
        
        # Load NLI data
        examples = combine_nli_datasets(
            use_snli=args.use_snli,
            use_mnli=args.use_mnli,
            use_paws=args.use_paws,
            snli_ratio=args.snli_ratio,
            mnli_ratio=args.mnli_ratio,
            snli_max=args.snli_max,
            mnli_max=args.mnli_max,
        )
        
        # Create dataset
        dataset = Dataset.from_dict({
            'premise': [ex['premise'] for ex in examples],
            'hypothesis': [ex['hypothesis'] for ex in examples],
            'label': [ex['label'] for ex in examples],
        })
        
        # Tokenize
        tokenizer = AutoTokenizer.from_pretrained(args.model_name)
        
        def tokenize_fn(batch):
            encodings = tokenizer(
                batch['premise'],
                batch['hypothesis'],
                truncation=True,
                max_length=args.max_length,
            )
            encodings['labels'] = batch['label']
            return encodings
        
        dataset = dataset.map(tokenize_fn, batched=True, remove_columns=['premise', 'hypothesis'])
        
        # Train
        model = EntailmentModel(model_name=args.model_name, num_labels=2)
        
        training_args = TrainingArguments(
            output_dir=args.output_dir,
            num_train_epochs=args.epochs,
            per_device_train_batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            warmup_steps=500,
            weight_decay=0.01,
            logging_steps=100,
            seed=args.seed,
        )
        
        data_collator = DataCollatorWithPadding(tokenizer=tokenizer, return_tensors="pt")
        
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=dataset,
            data_collator=data_collator,
        )
        
        trainer.train()
        trainer.save_model(args.output_dir)
        
        # Save metadata
        metadata_path = Path(args.output_dir) / "model_metadata.json"
        metadata_path.write_text(
            json.dumps(
                {"model_name": args.model_name, "max_length": args.max_length, "pretrained_on": "NLI"},
                indent=2,
            ),
            encoding="utf-8",
        )
        
        print(f"NLI pre-training complete! Model saved to {args.output_dir}")
    
    elif args.command == "ensemble_meta":
        train_meta_classifier(
            model_paths=args.model_paths,
            train_data=args.train_data,
            eval_data=args.eval_data,
            output_dir=args.output_dir,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            max_length=args.max_length,
            seed=args.seed,
            device="cuda" if torch.cuda.is_available() else "cpu",
        )


if __name__ == "__main__":
    main()
