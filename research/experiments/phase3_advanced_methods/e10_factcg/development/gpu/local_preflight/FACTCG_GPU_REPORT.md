# FactCG GPU report

```json
{
  "status": "BLOCKED",
  "model_id": "yaxili96/FactCG-DeBERTa-v3-Large",
  "model_revision": "0430e3509dbd28d2dff7a117c0eae25359ff3e80",
  "manifest_sha256": "357e2b011f9403dfe9fb28ae84ffc4cd3524eeb5e9f347d3d295f90dceb30d3f",
  "model_loaded": false,
  "samples_processed": 0,
  "inference_errors": [],
  "retries": 0,
  "output_sha256": null,
  "settings": {
    "device": "cuda:0",
    "dtype": "float32",
    "use_safetensors": true,
    "use_fast": true,
    "max_length": 2048,
    "truncation": "only_first",
    "padding": "longest",
    "pad_token": "eos_token",
    "reference_chunk_words": 550,
    "batch_size": 1,
    "hypothesis_split": false,
    "support_class_index": 1,
    "activation": "softmax",
    "reference_aggregation": "max",
    "temperature_scaling": null,
    "quantization": null,
    "autocast": false,
    "matmul_allow_tf32": false,
    "seed": 42
  },
  "dependencies": {},
  "device": {
    "platform": "Windows-10-10.0.26200-SP0",
    "python": "3.11.9 | packaged by Anaconda, Inc. | (main, Apr 19 2024, 16:40:41) [MSC v.1916 64 bit (AMD64)]"
  },
  "truncated_chunks": 0,
  "reference_chunks": 0,
  "max_untruncated_tokens": 0,
  "reason": "Linux x86_64 required",
  "elapsed_seconds": 0.09399999998277053
}
```
