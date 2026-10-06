# CRM ETL Toolkit

Lead qualification and CRM ETL toolkit: data extraction, cleaning,
scoring with ML, rule generation, and a Flask/Dash dashboard plus
FastAPI services. Built in Python, with Portuguese-language UI strings.

## Layout

- `crm-etl/` - unified app: extractor framework (`extractors/`), backend
  services (`backend/`, `services/`), web dashboard (`www/`), GPU helpers,
  tests (`tests/`, `www/tests/`), older variants (`legacy/`).
- `crm-pipelines/` - pipeline scripts: cleaners, consolidation,
  Firebase-to-Supabase migration, ETL core.
- `bkp-pipeline/` - pipeline plus ML collection: cleaners, analytics
  engine, Vertex/App Engine deployment, dashboards, examples.
- `docs/` - tool overview deck.

## Quickstart

Requirements: Python 3.10+.

```bash
pip install -r crm-etl/requirements-prod.txt
pip install -r crm-etl/requirements-optional.txt  # AI providers, dev tools
cp crm-etl/.env.example crm-etl/.env  # then set API keys
cd crm-etl
python start_crm_system.py --dev
```

The launcher checks dependencies, verifies backend files, and serves the
API on `http://127.0.0.1:8000` (`/docs` for the OpenAPI UI).

## Configuration

- `crm-etl/.env` - API keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) and
  environment. Never commit real keys; `.env.example` shows the shape.
- `crm-etl/config_exemplo.yaml`, `config_gpu_exemplo.yaml` - pipeline
  config examples.

## Tests

```bash
cd crm-etl
python run_tests.py            # unit/integration suites
python start_crm_system.py --test   # smoke: imports + pipeline wiring
```

Playwright e2e specs live under `www/tests/e2e/` (needs `pip install
playwright` plus `playwright install`). CI runs the self-contained
pipeline suite; backend and frontend suites need a live server.

## Notes

- Sample and test workbooks ship with the tree (`www/test_data/`,
  `output/`); brand art was removed, so the UI references a logo file
  you must supply (`www/static/img/`).
- Four legacy scripts were truncated at the source and are excluded
  from this repo.
- CI runs a syntax compile plus a secret-pattern scan on every push.

## License

MIT, see `LICENSE`.
