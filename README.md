# SHROOM Hallucination Detection

This repository contains the implementation and results of my diploma thesis on **hallucination detection in natural language generation**, developed in the context of **SemEval-2024 Task 6 (SHROOM)**.

The goal of this research was to investigate different approaches to hallucination detection and compare their effectiveness across multiple natural language generation tasks.

## The Problem

Language models can generate text that is fluent and grammatically correct but does not accurately preserve the intended meaning.

For example, consider the following sentences:

- **Original:** "It's my job."
- **Generated:** "It's my duty."

Although these sentences are semantically similar, they do not express exactly the same meaning.

Such cases illustrate why hallucination detection can be challenging. The difference is not always obvious, and human evaluators may disagree on whether the generated text is acceptable.

## SHROOM Benchmark

SHROOM was introduced as part of SemEval-2024 to evaluate hallucination detection methods using a common dataset and evaluation framework.

The benchmark includes two tracks:

- **Model-aware:** The detection system has access to the model that generated the text.
- **Model-agnostic:** The detection system evaluates generated text without access to the generating model.

This thesis focuses on the **model-agnostic track**, aiming to detect hallucinations without depending on a specific text generation model.

Three tasks are considered:

- **Definition Modeling (DM):** Generating definitions of words or expressions.
- **Machine Translation (MT):** Translating text between languages.
- **Paraphrase Generation (PG):** Rewriting text while preserving its original meaning.

## Prediction Task

Each SHROOM example contains the generated text that must be evaluated, along with additional information:

| Field | Description |
|---|---|
| `hyp` | The generated text being evaluated |
| `src` | The original input text |
| `tgt` | The expected or reference text |

The available information is used differently depending on the task. Definition Modeling primarily relies on the target reference, while Machine Translation and Paraphrase Generation can also use the source text.

The detection system produces two outputs:

1. A **hallucination score between 0 and 1**, estimating the likelihood that the generated text contains a hallucination.
2. A **binary prediction**, classifying the text as Hallucination or Not Hallucination using a threshold of 0.5.

## Data and Evaluation

The initial exploratory data analysis examined the 499 examples in the model-agnostic development set.

Two important observations influenced the methodology:

First, the distribution of hallucinations differs between tasks. To account for these differences, the main evaluation uses **Stratified 5-Fold Cross-Validation with Out-of-Fold (OOF) predictions**.

The data is divided into five folds while preserving the distribution of tasks and hallucination labels. In each iteration, four folds provide the human-labeled training data, while the remaining fold is used for evaluation. Each example receives one OOF prediction, and the overall metrics are calculated from the combined predictions.

Second, human evaluators do not always agree. Rather than treating hallucination detection only as a binary classification problem, the main approach uses a **regression model** to predict the continuous hallucination score derived from human annotations.

The later experiments use a shared development set of **561 human-labeled examples**, obtained from the development and trial sets after duplicate handling and removal of exact overlaps with the official test set.

The evaluation uses two main metrics:

- **Accuracy:** The proportion of correctly classified examples.
- **Spearman correlation:** The agreement between the ranking of predicted hallucination scores and the ranking derived from human evaluations.

Accuracy is the primary comparison criterion, while Spearman correlation is secondary.

## Experimental Approach

The research was organized into three experimental phases, starting with a semantic-feature baseline and progressively exploring external knowledge, additional verification methods and transformer fine-tuning.

### Phase 1 - Semantic Features (E1-E4)

The initial approach converts semantic relationships between texts into numerical features that can be used by a machine learning model.

- **E1 - Natural Language Inference:** DeBERTa is used to extract six features describing whether one text supports, contradicts or is neutral toward another.
- **E2 - Semantic Similarity:** MPNet is used to extract eight features measuring how closely the source, reference and generated texts are related in meaning.
- **E3 - Combined Approach:** The six NLI features and eight similarity features are combined into 14 features and provided to a Random Forest Regressor with 500 decision trees.
- **E4 - Synthetic Data:** Additional automatically generated examples are investigated to determine whether they improve the initial approach.

The main objective was to examine whether combining different semantic signals performs better than using each approach separately.

### Phase 2 - External Knowledge and Additional Features (E5-E8)

The second phase extends the initial Random Forest approach with external information and additional methods for comparing texts.

- **E5 - Retrieval-Augmented Generation (RAG):** External dictionary definitions, primarily from Wiktionary, are retrieved for Definition Modeling. Relevant information is selected and converted into additional numerical features.
- **E6 - Feature Extensions:** Four versions examine additional comparisons with retrieved definitions, a second NLI evaluator, HHEM, BERTScore and structural features.
- **E7 - Selective Agentic RAG:** A simple rule-based method selects between the E3 and E6-v1 predictions depending on the availability and relevance of retrieved information. This is not an autonomous LLM agent.
- **E8 - Random Forest Tuning:** Different Random Forest configurations are tested using nested cross-validation, without introducing new predictor features.

The objective was to determine which extensions provide useful improvements over the original semantic-feature baseline.

### Phase 3 - Claim Verification and Transformer Fine-Tuning (E9-E11)

The final phase investigates different ways of verifying generated text.

- **E9 - Claim-Level Verification:** Generated text is divided into smaller statements, called claims. Each claim is evaluated separately using methods including NLI and MiniCheck.
- **E10 - FactCG Verification:** Instead of splitting the generated text into claims, FactCG evaluates the complete generated text against the appropriate reference. Its support score is added to the E6-v3 features and used by the Random Forest.
- **E11 - Transformer Fine-Tuning:** DeBERTa is trained directly for hallucination detection, without using the Random Forest. The experiments investigate human labels, automatically generated supervision and contrastive learning.

E11 includes several variants. E11-B examined the feasibility of automatically generated labels but did not produce a final trained model or evaluation metrics.

The complete experiment descriptions and related implementations are available in [Experiment Documentation](docs/EXPERIMENTS.md).

## Results

The following table summarizes selected results from the shared 561-example development evaluation.

| Experiment | Correct predictions | Accuracy | Spearman |
|---|---:|---:|---:|
| E3 (re-evaluated baseline) | 445/561 | 79.32% | 0.7390 |
| E5 | 446/561 | 79.50% | 0.7422 |
| E6-v3 | 474/561 | 84.49% | 0.7817 |
| E9-B | 468/561 | 83.42% | 0.7886 |
| E10 | 475/561 | 84.67% | 0.7828 |
| E11-C | 466/561 | 83.07% | 0.7270 |

**E10 achieved the highest development accuracy of 84.67%**, correctly classifying 475 out of 561 examples.

**E9-B achieved the highest Spearman correlation of 0.7886.**

E10 was selected as the best-performing configuration according to the accuracy-first evaluation criterion.

However, its improvement over E6-v3 was limited to one additional correct prediction and was not statistically established as significant (McNemar p = 1.0).

These development results reflect comparisons between approaches explored on the same dataset and should not be treated as independent confirmation of generalization.

### Retrospective Evaluation on the Official Test Set

E10 was also evaluated retrospectively on the official SHROOM model-agnostic test set of 1,500 examples.

| Metric | Result |
|---|---:|
| Correct predictions | 1,234/1,500 |
| Accuracy | 82.27% |
| Spearman correlation | 0.7501 |

This evaluation took place after the official labels had been released and involved reconstruction of external dictionary evidence.

The official test set had also been used in earlier exploratory work. In addition, the final training pool retained 14 Machine Translation examples sharing source and reference pairs with test examples, although their generated outputs differed.

These results therefore represent a **retrospective evaluation**, not an official SemEval submission or an independent untouched test.

See the [test-use audit](RAG/results/e10_official_test_v1/recovery_audit/PRIOR_TEST_USE_AUDIT.md), [MT overlap audit](RAG/results/e10_official_test_v1/recovery_audit/E10_OFFICIAL_TEST_MT_OVERLAP_AUDIT.md) and [full results](docs/RESULTS.md).

## Key Findings

The experiments led to three main observations:

1. **NLI provides a strong foundation for hallucination detection.** Semantic similarity is also useful, particularly when combined with NLI features.

2. **Automatically generated supervision can support transformer training**, but the tested fine-tuned models did not outperform the strongest feature-based approach.

3. **Increasing model complexity does not necessarily improve performance.** The usefulness of additional features and verification methods depends on the information they provide.

Future work could investigate more adaptive retrieval strategies, more reliable external knowledge sources and improved methods for selecting automatically generated training labels.

## Technologies

The project primarily uses Python, PyTorch, Hugging Face Transformers, Sentence Transformers, scikit-learn, NumPy, pandas, SciPy and Jupyter Notebooks.

Selected experiments used Modal for remote execution.

## Repository Structure

| Directory | Description |
|---|---|
| `codex/` | Data preparation, semantic feature extraction and cross-validation procedures |
| `data/` | Exploratory analysis notebooks and early experiment summaries |
| `RAG/` | Retrieval modules, additional verification methods and experiments E5-E11 |
| `solution/` | Separate Python implementation with training, evaluation and CLI utilities |
| `docs/` | Technical documentation, experimental results and reproducibility information |
| `thesis/` | Complete thesis in PDF and Word formats |
| `presentation/` | Thesis presentation in PowerPoint format |
| `manifests/` | File verification records and public release documentation |
| `historical_versions/` | Preserved historical source snapshots, not standalone runnable versions |
| `thesis_writing/` | Supporting script for verifying research results used during thesis writing |
| `tools/` | Scripts for checking and preparing the public repository release |

The original directory structure was preserved where necessary to maintain compatibility with existing research scripts and recorded experimental files.

## Getting Started

This repository documents a series of research experiments rather than a single ready-to-run application.

To explore the work, start with the [experiment index](docs/EXPERIMENTS.md), which connects each experiment to its corresponding implementation.

The [solution quickstart](solution/QUICKSTART.md) provides an example of the separate command-line implementation. It does not reproduce the complete thesis results.

Additional documentation is available in:

- [Architecture](docs/ARCHITECTURE.md)
- [Results](docs/RESULTS.md)
- [Reproducibility](docs/REPRODUCIBILITY.md)
- [Environment Requirements](docs/ENVIRONMENTS.md)
- [Data Access](docs/DATA_ACCESS.md)
- [Known Limitations](docs/KNOWN_LIMITATIONS.md)

### Reproducibility

The repository includes implementation code, experiment configurations, evaluation protocols and recorded results.

Full datasets, model weights, intermediate features and some saved experimental artifacts are not distributed here. Exact reproduction may require separately obtained data, recorded model versions and experiment-specific environments.

## Thesis and Presentation

**Thesis:** *Ανίχνευση hallucinations σε συστήματα παραγωγής φυσικής γλώσσας: πειραματική μελέτη στο πλαίσιο του διαγωνισμού SHROOM*

**Author:** Spyros Kontakis

**Institution:** University of Ioannina, Department of Computer Science and Engineering

**Supervisor:** Konstantinos Skianis

**Date:** October 2026

- [Thesis (PDF)](thesis/Thesis.pdf)
- [Thesis (Word)](thesis/Thesis.docx)
- [Thesis Presentation (PowerPoint)](presentation/Thesis_Presentation.pptx)

## License

Original project material that the author is entitled to license is provided under the [MIT License](LICENSE).

Third-party components retain their respective licenses and copyright notices. Datasets and pretrained model weights are not covered by the project's MIT license.

See the [licensing information](docs/LICENSE_PROPOSAL.md) and [third-party notices](docs/THIRD_PARTY_NOTICES.md).