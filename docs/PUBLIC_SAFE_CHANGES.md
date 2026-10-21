# Public-safe derivatives
Originals and previous staging are unchanged. Every candidate file has a hash and provenance record.
Notebook outputs, execution counts, attachments and nonessential metadata were removed. Code cells retain order, with original/public hashes and changes recorded per cell.
Set SHROOM_PROJECT_ROOT to your checkout root before running parameterized notebooks/scripts; the default is the working directory.
GOOGLE_APPLICATION_CREDENTIALS, GOOGLE_CLOUD_PROJECT and AZURE_OPENAI_BASE_URL are supplied externally for historical API paths. No actual credential filename, project or endpoint is bundled.
SHROOM_DIAGNOSTIC_REQUEST supplies the private request document for historical diagnostic report generators that require it.
Scientific hyperparameters, model revisions, fold IDs and scoring algorithms were not refactored.
Historical manifests retain original artifact hashes. Public derivatives have separate hashes. Frozen reproduction may require the originals and external artifacts; do not relabel a sanitized file with an original hash.
No training, inference, package installation, model download or paid call occurred in this phase. Historical source can perform these operations if executed; no notebook was run.
