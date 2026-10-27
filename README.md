# CRM ETL Toolkit

Clean CRM exports, derive contact-quality features, and train or run a local lead classifier with Python and FastAPI.

Use it when you need to turn CSV or Excel lead exports into a consistent dataset before analysis or CRM import. The local workflow runs without a CRM account, API key, GPU, or cloud service.

## Run an offline example

Use Python 3.10 or newer. From the repository root:

```bash
git clone https://github.com/yuri-rod/crm-etl-toolkit.git
cd crm-etl-toolkit
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r crm-etl/requirements-prod.txt
python crm-etl/examples/offline_demo.py --output cleaned-leads.csv
```

On Windows, activate the environment with `.venv\Scripts\activate`.

The example creates three synthetic records in a temporary directory, runs the same ETL class as the API, and keeps the newer of two records sharing a CPF. Its output includes:

```text
Input: 3 rows; output: 2 leads
cpf,email,data_quality_score
00123456789,new@example.com,2
00987654321,two@example.com,2
Saved: cleaned-leads.csv
```

The output includes all cleaned columns and derived features. The example refuses to overwrite an existing file. Omit `--output` to inspect the result without saving it.

## Local API and command line

```bash
python crm-etl/start_crm_system.py --test
python crm-etl/start_crm_system.py --dev
```

The launcher starts `crm-etl/backend/api_server.py` on `http://127.0.0.1:8000`. Open `/docs` for the request schemas, or check `curl http://127.0.0.1:8000/health`. It can be invoked from another directory using its absolute path.

The API accepts multipart uploads at `POST /pipeline/execute` with `mode=train` or `mode=batch-predict`. It returns a job ID; inspect `/pipeline/status/{pipeline_id}` and retrieve completed results from `/download/{pipeline_id}`. Each upload gets a unique ID. Invalid modes, unsupported input extensions, and filenames containing directories are rejected before writing a file. `/admin/cleanup` removes files only for recorded, completed or failed jobs at least two days old.

The same pipeline is available directly:

```bash
python crm-etl/backend/unificado.py train --data leads.csv --model-dir ./my-model
python crm-etl/backend/unificado.py batch-predict --data new-leads.csv --model-dir ./my-model --output predictions.csv
```

Training requires a `qualidade_lead` target column, or `--target` to choose another. Positive labels are `alta`, `sim`, `1`, and `high`, case insensitive; other values map to the negative class. Use data representing both classes. Predictions require a model you trained and trust. A failed command exits nonzero. Prediction output replaces the file named by `--output`, so choose a new path when preserving a previous result.

## What the pipeline does

- Reads CSV with comma, semicolon, pipe, or tab separators, plus Excel files. UTF-8 and Latin encodings are attempted for CSV.
- Preserves CSV CPF/CNPJ fields as text, including leading zeroes. Excel identifiers should already be stored as text.
- Deduplicates on the first CPF column, or the first CNPJ column if no CPF exists. A date column is used to retain the newest record; without one, input order decides. Rows missing the selected identifier are removed.
- Derives name length, email/LinkedIn/WhatsApp presence, and a contact-data score. Missing optional contact columns produce empty values, not a failed pipeline. Presence checks do not establish that a contact is valid or reachable.
- Trains a scikit-learn preprocessing and RandomForest pipeline, saves it with metadata, and produces batch predictions. Training preserves the caller's original labels.

The implementation is in [`crm-etl/backend/unificado.py`](crm-etl/backend/unificado.py). [`api_server.py`](crm-etl/backend/api_server.py) provides upload, job status, download, and cleanup endpoints. The [offline example](crm-etl/examples/offline_demo.py) shows the ETL path without model training or external enrichment.

## Tests and development

```bash
python -m pip install pytest httpx
python -m pytest crm-etl/tests/test_etl_pipeline.py crm-etl/tests/test_local_workflow.py crm-etl/www/tests/test_unified_crm_pipeline_load_data.py crm-etl/www/tests/test_cleaning_transformation_scoring.py crm-etl/www/tests/test_export_import_roundtrip.py -q
python -m compileall -q crm-etl bkp-pipeline crm-pipelines
```

[Local workflow tests](crm-etl/tests/test_local_workflow.py) cover isolated uploads, bounded cleanup, invalid input, launcher paths, CLI failures, identifier preservation, training, and HTTP result download. The existing backend suites cover CSV/Excel loading, transformations, model persistence, and export round trips. Tests use temporary files, synthetic data, and mocked enrichment. CI runs these suites on Python 3.10 and 3.12 with read-only repository permissions.

See [test scope and commands](crm-etl/tests/README.md) for the distinction between application tests and older live-server, browser, and extractor experiments. To contribute, reproduce the issue with a failing test against the application, apply the smallest fix, and run the relevant suite. Do not commit CRM exports, credentials, or generated models.

## Operating boundaries

Keep the API on localhost for trusted local use. It has no authentication, accepts a local model directory, and keeps job status in memory. Restarting the process loses that status; it does not resume interrupted work. Run one server process and use separate model directories for independent training jobs. The current background task executes synchronous processing in that process.

Only load trusted model files: `joblib` deserialization can execute code. Enrichment is off by default; `--enrich` or the API's enrichment flag makes external ReceitaWS requests. AI rule generation requires separately configured provider dependencies and credentials. Neither is needed for the offline workflow. Tiny training sets may be evaluated on their training data, so those scores are not evidence of predictive quality.

## Repository map

| Path | Purpose |
| --- | --- |
| `crm-etl/backend/`, `crm-etl/start_crm_system.py` | Local API, CLI, and pipeline covered above |
| `crm-etl/www/` | Earlier dashboard and backend variants; selected tests exercise the maintained backend |
| `crm-etl/extractors/` | Separate extractor experiment with missing `etl` package dependencies |
| `crm-pipelines/`, `bkp-pipeline/` | Historical cleaning, analytics, migration, and deployment scripts |
| `crm-etl/main.py`, `crm-etl/README.md` | Original attributed weather ETL tutorial, separate from the CRM workflow |
| `docs/` | Earlier project presentation |

The dashboard, deployment scripts, external integrations, and legacy variants are outside the local test command above. Their historical instructions are not the quickstart for this workflow.

## License

MIT. See [LICENSE](LICENSE). Existing attribution in the tutorial and historical material is retained.
