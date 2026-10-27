"""Example script to test the hallucination detection system."""

import json
from pathlib import Path

from src.data.loader import save_jsonl


def create_example_data():
    """Create minimal example SHROOM data for testing."""
    
    # Create example training data
    train_examples = [
        {
            "src": "The capital of France is Paris.",
            "tgt": "Paris is the capital city of France.",
            "hyp": "Paris is the capital of France.",
            "label": "not_hallucinated",
            "task": "MT"
        },
        {
            "src": "The capital of France is Paris.",
            "tgt": "Paris is the capital city of France.",
            "hyp": "London is the capital of France.",
            "label": "hallucinated",
            "task": "MT"
        },
        {
            "src": "Einstein developed the theory of relativity.",
            "tgt": "Albert Einstein developed the special and general theories of relativity.",
            "hyp": "Albert Einstein developed the theory of relativity.",
            "label": "not_hallucinated",
            "task": "MT"
        },
        {
            "src": "Einstein developed the theory of relativity.",
            "tgt": "Albert Einstein developed the special and general theories of relativity.",
            "hyp": "Einstein invented the airplane.",
            "label": "hallucinated",
            "task": "MT"
        },
    ]
    
    # Create example eval data
    eval_examples = [
        {
            "src": "The Great Wall is in China.",
            "tgt": "The Great Wall of China is a massive fortification.",
            "hyp": "The Great Wall is in China.",
            "label": "not_hallucinated",
            "task": "MT"
        },
        {
            "src": "The Great Wall is in China.",
            "tgt": "The Great Wall of China is a massive fortification.",
            "hyp": "The Great Wall is in Japan.",
            "label": "hallucinated",
            "task": "MT"
        },
    ]
    
    # Save example data
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    
    train_path = Path("data/raw/train_example.jsonl")
    eval_path = Path("data/raw/eval_example.jsonl")
    
    save_jsonl(train_examples, train_path)
    save_jsonl(eval_examples, eval_path)
    
    print(f"✅ Created example training data: {train_path}")
    print(f"   {len(train_examples)} examples")
    print(f"\n✅ Created example eval data: {eval_path}")
    print(f"   {len(eval_examples)} examples")
    
    # Print sample
    print(f"\n📝 Sample training example:")
    print(f"   {json.dumps(train_examples[0], indent=2)}")


if __name__ == "__main__":
    print("Creating example SHROOM data for testing...\n")
    create_example_data()
    
    print("\n" + "="*60)
    print("Next steps:")
    print("="*60)
    print("\n1. Install dependencies:")
    print("   pip install -r requirements.txt")
    print("\n2. Train model (uses example data):")
    print("   python -m src.main train \\")
    print("     --train_data data/raw/train_example.jsonl \\")
    print("     --eval_data data/raw/eval_example.jsonl \\")
    print("     --output_dir ./output \\")
    print("     --epochs 2 \\")
    print("     --batch_size 2")
    print("\n3. Evaluate model:")
    print("   python -m src.main evaluate \\")
    print("     --model_path ./output \\")
    print("     --data_path data/raw/eval_example.jsonl")
    print("\n" + "="*60)
