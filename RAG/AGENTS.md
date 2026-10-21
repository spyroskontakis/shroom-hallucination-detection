# SHROOM RAG Project Instructions

## Project goal

Extend the existing model-agnostic SHROOM hallucination-detection implementation with a controlled RAG experiment while preserving the completed E1-E4 experiments.

## Baseline that must remain unchanged

- Selected baseline: `E3_NLI_similarity`.
- E3 features: 6 NLI + 8 semantic-similarity features.
- Development set: 499 model-agnostic samples.
- Evaluation: the existing five common stratified folds.
- Selection metrics: Overall OOF Accuracy first, Overall OOF Spearman second.

## Current scope

- Work only on the Module 1 learning prototype unless the user explicitly approves the next module.
- Use a separate notebook named `shroom_rag_e5_module1.ipynb`.
- Do not edit the original E1-E4 notebook.
- Explain new functions with short Greek Markdown cells in simple undergraduate style.

## Data and leakage rules

- Build the knowledge base only from `train.model-agnostic.json` in the unlabeled training split.
- Never place `label`, `labels`, `label_bin`, `p(Hallucination)`, or `p_hallucination` in retrieval queries or LLM prompts.
- Never use development labels for retrieval, prompt construction, tuning, or generation.
- Development labels may be joined only after predictions exist, for evaluation.
- Do not load or use the official test set during development or model selection.
- If labeled examples are ever retrieved in a future experiment, the retrieval index must be rebuilt from the training portion of each CV fold only.

## API and credential safety

- Keep API execution disabled by default.
- Do not run Gemini calls unless `RUN_API_CALLS=True` was explicitly set by the user.
- Start with at most three samples per mode.
- Cache every successful response immediately and resume from cache.
- Never print, copy, commit, or modify a service-account JSON key.
- Read credential paths and project identifiers from environment variables only.

## Module 1 technical constraints

- Support both `<define>term</define>` and `<define> term <define>` formats.
- Return `None` when a term cannot be extracted reliably; do not guess.
- Use normalized exact term matching only.
- Retrieve no more than three definitions.
- Do not add LangChain, LlamaIndex, FAISS, Weaviate, BM25, or dense retrieval yet.
- Treat retrieved evidence as secondary to the provided SHROOM reference.
- Structured LLM output must include `p_hallucination`, `label`, `reason`, and `evidence_ids`.

## Change and review rules

- Plan before editing.
- Make focused changes and show the diff.
- Do not rerun expensive NLI or API cells unless necessary.
- Add or update offline tests for extraction, normalization, response validation, and cache behavior.
- Preserve deterministic settings such as `RANDOM_STATE=42`.
- Do not overwrite cached outputs or completed experiment results.

## Module 1 is done when

- Offline extraction and exact-retrieval tests pass.
- Exact-retrieval coverage is reported for a fixed 20-example DM sample.
- At least five retrieved results are manually reviewed.
- Prompt inspection confirms that no gold labels are included.
- The approved 3+3 API smoke run returns valid cached JSON.
- Failures and cases of irrelevant evidence are documented before Module 2 begins.
