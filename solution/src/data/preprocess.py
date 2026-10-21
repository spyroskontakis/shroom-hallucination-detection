"""Preprocessing utilities for SHROOM dataset."""

from typing import Any, Dict, List, Optional

import pandas as pd


def preprocess_shroom(
    examples: List[Dict[str, Any]],
    task_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Preprocess SHROOM examples into standard format.
    
    Maps SHROOM fields into:
    - premise: tgt (for DM/MT) or src (for PG)
    - hypothesis: hyp
    - label: binary (1 for Hallucination, 0 for Not hallucination)
    
    Args:
        examples: List of SHROOM examples.
        task_type: Task type ('DM', 'MT', 'PG'). If None, inferred from data.
    
    Returns:
        List of preprocessed examples with 'premise', 'hypothesis', 'label' keys.
    """
    processed = []
    
    for example in examples:
        # Infer task type if not provided
        if task_type is None:
            inferred_task = _infer_task_type(example)
        else:
            inferred_task = task_type
        
        # Extract premise based on task type
        if inferred_task in ['DM', 'MT']:
            premise = example.get('tgt', '')
        elif inferred_task == 'PG':
            premise = example.get('src', '')
        else:
            # Fallback: try tgt first, then src
            premise = example.get('tgt', example.get('src', ''))
        
        # Extract hypothesis and label
        hypothesis = example.get('hyp', '')
        
        # Convert label to binary: 1 for hallucination, 0 for not hallucination
        label_str = example.get('label', '')
        label = 1 if label_str.lower() in ['hallucinated', 'hallucination', 'hallucinated'] else 0
        
        processed.append({
            'premise': premise,
            'hypothesis': hypothesis,
            'label': label,
            'task': inferred_task,
        })
    
    return processed


def _infer_task_type(example: Dict[str, Any]) -> str:
    """Infer task type from example fields.
    
    Args:
        example: SHROOM example.
    
    Returns:
        Task type string ('DM', 'MT', or 'PG').
    """
    if 'task' in example:
        return example['task']
    
    # Heuristic: check which fields are present
    if 'tgt' in example:
        return 'DM' if 'document' in example else 'MT'
    elif 'src' in example:
        return 'PG'
    
    return 'DM'  # Default fallback


def create_examples_dataframe(
    examples: List[Dict[str, Any]]
) -> pd.DataFrame:
    """Create pandas DataFrame from preprocessed examples.
    
    Args:
        examples: List of preprocessed examples.
    
    Returns:
        DataFrame with columns: premise, hypothesis, label, task
    """
    return pd.DataFrame(examples)
