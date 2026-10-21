"""Evaluation script."""

import argparse
from typing import Dict, Optional

import numpy as np
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from src.data.loader import load_data
from src.data.preprocess import preprocess_shroom
from src.models.entailment_model import (
    infer_model_name,
    load_checkpoint_weights,
    load_model_and_tokenizer,
)
from src.utils.metrics import compute_correlation, compute_metrics
from src.utils.seed import set_seed


def _extract_logits(model_output: torch.Tensor) -> torch.Tensor:
    """Normalize model outputs to a logits tensor."""
    return model_output.logits if hasattr(model_output, "logits") else model_output


def evaluate(
    model_path: str,
    data_path: str,
    batch_size: int = 32,
    max_length: int = 512,
    device: str = "cuda" if torch.cuda.is_available() else "cpu",
    model_name: Optional[str] = None,
    task_type: Optional[str] = None,
    seed: int = 42,
) -> Dict[str, float]:
    """Evaluate model on dataset.
    
    Args:
        model_path: Path to model checkpoint (directory from trainer).
        data_path: Path to JSONL file.
        batch_size: Batch size.
        max_length: Maximum sequence length.
        device: Device to use ('cuda' or 'cpu').
        model_name: Optional fallback base model name.
        task_type: Task type for preprocessing ('DM', 'MT', 'PG').
        seed: Random seed.
    
    Returns:
        Dictionary with evaluation metrics.
    """
    set_seed(seed)
    
    # Load data
    print(f"Loading data from {data_path}...")
    examples = load_data(data_path)
    examples = preprocess_shroom(examples, task_type=task_type)
    
    # Load model and tokenizer
    print(f"Loading model from {model_path}...")
    resolved_model_name = infer_model_name(model_path, fallback=model_name or "microsoft/deberta-large")
    print(f"Using base model: {resolved_model_name}")
    model, tokenizer = load_model_and_tokenizer(model_name=resolved_model_name)
    load_checkpoint_weights(model, model_path, device)
    
    model.to(device)
    model.eval()
    
    # Prepare data
    premises = [ex['premise'] for ex in examples]
    hypotheses = [ex['hypothesis'] for ex in examples]
    labels = np.array([ex['label'] for ex in examples])
    
    # Tokenize
    print("Tokenizing...")
    encodings = tokenizer(
        premises,
        hypotheses,
        truncation=True,
        padding=True,
        max_length=max_length,
        return_tensors="pt",
    )
    
    # Create dataset
    from torch.utils.data import Dataset
    
    class SimpleDataset(Dataset):
        def __init__(self, encodings):
            self.encodings = encodings
        
        def __len__(self):
            return len(self.encodings['input_ids'])
        
        def __getitem__(self, idx):
            return {k: v[idx] for k, v in self.encodings.items()}
    
    dataset = SimpleDataset(encodings)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    
    # Evaluate
    print("Evaluating...")
    all_logits = []
    all_probs = []
    
    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Evaluating"):
            batch = {k: v.to(device) for k, v in batch.items()}
            logits = _extract_logits(model(**batch))
            all_logits.append(logits.cpu().numpy())
            probs = torch.softmax(logits, dim=-1)[:, 1].cpu().numpy()
            all_probs.append(probs)
    
    logits_array = np.concatenate(all_logits, axis=0)
    probs_array = np.concatenate(all_probs, axis=0)
    predictions = np.argmax(logits_array, axis=1)
    
    # Compute metrics
    metrics = compute_metrics(predictions, labels)
    correlation, p_value = compute_correlation(probs_array, labels)
    
    metrics['spearman_correlation'] = correlation
    metrics['spearman_p_value'] = p_value
    
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate model")
    parser.add_argument("--model_path", type=str, required=True, help="Path to model checkpoint")
    parser.add_argument("--data_path", type=str, required=True, help="Path to JSONL file")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--max_length", type=int, default=512, help="Maximum sequence length")
    parser.add_argument("--model_name", type=str, default=None, help="Fallback base model name")
    parser.add_argument("--task_type", type=str, default=None, help="Task type (DM/MT/PG)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    metrics = evaluate(
        model_path=args.model_path,
        data_path=args.data_path,
        batch_size=args.batch_size,
        max_length=args.max_length,
        model_name=args.model_name,
        task_type=args.task_type,
        seed=args.seed,
    )
    
    print("\n" + "="*50)
    print("EVALUATION RESULTS")
    print("="*50)
    for key, value in metrics.items():
        print(f"{key}: {value:.4f}")
