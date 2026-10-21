"""Training script using HuggingFace Trainer."""

import argparse
import json
from pathlib import Path
from typing import Dict, Optional
from importlib.util import find_spec

import numpy as np
import torch
import yaml
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)

from src.data.loader import load_data
from src.data.preprocess import preprocess_shroom
from src.models.entailment_model import EntailmentModel
from src.utils.metrics import compute_metrics
from src.utils.seed import set_seed


def get_reporting_integrations() -> list[str]:
    """Enable TensorBoard logging only when the dependency is installed."""
    return ["tensorboard"] if find_spec("tensorboard") is not None else []


def load_config(config_path: str) -> Dict:
    """Load YAML config file.
    
    Args:
        config_path: Path to YAML config.
    
    Returns:
        Configuration dictionary.
    """
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def create_dataset(
    data_path: str,
    tokenizer,
    max_length: int = 512,
    task_type: Optional[str] = None,
) -> Dataset:
    """Create HuggingFace Dataset.
    
    Args:
        data_path: Path to JSONL file.
        tokenizer: Tokenizer instance.
        max_length: Maximum sequence length.
        task_type: Task type for preprocessing.
    
    Returns:
        HuggingFace Dataset.
    """
    # Load and preprocess data
    examples = load_data(data_path)
    examples = preprocess_shroom(examples, task_type=task_type)
    
    # Create dataset
    dataset = Dataset.from_dict({
        'premise': [ex['premise'] for ex in examples],
        'hypothesis': [ex['hypothesis'] for ex in examples],
        'label': [ex['label'] for ex in examples],
    })
    
    # Tokenize
    def tokenize_fn(batch):
        encodings = tokenizer(
            batch['premise'],
            batch['hypothesis'],
            truncation=True,
            max_length=max_length,
        )
        encodings['labels'] = batch['label']
        return encodings
    
    dataset = dataset.map(tokenize_fn, batched=True, remove_columns=['premise', 'hypothesis'])
    
    return dataset


def compute_metrics_fn(eval_pred):
    """Compute metrics for Trainer.
    
    Args:
        eval_pred: EvalPrediction object with predictions and label_ids.
    
    Returns:
        Dictionary with metrics.
    """
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    
    metrics = compute_metrics(predictions, labels)
    return metrics


def train(
    config_path: Optional[str] = None,
    train_data: Optional[str] = None,
    eval_data: Optional[str] = None,
    model_name: str = "microsoft/deberta-large",
    output_dir: str = "./output",
    epochs: int = 3,
    batch_size: int = 8,
    learning_rate: float = 2e-5,
    max_length: int = 512,
    seed: int = 42,
    task_type: Optional[str] = None,
) -> None:
    """Train model.
    
    Args:
        config_path: Path to YAML config (overrides other args if provided).
        train_data: Path to training data JSONL.
        eval_data: Path to evaluation data JSONL.
        model_name: HuggingFace model name.
        output_dir: Output directory for checkpoints.
        epochs: Number of training epochs.
        batch_size: Batch size.
        learning_rate: Learning rate.
        max_length: Maximum sequence length.
        seed: Random seed.
        task_type: Task type for preprocessing.
    """
    set_seed(seed)
    
    # Load config if provided
    if config_path:
        config = load_config(config_path)
        train_data = config.get('train_data', train_data)
        eval_data = config.get('eval_data', eval_data)
        model_name = config.get('model_name', model_name)
        output_dir = config.get('output_dir', output_dir)
        epochs = config.get('epochs', epochs)
        batch_size = config.get('batch_size', batch_size)
        learning_rate = config.get('learning_rate', learning_rate)
        max_length = config.get('max_length', max_length)
        task_type = config.get('task_type', task_type)
    
    assert train_data is not None, "train_data required"
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # Load tokenizer and model
    print(f"Loading model: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = EntailmentModel(model_name=model_name, num_labels=2)
    
    # Create datasets
    print(f"Loading training data from {train_data}")
    train_dataset = create_dataset(train_data, tokenizer, max_length, task_type)
    
    eval_dataset = None
    if eval_data:
        print(f"Loading evaluation data from {eval_data}")
        eval_dataset = create_dataset(eval_data, tokenizer, max_length, task_type)
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        learning_rate=learning_rate,
        warmup_steps=500,
        weight_decay=0.01,
        logging_steps=100,
        save_steps=500,
        eval_strategy="steps" if eval_data else "no",
        eval_steps=500 if eval_data else None,
        load_best_model_at_end=True if eval_data else False,
        metric_for_best_model="f1" if eval_data else None,
        seed=seed,
        report_to=get_reporting_integrations(),
        dataloader_pin_memory=device == "cuda",
    )
    
    # Trainer
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer, return_tensors="pt")

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
        compute_metrics=compute_metrics_fn if eval_data else None,
    )
    
    # Train
    print("Starting training...")
    trainer.train()
    
    # Save model
    print(f"Saving model to {output_dir}")
    trainer.save_model(output_dir)

    metadata_path = Path(output_dir) / "model_metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "model_name": model_name,
                "max_length": max_length,
                "task_type": task_type,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    
    print("Training complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train hallucination detection model")
    parser.add_argument("--config", type=str, default=None, help="Path to config YAML")
    parser.add_argument("--train_data", type=str, default=None, help="Path to training data")
    parser.add_argument("--eval_data", type=str, default=None, help="Path to evaluation data")
    parser.add_argument("--model_name", type=str, default="microsoft/deberta-large", help="Model name")
    parser.add_argument("--output_dir", type=str, default="./output", help="Output directory")
    parser.add_argument("--epochs", type=int, default=3, help="Number of epochs")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size")
    parser.add_argument("--learning_rate", type=float, default=2e-5, help="Learning rate")
    parser.add_argument("--max_length", type=int, default=512, help="Max length")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--task_type", type=str, default=None, help="Task type (DM/MT/PG)")
    
    args = parser.parse_args()
    
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
