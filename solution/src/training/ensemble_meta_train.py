"""Ensemble meta-classifier training."""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

import numpy as np
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.utils.data import DataLoader, TensorDataset
from datasets import Dataset
from transformers import DataCollatorWithPadding

from src.data.loader import load_data
from src.data.preprocess import preprocess_shroom
from src.models.entailment_model import load_model_and_tokenizer, infer_model_name
from src.utils.metrics import compute_metrics
from src.utils.seed import set_seed

logger = logging.getLogger(__name__)


class EnsembleMetaClassifier(nn.Module):
    """Meta-classifier that combines predictions from multiple base models."""
    
    def __init__(self, num_models: int, hidden_size: int = 128, dropout: float = 0.2):
        """Initialize meta-classifier.
        
        Args:
            num_models: Number of base models in ensemble
            hidden_size: Hidden layer size
            dropout: Dropout probability
        """
        super().__init__()
        input_size = num_models * 2  # 2 logits per model
        
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(hidden_size, 2)
        self.relu = nn.ReLU()
    
    def forward(self, ensemble_logits: torch.Tensor) -> torch.Tensor:
        """Forward pass.
        
        Args:
            ensemble_logits: Concatenated logits from K models [batch_size, 2*K]
        
        Returns:
            Final logits [batch_size, 2]
        """
        x = self.relu(self.fc1(ensemble_logits))
        x = self.dropout(x)
        logits = self.fc2(x)
        return logits


def get_ensemble_logits(
    model_paths: List[str],
    data_path: str,
    tokenizer,
    max_length: int = 512,
    batch_size: int = 32,
    device: str = "cuda",
) -> tuple[np.ndarray, np.ndarray]:
    """Get predictions from all models in ensemble.
    
    Args:
        model_paths: Paths to trained model checkpoints
        data_path: Path to data JSONL file
        tokenizer: Tokenizer for encoding
        max_length: Maximum sequence length
        batch_size: Batch size for inference
        device: Device to run on
    
    Returns:
        Tuple of (ensemble_logits, labels) where ensemble_logits shape is [N, 2*K]
    """
    # Load and preprocess data
    examples = load_data(data_path)
    examples = preprocess_shroom(examples)
    
    dataset = Dataset.from_dict({
        "premise": [ex["premise"] for ex in examples],
        "hypothesis": [ex["hypothesis"] for ex in examples],
        "label": [ex["label"] for ex in examples],
    })
    
    def tokenize_fn(batch):
        encodings = tokenizer(
            batch["premise"],
            batch["hypothesis"],
            truncation=True,
            max_length=max_length,
        )
        encodings["labels"] = batch["label"]
        return encodings
    
    dataset = dataset.map(tokenize_fn, batched=True, remove_columns=["premise", "hypothesis"])
    dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels", "token_type_ids"])
    
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=DataCollatorWithPadding(tokenizer=tokenizer, return_tensors="pt"),
    )
    
    # Get labels
    all_labels = torch.tensor([ex["label"] for ex in examples])
    
    # Load all models and get predictions
    all_logits = []
    
    for model_path in model_paths:
        logger.info(f"Loading model from {model_path}")
        
        model_name = infer_model_name(model_path)
        model, _ = load_model_and_tokenizer(model_name)
        
        # Load weights
        from src.models.entailment_model import load_checkpoint_weights
        load_checkpoint_weights(model, model_path, device)
        model.to(device)
        model.eval()
        
        model_logits = []
        with torch.no_grad():
            for batch in dataloader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                token_type_ids = batch.get("token_type_ids", None)
                if token_type_ids is not None:
                    token_type_ids = token_type_ids.to(device)
                
                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    token_type_ids=token_type_ids,
                )
                model_logits.append(outputs.logits.cpu().numpy())
        
        model_logits = np.vstack(model_logits)
        all_logits.append(model_logits)
        logger.info(f"  Shape: {model_logits.shape}")
    
    # Concatenate logits from all models
    ensemble_logits = np.hstack(all_logits)  # [N, 2*K]
    labels = all_labels.numpy()
    
    logger.info(f"Ensemble logits shape: {ensemble_logits.shape}")
    logger.info(f"Labels shape: {labels.shape}")
    
    return ensemble_logits, labels


def train_meta_classifier(
    model_paths: List[str],
    train_data: str,
    eval_data: Optional[str] = None,
    output_dir: str = "./ensemble_output",
    epochs: int = 5,
    batch_size: int = 32,
    learning_rate: float = 1e-3,
    max_length: int = 512,
    seed: int = 42,
    device: str = "cuda",
) -> None:
    """Train meta-classifier on top of ensemble predictions.
    
    Args:
        model_paths: Paths to trained base models
        train_data: Path to training data JSONL
        eval_data: Path to evaluation data JSONL (optional)
        output_dir: Output directory for meta-classifier
        epochs: Number of training epochs
        batch_size: Batch size
        learning_rate: Learning rate
        max_length: Max sequence length
        seed: Random seed
        device: Device to use
    """
    set_seed(seed)
    
    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load tokenizer from first model
    model_name = infer_model_name(model_paths[0])
    _, tokenizer = load_model_and_tokenizer(model_name)
    
    logger.info(f"Getting ensemble logits for {len(train_data.split())} training samples...")
    train_logits, train_labels = get_ensemble_logits(
        model_paths, train_data, tokenizer, max_length, batch_size, device
    )
    
    eval_logits = None
    eval_labels = None
    if eval_data:
        logger.info(f"Getting ensemble logits for evaluation...")
        eval_logits, eval_labels = get_ensemble_logits(
            model_paths, eval_data, tokenizer, max_length, batch_size, device
        )
    
    # Create meta-classifier
    num_models = len(model_paths)
    meta_model = EnsembleMetaClassifier(
        num_models=num_models,
        hidden_size=128,
        dropout=0.2,
    ).to(device)
    
    # Create datasets
    train_dataset = TensorDataset(
        torch.FloatTensor(train_logits),
        torch.LongTensor(train_labels),
    )
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    
    if eval_logits is not None:
        eval_dataset = TensorDataset(
            torch.FloatTensor(eval_logits),
            torch.LongTensor(eval_labels),
        )
        eval_loader = DataLoader(eval_dataset, batch_size=batch_size, shuffle=False)
    
    # Training setup
    optimizer = AdamW(meta_model.parameters(), lr=learning_rate)
    loss_fn = nn.CrossEntropyLoss()
    
    best_eval_f1 = 0.0
    
    # Training loop
    for epoch in range(epochs):
        # Train
        meta_model.train()
        total_loss = 0.0
        for batch_logits, batch_labels in train_loader:
            batch_logits = batch_logits.to(device)
            batch_labels = batch_labels.to(device)
            
            logits = meta_model(batch_logits)
            loss = loss_fn(logits, batch_labels)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        avg_loss = total_loss / len(train_loader)
        logger.info(f"Epoch {epoch+1}/{epochs} - Loss: {avg_loss:.4f}")
        
        # Evaluate
        if eval_logits is not None:
            meta_model.eval()
            all_preds = []
            all_labels_eval = []
            
            with torch.no_grad():
                for batch_logits, batch_labels in eval_loader:
                    batch_logits = batch_logits.to(device)
                    logits = meta_model(batch_logits)
                    preds = torch.argmax(logits, dim=1)
                    
                    all_preds.extend(preds.cpu().numpy())
                    all_labels_eval.extend(batch_labels.numpy())
            
            metrics = compute_metrics((np.array(all_preds), np.array(all_labels_eval)))
            logger.info(f"  Eval - Accuracy: {metrics['accuracy']:.4f}, F1: {metrics['f1']:.4f}")
            
            if metrics["f1"] > best_eval_f1:
                best_eval_f1 = metrics["f1"]
                logger.info(f"  Saving best model (F1: {best_eval_f1:.4f})")
                torch.save(meta_model.state_dict(), output_dir / "meta_model.pt")
    
    # Save final model and config
    torch.save(meta_model.state_dict(), output_dir / "meta_model_final.pt")
    
    config = {
        "num_models": num_models,
        "model_paths": model_paths,
        "hidden_size": 128,
        "dropout": 0.2,
        "best_eval_f1": best_eval_f1,
    }
    
    with open(output_dir / "meta_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Meta-classifier training complete!")
    logger.info(f"Saved to {output_dir}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Train ensemble meta-classifier")
    parser.add_argument("--model_paths", type=str, nargs="+", required=True, help="Base model paths")
    parser.add_argument("--train_data", type=str, required=True, help="Training data path")
    parser.add_argument("--eval_data", type=str, default=None, help="Evaluation data path")
    parser.add_argument("--output_dir", type=str, default="./ensemble_output", help="Output dir")
    parser.add_argument("--epochs", type=int, default=5, help="Epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--learning_rate", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--max_length", type=int, default=512, help="Max length")
    parser.add_argument("--seed", type=int, default=42, help="Seed")
    
    args = parser.parse_args()
    
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
    )
