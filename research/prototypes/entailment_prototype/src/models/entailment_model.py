"""Entailment-based hallucination detection model."""

import json
from importlib.util import find_spec
from pathlib import Path
from typing import Optional

import torch
from torch import nn
from transformers import AutoModel, AutoTokenizer, PreTrainedTokenizer
from transformers.modeling_outputs import SequenceClassifierOutput


class EntailmentModel(nn.Module):
    """Entailment model for hallucination detection.
    
    Uses a pre-trained transformer model (e.g., DeBERTa) to perform
    sequence classification on (premise, hypothesis) pairs.
    """
    
    def __init__(
        self,
        model_name: str = "microsoft/deberta-large",
        num_labels: int = 2,
        dropout: float = 0.1,
    ) -> None:
        """Initialize entailment model.
        
        Args:
            model_name: HuggingFace model identifier.
            num_labels: Number of output classes (2 for binary classification).
            dropout: Dropout probability for classification head.
        """
        super().__init__()
        self.model_name = model_name
        self.num_labels = num_labels
        
        # Load pre-trained model
        self.transformer = AutoModel.from_pretrained(model_name)
        
        # Classification head
        hidden_size = self.transformer.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        self.classify = nn.Linear(hidden_size, num_labels)
    
    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        token_type_ids: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
    ) -> SequenceClassifierOutput:
        """Forward pass.
        
        Args:
            input_ids: Input token IDs (shape: [batch_size, seq_len])
            attention_mask: Attention mask (shape: [batch_size, seq_len])
            token_type_ids: Token type IDs (shape: [batch_size, seq_len])
            labels: Target labels (shape: [batch_size])
        
        Returns:
            HuggingFace-compatible sequence classification output.
        """
        transformer_kwargs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        }
        if token_type_ids is not None:
            transformer_kwargs["token_type_ids"] = token_type_ids

        outputs = self.transformer(
            **transformer_kwargs,
        )
        
        # Use [CLS] token representation
        pooled_output = outputs.last_hidden_state[:, 0, :]
        
        # Classification
        logits = self.classify(self.dropout(pooled_output))

        loss = None
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(logits.view(-1, self.num_labels), labels.view(-1))

        return SequenceClassifierOutput(
            loss=loss,
            logits=logits,
            hidden_states=getattr(outputs, "hidden_states", None),
            attentions=getattr(outputs, "attentions", None),
        )


def load_model_and_tokenizer(
    model_name: str = "microsoft/deberta-large",
    num_labels: int = 2,
) -> tuple[EntailmentModel, PreTrainedTokenizer]:
    """Load model and tokenizer.
    
    Args:
        model_name: HuggingFace model identifier.
        num_labels: Number of output classes.
    
    Returns:
        Tuple of (model, tokenizer)
    """
    model = EntailmentModel(model_name=model_name, num_labels=num_labels)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    return model, tokenizer


def infer_model_name(model_path: str, fallback: str = "microsoft/deberta-large") -> str:
    """Infer the base HuggingFace model name from a saved training directory."""
    model_path_obj = Path(model_path)
    metadata_path = model_path_obj / "model_metadata.json"

    if metadata_path.exists():
        try:
            with metadata_path.open("r", encoding="utf-8") as metadata_file:
                metadata = json.load(metadata_file)
            if isinstance(metadata, dict) and isinstance(metadata.get("model_name"), str):
                return metadata["model_name"]
        except Exception:
            pass

    return fallback


def load_checkpoint_weights(model: nn.Module, model_path: str, device: str) -> bool:
    """Load saved weights from a Trainer output directory if present."""
    model_path_obj = Path(model_path)
    safetensors_path = model_path_obj / "model.safetensors"
    pytorch_path = model_path_obj / "pytorch_model.bin"

    if safetensors_path.exists() and find_spec("safetensors") is not None:
        from safetensors.torch import load_file

        state_dict = load_file(str(safetensors_path), device=device)
        model.load_state_dict(state_dict)
        return True

    if pytorch_path.exists():
        state_dict = torch.load(pytorch_path, map_location=device)
        model.load_state_dict(state_dict)
        return True

    return False
