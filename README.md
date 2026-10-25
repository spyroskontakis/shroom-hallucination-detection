# SHROOM Hallucination Detection

This repository contains the implementation and results of my diploma thesis on **hallucination detection in natural language generation**, developed in the context of **SemEval-2024 Task 6 (SHROOM)**.

The research focuses on the **model-agnostic track**, where generated text is evaluated using the available source and reference texts, without access to the model that produced it.

The study covers three natural language generation tasks:

- **Definition Modeling (DM):** Generating definitions of words or expressions.
- **Machine Translation (MT):** Translating text between languages.
- **Paraphrase Generation (PG):** Rewriting text while preserving its meaning.

The goal is to detect fluent and plausible generated text whose meaning is not supported by the appropriate reference.

The project includes experiments **E1-E11**, investigating different approaches based on semantic analysis, external knowledge retrieval and machine learning.

## Methodology

The initial approach combines two types of semantic information:

- **Natural Language Inference (NLI):** Estimates whether a reference supports, contradicts or neither supports nor contradicts the generated text.
- **Semantic Similarity:** Uses sentence embeddings to compare the source, reference and generated texts.

The combined baseline uses six NLI features and eight semantic similarity features. These are provided to a **Random Forest Regressor**, which predicts a continuous hallucination score. The score is converted into a binary label using a threshold of 0.5.

The approach was progressively extended with external dictionary definitions, additional semantic verification methods and alternative training strategies.

The main extensions include:

- Retrieval and selection of relevant definitions using lexical and semantic search.
- Additional semantic checks using HHEM, BERTScore, MiniCheck and FactCG.
- Verification of individual claims within generated text.
- Selective use of external information through rule-based routing.
- Different Random Forest configurations.
- Transformer fine-tuning with additional supervision and contrastive learning.

These methods were investigated through separate experiments and do not all form part of a single final model.

## Experiments

The experimental work was organized into three phases:

- **Phase 1 (E1-E4):** Development of the initial detection approach and investigation of synthetic training data.
- **Phase 2 (E5-E8):** External knowledge retrieval, additional features and alternative model configurations.
- **Phase 3 (E9-E11):** Claim verification and alternative transformer training strategies.

| Experiment | Description |
|---|---|
| E1 | Hallucination detection using NLI features |
| E2 | Hallucination detection using semantic similarity features |
| E3 | Combination of NLI and semantic similarity using Random Forest |
| E4 | Investigation of synthetic training data |
| E5 | Retrieval and evaluation of external dictionary definitions, followed by their use as additional features |
| E6 | Additional semantic and structural features, including a second NLI evaluator, HHEM and BERTScore |
| E7 | Rule-based selection between the baseline and an evidence-enhanced model |
| E8 | Random Forest configuration selection using nested cross-validation |
| E9 | Verification of individual claims using NLI and MiniCheck |
| E10 | Additional verification of the complete generated text using FactCG |
| E11 | DeBERTa fine-tuning with human labels, additional automatic supervision and contrastive learning |

E6 includes four successive versions (E6-v1 to E6-v4). E9 and E11 also investigate different configurations.

E7 examines a simple rule-based routing approach, referred to in the thesis as Agentic RAG. It selects between existing model predictions based on the availability and relevance of retrieved information, without using an autonomous LLM agent.

E11 includes variants A-E. E11-B investigated the feasibility of automatically generated labels but did not produce a final trained transformer or evaluation metrics.

Detailed experiment descriptions are available in the [experiment documentation](docs/EXPERIMENTS.md).

## Evaluation

The main experimental comparisons use a shared development dataset of **561 human-labeled examples**, assembled from the SHROOM development and trial sets after removing duplicates and exact example overlaps with the official test set.

The evaluation uses **stratified 5-fold cross-validation with out-of-fold (OOF) predictions**.

The examples are divided into five groups while preserving the distribution of tasks and hallucination labels. In each iteration, a model is trained on four groups and evaluated on the remaining group. Every example receives one prediction from a model that was not trained on that example.

The same predefined splits are used across the main comparisons. Experiment E8 additionally uses internal 3-fold cross-validation to select Random Forest configurations within each outer training split.

Two main evaluation metrics are used:

- **Accuracy:** The percentage of correctly classified examples.
- **Spearman correlation:** How closely the predicted scores rank examples in the same order as the human hallucination scores.

Accuracy is the primary comparison criterion, with Spearman correlation used as a secondary criterion.

The earlier E1-E4 notebook evaluation used 499 examples. Its results should not be directly compared with the later 561-example evaluation.

Because successive configurations were developed and compared on the same development set, the reported results primarily support comparisons between experimental approaches rather than independent confirmation of generalization.

## Results

The following table presents selected results from the shared 561-example development evaluation.

| Experiment | Correct predictions | Accuracy | Spearman |
|---|---:|---:|---:|
| E3 (re-evaluated baseline) | 445/561 | 79.32% | 0.7390 |
| E5 | 446/561 | 79.50% | 0.7422 |
| E6-v3 | 474/561 | 84.49% | 0.7817 |
| E9-B | 468/561 | 83.42% | 0.7886 |
| E10 | 475/561 | 84.67% | 0.7828 |
| E11-C | 466/561 | 83.07% | 0.7270 |

Among the configurations evaluated on the shared development set:

- **E10 achieved the highest accuracy**, with 475 correct predictions out of 561 examples (84.67%).
- **E9-B achieved the highest Spearman correlation**, with a value of 0.7886.

E10 classified one more example correctly than E6-v3. However, the paired comparison did not establish a statistically significant improvement (McNemar p = 1.0).

Overall, the experiments show that additional features and more complex training strategies do not necessarily lead to better results.

The complete results are available in [Results](docs/RESULTS.md).

### Retrospective Evaluation on the Official Test Set

E10 was also evaluated retrospectively on the official SHROOM model-agnostic test set of 1,500 examples.

| Metric | Result |
|---|---:|
| Correct predictions | 1,234/1,500 |
| Accuracy | 82.27% |
| Spearman correlation | 0.7501 |

This evaluation was performed after the official labels had been released and required reconstruction of part of the external dictionary evidence.

Earlier exploratory work had also used the official test set. Additionally, the final training pool retained 14 MT examples sharing source and reference pairs with test examples, although their generated hypotheses were different.

Therefore, these results should not be interpreted as an independent, untouched test evaluation or as an official SemEval competition submission.

Further details are available in [Known Limitations](docs/KNOWN_LIMITATIONS.md).

## Technical Implementation

Beyond the experimental comparisons, the project includes:

- Data preparation, feature extraction and evaluation pipelines using consistent data splits.
- Retrieval and semantic verification methods for evaluating generated text.
- Transformer fine-tuning experiments with different training strategies.
- Reproducibility checks, recorded configurations and tests for verifying experimental artifacts.

The implementation uses the following technologies:

**Python**, **PyTorch**, **Hugging Face Transformers**, **Sentence Transformers**, **scikit-learn**, **NumPy**, **pandas**, **SciPy** and **Jupyter Notebooks**.

Selected experiments also used **Modal** for remote execution.

## Repository Structure

| Directory | Contents |
|---|---|
| `codex/` | Data preparation, feature extraction and evaluation procedures |
| `RAG/` | Baseline notebooks, RAG development and experiments E5-E11 |
| `solution/` | Separate baseline implementation and command-line tools |
| `data/` | Selected notebooks and experimental summaries |
| `docs/` | Methodology, results and reproducibility documentation |
| `thesis/` | Complete thesis in PDF and Word formats |
| `presentation/` | Thesis presentation in PowerPoint format |
| `manifests/` | Records for verifying files and experimental artifacts |
| `historical_versions/` | Preserved source snapshots from earlier development stages |

The original directory structure was retained where necessary to preserve references between scripts and experimental files.

## Getting Started

This repository contains research implementations rather than a single ready-to-run application.

For an example of the available command-line functionality, see the [solution quickstart](solution/QUICKSTART.md). This is a separate implementation and does not reproduce the complete thesis results.

To explore a specific experiment, start with the [experiment documentation](docs/EXPERIMENTS.md) and consult its corresponding scripts and evaluation protocol.

Additional technical documentation:

- [Architecture](docs/ARCHITECTURE.md)
- [Results](docs/RESULTS.md)
- [Reproducibility](docs/REPRODUCIBILITY.md)
- [Environment Requirements](docs/ENVIRONMENTS.md)
- [Data Access](docs/DATA_ACCESS.md)
- [Known Limitations](docs/KNOWN_LIMITATIONS.md)

### Reproducibility

The repository includes source code, experimental configurations, evaluation protocols and recorded results.

However, full datasets, pretrained model weights, intermediate features and some saved experimental artifacts are not distributed here.

Exact reproduction may require the original inputs, recorded model versions, saved features, retrieval artifacts and experiment-specific environments. Public fold assignments alone are not sufficient.

Some historical scripts and external dependencies may also require additional setup or access to previously used services and model versions.

## Thesis and Presentation

**Thesis:** *Ανίχνευση hallucinations σε συστήματα παραγωγής φυσικής γλώσσας: πειραματική μελέτη στο πλαίσιο του διαγωνισμού SHROOM*

**Author:** Spyros Kontakis

**Institution:** University of Ioannina, Department of Computer Science and Engineering

**Supervisor:** Konstantinos Skianis

**Date:** October 2026

The complete thesis and presentation are available below:

- [Thesis (PDF)](thesis/Thesis.pdf)
- [Thesis (Word)](thesis/Thesis.docx)
- [Thesis Presentation (PowerPoint)](presentation/Thesis_Presentation.pptx)

## License

Original project material that the author is entitled to license is provided under the [MIT License](LICENSE).

Third-party code and components retain their respective licenses and copyright notices. Datasets and pretrained model weights are not covered by the project's MIT license.

For details, see the [licensing information](docs/LICENSE_PROPOSAL.md) and [third-party notices](docs/THIRD_PARTY_NOTICES.md).