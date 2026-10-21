# Local FactCG 12-sample smoke

Status: **PASS**

| canonical_id | task | FactCG support probability |
|---|---|---|
| HDEV_0001_e3a6ae1bd526 | DM | 0.2185198069 |
| HDEV_0002_3d51bbb57230 | DM | 0.9528976083 |
| HDEV_0003_530e1aebd9d8 | DM | 0.0380134732 |
| HDEV_0004_e249137cb532 | DM | 0.3243009448 |
| HDEV_0313_309fe2c60a90 | MT | 0.0272306763 |
| HDEV_0314_cc66f0011ead | MT | 0.3208937049 |
| HDEV_0315_a999432d4765 | MT | 0.0256845560 |
| HDEV_0316_b50d3005456c | MT | 0.0551905856 |
| HDEV_0188_10b0356acc52 | PG | 0.6211690307 |
| HDEV_0189_059ce4f91dea | PG | 0.1011005118 |
| HDEV_0190_5d6ecaa6eba3 | PG | 0.1813083887 |
| HDEV_0191_75d66ca83425 | PG | 0.0680656731 |

Runtime and integrity metadata:

```json
{
  "status": "PASS",
  "model_id": "yaxili96/FactCG-DeBERTa-v3-Large",
  "revision": "0430e3509dbd28d2dff7a117c0eae25359ff3e80",
  "device": "cpu",
  "dtype": "float32",
  "batch_size": 1,
  "model_loaded": true,
  "outputs": 12,
  "leakage_check": "PASS",
  "recommendation": "LOCAL_FULL_RUN",
  "reason": "Orientation, 12 sample coverage, finite range, reference policy and leakage checks passed",
  "model_load_seconds": 29.823567599989474,
  "inference_12_seconds": 13.491027399955783,
  "download_seconds": 316.9647735999897,
  "memory": {
    "peak_sampled_rss_bytes": 1632743424,
    "minimum_system_available_bytes": 3006550016,
    "total_system_ram_bytes": 16907886592,
    "os_peak_working_set_bytes": 1632743424,
    "measurement": "Process RSS sampled every 0.1 sec; Windows OS peak working set when available; minimum available system RAM"
  },
  "software": {
    "torch": "2.2.1+cpu",
    "transformers": "4.38.1",
    "tokenizers": "0.15.2",
    "numpy": "1.26.4",
    "nltk": "3.9.1",
    "huggingface-hub": "0.26.2",
    "safetensors": "0.4.5",
    "sentencepiece": "0.2.0",
    "psutil": "6.1.0",
    "accelerate": "0.28.0"
  },
  "python": "3.11.9 | packaged by Anaconda, Inc. | (main, Apr 19 2024, 16:40:41) [MSC v.1916 64 bit (AMD64)]",
  "platform": "Windows-10-10.0.26200-SP0",
  "cpu": "Intel64 Family 6 Model 140 Stepping 1, GenuineIntel",
  "reference_policy_check": "PASS",
  "input_sha256": "10ecdbc5f25bd4b9c7c7d4c2d131194647a86c556591c75418dbcb436ba1753d",
  "selected_input_digest": "938ed6320509f29d5ced576768323e4b929f3b22e494d84f39f3aa678138a9e5",
  "selection": "First four canonical IDs sorted independently within each task; no labels read",
  "threads": {
    "intraop": 4,
    "interop": 1
  },
  "cuda_available": false,
  "parameter_count": 435063810,
  "orientation": {
    "supported_probability": 0.7685862183570862,
    "contradictory_probability": 0.04932050779461861,
    "gap": 0.7192657105624676,
    "required_gap": 0.25,
    "inference_seconds": 2.297523299988825,
    "semantics": "Official HF branch: softmax(logits)[:,1], max over reference chunks",
    "status": "PASS"
  },
  "counts_by_task": {
    "DM": 4,
    "MT": 4,
    "PG": 4
  },
  "output_sha256": "827f5564b1e454cc43f97af5076c11e6901bf0acdf33c9cd831bd81d74a33863",
  "per_sample_seconds": [
    0.9893621999653988,
    1.0485523999668658,
    0.9639812000095844,
    1.066233099962119,
    1.0366306999931112,
    1.1406113999546506,
    1.0879771999898367,
    1.5239300999674015,
    1.2992151999496855,
    1.0706041000084952,
    1.0528752999962308,
    1.2061434999923222
  ],
  "estimate_561": {
    "warm_cache_load_plus_inference_seconds": 660.2995092885685,
    "inference_only_seconds": 630.475941688579,
    "cold_download_additional_seconds": 316.9647735999897,
    "mean_seconds_per_sample": 1.1238430333129752,
    "median_seconds_per_sample": 1.068418599985307,
    "slowest_sample_linear_projection_seconds": 884.7483536817017,
    "limitation": "Linear extrapolation from 12 fixed ID-selected samples; not a representative performance benchmark. No full run executed."
  },
  "frozen_packages_unchanged": true,
  "wall_seconds": 372.78299759997753
}
```

LOCAL_FULL_RUN
