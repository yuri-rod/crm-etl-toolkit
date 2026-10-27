# CRM ETL tests

The local suites exercise the maintained `crm-etl/backend/` pipeline and API with synthetic data. No CRM account, paid API, or running server is required.

From the repository root:

```bash
python -m pip install -r crm-etl/requirements-prod.txt pytest httpx
python -m pytest crm-etl/tests/test_etl_pipeline.py crm-etl/tests/test_local_workflow.py crm-etl/www/tests/test_unified_crm_pipeline_load_data.py crm-etl/www/tests/test_cleaning_transformation_scoring.py crm-etl/www/tests/test_export_import_roundtrip.py -q
```

| Suite | What it checks |
| --- | --- |
| `test_local_workflow.py` | Application upload isolation, cleanup ownership, invalid requests, launcher paths, nonzero CLI failures, identifier preservation, training, download, and the offline example |
| `www/tests/test_unified_crm_pipeline_load_data.py` | CSV delimiters/encodings, Excel loading, and invalid formats |
| `www/tests/test_cleaning_transformation_scoring.py` | Cleaning, feature extraction, mocked enrichment, training, and model persistence |
| `www/tests/test_export_import_roundtrip.py` | CSV/Excel output and prediction round trips |
| `test_etl_pipeline.py` | Standalone pandas transformation examples implemented inside that test module |

The last suite is retained as an example; its success alone does not verify the application. CI runs all five suites on Python 3.10 and 3.12, plus syntax compilation and a secret-pattern check. No deployment is part of this workflow.

## Other tests

`test_backend_endpoints.py` targets a live server. `test_frontend_links.py` and `www/tests/e2e/` check older dashboard layouts and require their documented browser/server setup. They are not included in the local application suite.

`test_extractors.py` imports an `etl` package and schema classes that are not present in this tree. The extractor framework is a separate experiment, not the loader used by `UnifiedCRMPipeline`. Its collection failure remains unresolved; do not treat the entire `tests/` directory as a passing suite.

Run tests from a disposable checkout when changing recovery or file operations. Use temporary model directories and synthetic inputs. Add regressions against application code before changing behavior; keep external enrichment mocked. Model evaluation on synthetic or training data is not a benchmark of real lead quality.

## Existing notice

Part of CRM ETL ETL system. All rights reserved.
