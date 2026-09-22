# CK Personal Finance

This directory is the standalone repository root for the private money cockpit. Run commands here. It contains the FastAPI server, PostgreSQL store, cockpit SPA, tests and historical story-flow generators.

## Run locally

Use Python 3.12 or newer and PostgreSQL with pgvector available. Install into a dedicated virtual environment:

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
```

Set `PF_DATABASE_URL` to the approved PostgreSQL database connection string in the process environment. `PERSONAL_FINANCE_DATABASE_URL` remains an alternative. There is no default password or SQLite fallback. Startup creates the cockpit tables and synthetic example records; use a dedicated database, not an unrelated application's database. The role must be able to initialise the schema and use the `vector` extension in `public`.

Configure `FINANCE_AUTH_USERNAME` and `FINANCE_AUTH_PASSWORD_HASH` as described in [AUTHENTICATION.md](AUTHENTICATION.md). The inherited `FINANCE_AUTH_*` names are retained for compatibility. Authentication fails closed when missing. Environment variables must be set by the launcher; this app does not load `.env` files automatically.

```powershell
.venv/Scripts/python -m uvicorn server:app --host 127.0.0.1 --port 5124
```

Open `/` for the cockpit, `/api/health` for health, and `/docs` for the API. Assets are served under `/static`. External model calls and live bank connections remain disabled. Uploads stay under this repository's `uploads/personal-finance/user-provided` directory. Existing databases and uploads were not moved by the source extraction.

## Test against PostgreSQL

Set `TEST_DATABASE_URL` to a local, dedicated database named `finance_test`, with pgvector installed in `public`. Tests create and remove only their own random schemas. Upload fixtures use temporary directories; source indexing is empty unless a test explicitly supplies a source.

```powershell
.venv/Scripts/python -m pytest tests/test_personal_finance.py -q
.venv/Scripts/python -m pytest tests -q
```

The cockpit file contains nine tests. The full suite also retains credential, upload, startup, preview and source-path checks from the extraction. No adjacent repository or parent checkout is needed.

## Historical story-flow tools

Install the optional `docs` dependencies to run `tools/build_ck_personal_finance_story_flow_v0_4.py`, `tools/build_ck_personal_finance_story_flow_v0_5.py` or `tools/build_ckpf_story_doc.py`. Outputs go beneath this repository's `reports` directory. These generators preserve historical product narratives; their deployment, provider and QA claims are not current runtime evidence. Referenced historical screenshots are optional and are not part of this extraction.
