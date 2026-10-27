"""Generate pseudo-labels using model confidence."""

import argparse
from typing import Optional

import numpy as np
import torch
from tqdm import tqdm

from src.data.loader import load_data, save_jsonl
from src.data.preprocess import preprocess_shroom
from src.models.entailment_model import (
    infer_model_name,
    load_checkpoint_weights,
    load_model_and_tokenizer,
)
from src.utils.seed import set_seed


def _extract_logits(model_output: torch.Tensor) -> torch.Tensor:
    """Normalize model outputs to a logits tensor."""
    return model_output.logits if hasattr(model_output, "logits") else model_output


def generate_pseudo_labels(
    model_path: str,
    data_path: str,
    output_path: str,
    confidence_threshold: float = 0.8,
    batch_size: int = 32,
    max_length: int = 512,
    device: str = "cuda" if torch.cuda.is_available() else "cpu",
    model_name: Optional[str] = None,
    task_type: Optional[str] = None,
    seed: int = 42,
) -> None:
    """Generate pseudo-labels for unlabeled data.
    
    Args:
        model_path: Path to model checkpoint (directory from trainer).
        data_path: Path to input JSONL file.
        output_path: Path to save pseudo-labeled JSONL file.
        confidence_threshold: Confidence threshold for pseudo-labeling.
        batch_size: Batch size.
        max_length: Maximum sequence length.
        device: Device to use ('cuda' or 'cpu').
        model_name: Optional fallback base model name.
        task_type: Task type for preprocessing ('DM', 'MT', 'PG').
        seed: Random seed.
    """
    set_seed(seed)
    
    # Load data
    print(f"Loading data from {data_path}...")
    examples = load_data(data_path)
    examples_preprocessed = preprocess_shroom(examples, task_type=task_type)
    
    # Load model and tokenizer
    print(f"Loading model from {model_path}...")
    resolved_model_name = infer_model_name(model_path, fallback=model_name or "microsoft/deberta-large")
    print(f"Using base model: {resolved_model_name}")
    model, tokenizer = load_model_and_tokenizer(model_name=resolved_model_name)
    load_checkpoint_weights(model, model_path, device)
    
    model.to(device)
    model.eval()
    
    # Prepare data
    premises = [ex['premise'] for ex in examples_preprocessed]
    hypotheses = [ex['hypothesis'] for ex in examples_preprocessed]
    
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
    from torch.utils.data import DataLoader, Dataset
    
    class SimpleDataset(Dataset):
        def __init__(self, encodings):
            self.encodings = encodings
        
        def __len__(self):
            return len(self.encodings['input_ids'])
        
        def __getitem__(self, idx):
            return {k: v[idx] for k, v in self.encodings.items()}
    
    dataset = SimpleDataset(encodings)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    
    # Generate pseudo-labels
    print("Generating pseudo-labels...")
    all_probs = []
    all_preds = []
    all_confidences = []
    
    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Pseudo-labeling"):
            batch = {k: v.to(device) for k, v in batch.items()}
            logits = _extract_logits(model(**batch))
            probs = torch.softmax(logits, dim=-1)
            preds = torch.argmax(logits, dim=-1)
            confidences = torch.max(probs, dim=-1).values
            
            all_probs.append(probs.cpu().numpy())
            all_preds.append(preds.cpu().numpy())
            all_confidences.append(confidences.cpu().numpy())
    
    probs = np.concatenate(all_probs, axis=0)
    preds = np.concatenate(all_preds, axis=0)
    confidences = np.concatenate(all_confidences, axis=0)
    
    # Filter by confidence threshold
    high_conf_mask = confidences >= confidence_threshold
    num_high_conf = np.sum(high_conf_mask)
    
    print(f"\nPseudo-label statistics:")
    print(f"  Total examples: {len(examples)}")
    print(f"  High confidence (>= {confidence_threshold}): {num_high_conf} ({100*num_high_conf/len(examples):.1f}%)")
    print(f"  Hallucinated: {np.sum(preds[high_conf_mask] == 1)}")
    print(f"  Not hallucinated: {np.sum(preds[high_conf_mask] == 0)}")
    
    # Save pseudo-labeled data
    output_examples = []
    for i, (example, pred, conf) in enumerate(zip(examples, preds, confidences)):
        example['pseudo_label'] = int(pred)
        example['pseudo_confidence'] = float(conf)
        example['high_confidence'] = bool(high_conf_mask[i])
        if high_conf_mask[i]:  # Only save high-confidence examples
            output_examples.append(example)
    
    print(f"\nSaving {len(output_examples)} high-confidence examples to {output_path}")
    save_jsonl(output_examples, output_path)
    print("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate pseudo-labels")
    parser.add_argument("--model_path", type=str, required=True, help="Path to model checkpoint")
    parser.add_argument("--data_path", type=str, required=True, help="Path to input JSONL file")
    parser.add_argument("--output_path", type=str, required=True, help="Path to save pseudo-labeled JSONL")
    parser.add_argument("--confidence_threshold", type=float, default=0.8, help="Confidence threshold")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--max_length", type=int, default=512, help="Maximum sequence length")
    parser.add_argument("--model_name", type=str, default=None, help="Fallback base model name")
    parser.add_argument("--task_type", type=str, default=None, help="Task type (DM/MT/PG)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
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
