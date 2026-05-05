# Phase 1 — DB Foundation: Implementation Plan

## Group 1 — Project Scaffold

1. Run `uv init backend` at repo root to create `backend/` with `pyproject.toml` and `.python-version`
2. Add runtime deps: `sqlmodel`, `python-dotenv`
3. Add dev deps: `pytest`, `ruff`, `mypy`
4. Configure `ruff` in `pyproject.toml` (`[tool.ruff]`): enable `E`, `F`, `I` rule sets; set `line-length = 88`
5. Configure `mypy` in `pyproject.toml` (`[tool.mypy]`): `strict = true`, `plugins = ["pydantic.mypy"]` (SQLModel has no mypy plugin; Pydantic's is used instead)
6. Add `[tool.uv] package = true` and `[tool.setuptools.packages.find] include = ["app*", "scripts*"]` so entry points are installed and setuptools doesn't pick up stray directories
7. Create `justfile` at repo root with recipes: `db-init`, `db-seed`, `test`, `lint`, `typecheck`; all paths prefixed with `backend/` so recipes work from repo root
8. Create `backend/.env.sample` (committed) with all required variables and placeholder values; copy to `backend/.env` locally (gitignored)
9. Create `backend/app/__init__.py` (empty)
10. Create `backend/app/config.py` — loads `.env` from `backend/` relative to `__file__` (not CWD) so entry points work from any working directory; exposes `DATABASE_URL`

## Group 2 — Data Models

11. Create `backend/app/models/__init__.py`
12. Create `backend/app/models/currency.py` — `Currency` SQLModel table
13. Create `backend/app/models/tag.py` — `Tag` SQLModel table
14. Create `backend/app/models/institution.py` — `Institution` SQLModel table
15. Create `backend/app/models/account.py` — `AccountSide` enum, `AccountStatus` enum, `Account` SQLModel table (FKs to Institution, Currency), `AccountTag` join table
16. Create `backend/app/models/balance.py` — `Balance` SQLModel table (FK to Account, composite unique on `account_id` + `month`)
17. Create `backend/app/models/exchange_rate.py` — `ExchangeRate` SQLModel table (`Numeric(10,4)` rate, composite unique on `currency_code` + `month`)
18. Export all models from `backend/app/models/__init__.py` so `create_all` sees them

## Group 3 — DB Engine & Session

19. Create `backend/app/db.py`:
    - Engine from `DATABASE_URL` with `check_same_thread=False`
    - `PRAGMA foreign_keys=ON` via `event.listens_for` on every connection
    - `init_db()`: `mkdir -p` data dir, then `SQLModel.metadata.create_all(engine)`
    - `get_session()` generator suitable for FastAPI `Depends()`

## Group 4 — CLI Scripts

20. Create `backend/scripts/__init__.py` (empty — makes `scripts` importable as a package)
21. Create `backend/scripts/db_init.py` — imports `app.models` for side-effect registration, calls `init_db()`; registered as `db-init` entry point
22. Create `backend/scripts/db_seed.py` — idempotent seed via `session.merge()`; registered as `db-seed` entry point

## Group 5 — Tests

23. Create `backend/tests/__init__.py`
24. Create `backend/tests/conftest.py` — per-test in-memory SQLite fixture with `PRAGMA foreign_keys=ON`; creates and drops all tables around each test
25. Create `backend/tests/test_models.py` — 17 tests:
    - Round-trips for all 6 models
    - Unique constraint violations (currency PK, tag name, account name, balance composite, exchange rate composite)
    - FK violations (account → institution, account → currency, exchange rate → currency)
    - Exchange rate decimal precision: `7.1000` and `0.9150` round-trip exactly
