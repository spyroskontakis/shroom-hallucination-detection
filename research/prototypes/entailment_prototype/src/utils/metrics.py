"""Custom metrics for evaluation."""

from typing import Dict, Tuple

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score


def compute_metrics(predictions: np.ndarray, labels: np.ndarray) -> Dict[str, float]:
    """Compute classification metrics.
    
    Args:
        predictions: Predicted labels (shape: [batch_size])
        labels: Ground truth labels (shape: [batch_size])
    
    Returns:
        Dictionary with metrics: accuracy, precision, recall, f1
    """
    accuracy = accuracy_score(labels, predictions)
    precision = precision_score(labels, predictions, zero_division=0, average='binary')
    recall = recall_score(labels, predictions, zero_division=0, average='binary')
    f1 = f1_score(labels, predictions, zero_division=0, average='binary')
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
    }


def compute_correlation(
    probabilities: np.ndarray, 
    labels: np.ndarray
) -> Tuple[float, float]:
    """Compute Spearman correlation between probabilities and labels.
    
    Args:
        probabilities: Predicted probabilities (shape: [batch_size])
        labels: Ground truth labels (shape: [batch_size])
    
    Returns:
        Tuple of (correlation coefficient, p-value)
    """
    correlation, p_value = spearmanr(probabilities, labels)
    return correlation, p_value
