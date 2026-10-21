"""NLI dataset loaders for pre-training."""

from typing import List, Dict, Any, Optional
from datasets import load_dataset, Dataset
import logging

logger = logging.getLogger(__name__)


def load_snli(
    split: str = "train",
    max_samples: Optional[int] = None,
    sample_ratio: float = 1.0,
) -> List[Dict[str, Any]]:
    """Load SNLI dataset and convert to entailment format.
    
    Args:
        split: Dataset split ('train', 'validation', 'test')
        max_samples: Maximum samples to load
        sample_ratio: Fraction of dataset to use (e.g., 0.1 for 10%)
    
    Returns:
        List of examples with 'premise', 'hypothesis', 'label' keys
    """
    try:
        dataset = load_dataset("snli", split=split)
    except Exception as e:
        logger.error(f"Failed to load SNLI: {e}")
        return []
    
    # Filter out examples with -1 label (invalid)
    dataset = dataset.filter(lambda x: x["label"] != -1)
    
    # Sample if needed
    if sample_ratio < 1.0:
        dataset = dataset.shuffle(seed=42).select(
            range(int(len(dataset) * sample_ratio))
        )
    
    if max_samples:
        dataset = dataset.select(range(min(max_samples, len(dataset))))
    
    # Convert to our format
    examples = []
    label_map = {0: 0, 1: 1, 2: 1}  # 0=entailment, 1=neutral, 2=contradiction -> Binary: 0=entails, 1=not entails
    
    for ex in dataset:
        examples.append({
            "premise": ex["premise"],
            "hypothesis": ex["hypothesis"],
            "label": label_map.get(ex["label"], 1),  # Treat non-entailment as 1
        })
    
    logger.info(f"Loaded {len(examples)} SNLI examples from {split}")
    return examples


def load_mnli(
    split: str = "train",
    max_samples: Optional[int] = None,
    sample_ratio: float = 1.0,
) -> List[Dict[str, Any]]:
    """Load MultiNLI dataset and convert to entailment format.
    
    Args:
        split: Dataset split ('train', 'validation_matched', 'validation_mismatched')
        max_samples: Maximum samples to load
        sample_ratio: Fraction of dataset to use
    
    Returns:
        List of examples with 'premise', 'hypothesis', 'label' keys
    """
    try:
        dataset = load_dataset("multi_nli", split=split)
    except Exception as e:
        logger.error(f"Failed to load MultiNLI: {e}")
        return []
    
    # Filter out examples with -1 label (invalid)
    dataset = dataset.filter(lambda x: x["label"] != -1)
    
    # Sample if needed
    if sample_ratio < 1.0:
        dataset = dataset.shuffle(seed=42).select(
            range(int(len(dataset) * sample_ratio))
        )
    
    if max_samples:
        dataset = dataset.select(range(min(max_samples, len(dataset))))
    
    # Convert to our format
    examples = []
    label_map = {0: 0, 1: 1, 2: 1}  # 0=entailment, 1=neutral, 2=contradiction
    
    for ex in dataset:
        examples.append({
            "premise": ex["premise"],
            "hypothesis": ex["hypothesis"],
            "label": label_map.get(ex["label"], 1),
        })
    
    logger.info(f"Loaded {len(examples)} MultiNLI examples from {split}")
    return examples


def load_paws_nli(
    split: str = "train",
    max_samples: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Load PAWS (paraphrase identification) - useful for detecting similar vs different.
    
    Args:
        split: Dataset split
        max_samples: Maximum samples to load
    
    Returns:
        List of examples with 'premise', 'hypothesis', 'label' keys
    """
    try:
        dataset = load_dataset("paws", "labeled_final", split=split)
    except Exception as e:
        logger.error(f"Failed to load PAWS: {e}")
        return []
    
    if max_samples:
        dataset = dataset.select(range(min(max_samples, len(dataset))))
    
    # In PAWS, label 1 means paraphrase (similar), 0 means not paraphrase
    # For hallucination detection: similar text = likely not hallucinated
    examples = []
    for ex in dataset:
        # PAWS uses 'label' field directly (0 or 1)
        examples.append({
            "premise": ex["sentence1"],
            "hypothesis": ex["sentence2"],
            "label": 0 if ex["label"] == 1 else 1,  # Flip: 1 (paraphrase) → 0 (entails)
        })
    
    logger.info(f"Loaded {len(examples)} PAWS examples from {split}")
    return examples


def combine_nli_datasets(
    use_snli: bool = True,
    use_mnli: bool = True,
    use_paws: bool = False,
    snli_ratio: float = 1.0,
    mnli_ratio: float = 1.0,
    snli_max: Optional[int] = None,
    mnli_max: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Combine multiple NLI datasets for stronger pre-training.
    
    Args:
        use_snli: Include SNLI dataset
        use_mnli: Include MultiNLI dataset
        use_paws: Include PAWS dataset
        snli_ratio: Fraction of SNLI to use
        mnli_ratio: Fraction of MultiNLI to use
        snli_max: Max SNLI samples
        mnli_max: Max MultiNLI samples
    
    Returns:
        Combined list of examples
    """
    all_examples = []
    
    if use_snli:
        snli_examples = load_snli(
            split="train",
            sample_ratio=snli_ratio,
            max_samples=snli_max,
        )
        all_examples.extend(snli_examples)
    
    if use_mnli:
        mnli_examples = load_mnli(
            split="train",
            sample_ratio=mnli_ratio,
            max_samples=mnli_max,
        )
        all_examples.extend(mnli_examples)
    
    if use_paws:
        paws_examples = load_paws_nli(
            split="train",
            max_samples=None,
        )
        all_examples.extend(paws_examples)
    
    logger.info(f"Combined {len(all_examples)} total NLI examples")
    return all_examples
