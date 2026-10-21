"""Data loading utilities for SHROOM dataset."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd


def load_jsonl(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Load JSONL file.
    
    Args:
        file_path: Path to JSONL file.
    
    Returns:
        List of dictionaries, one per line.
    """
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def load_data(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Load JSON or JSONL file automatically.
    
    Args:
        file_path: Path to JSON or JSONL file.
    
    Returns:
        List of dictionaries.
    """
    file_path = Path(file_path)
    
    if file_path.suffix.lower() == '.jsonl':
        return load_jsonl(file_path)
    else:
        # Try loading as JSON
        result = load_json(file_path)
        # If it's a dict, wrap in list; if already a list, return as-is
        return result if isinstance(result, list) else [result]


def load_json(file_path: Union[str, Path]) -> Union[List, Dict]:
    """Load JSON file.
    
    Args:
        file_path: Path to JSON file.
    
    Returns:
        Parsed JSON object (list or dict).
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_jsonl(data: List[Dict[str, Any]], file_path: Union[str, Path]) -> None:
    """Save list of dictionaries to JSONL file.
    
    Args:
        data: List of dictionaries.
        file_path: Path where to save JSONL file.
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')
