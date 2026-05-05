# Phase 1 — DB Foundation: Implementation Plan

## Group 1 — Project Scaffold

1. Run `uv init backend` at repo root to create `backend/` with `pyproject.toml` and `.python-version`
2. Add runtime deps: `sqlmodel`, `python-dotenv`
3. Add dev deps: `pytest`, `ruff`, `mypy`
4. Configure `ruff` in `pyproject.toml` (`[tool.ruff]`): enable `E`, `F`, `I` rule sets; set `line-length = 88`
5. Configure `mypy` in `pyproject.toml` (`[tool.mypy]`): `strict = true`, `plugins = ["sqlmodel.main"]` if available
6. Create `justfile` at repo root with recipes: `db-init`, `db-seed`, `test`, `lint`, `typecheck`
7. Create `backend/.env` (gitignored) with `DATABASE_URL=sqlite:///./nwtracker.db`
8. Create `backend/app/__init__.py` (empty)
9. Create `backend/app/config.py` — loads `DATABASE_URL` from `.env` via `python-dotenv`

## Group 2 — Data Models

10. Create `backend/app/models/__init__.py`
11. Create `backend/app/models/currency.py` — `Currency` SQLModel table
12. Create `backend/app/models/tag.py` — `Tag` SQLModel table
13. Create `backend/app/models/institution.py` — `Institution` SQLModel table
14. Create `backend/app/models/account.py` — `AccountSide` enum, `AccountStatus` enum, `AccountTag` join table, `Account` SQLModel table (FKs to Institution, Currency)
15. Create `backend/app/models/balance.py` — `Balance` SQLModel table (FK to Account, composite unique on `account_id` + `month`)
16. Create `backend/app/models/exchange_rate.py` — `ExchangeRate` SQLModel table (`Numeric(10,4)` rate, composite unique on `currency_code` + `month`)
17. Export all models from `backend/app/models/__init__.py` so `create_all` sees them

## Group 3 — DB Engine & Session

18. Create `backend/app/db.py`:
    - Create SQLAlchemy engine from `DATABASE_URL`
    - `init_db()` function: calls `SQLModel.metadata.create_all(engine)`
    - `get_session()` generator (for future FastAPI dependency injection)

## Group 4 — CLI Scripts

19. Create `backend/scripts/db_init.py` — calls `init_db()`; register as `[project.scripts] db-init = "scripts.db_init:main"`
20. Create `backend/scripts/db_seed.py` — inserts seed fixtures idempotently (insert-or-ignore); register as `db-seed`

## Group 5 — Tests

21. Create `backend/tests/__init__.py`
22. Create `backend/tests/conftest.py` — pytest fixture that creates an in-memory SQLite DB (`sqlite://`) and yields a session; tears down after each test
23. Create `backend/tests/test_models.py` — smoke tests:
    - Tables created without error
    - Seed data round-trips (insert + query)
    - Composite unique constraints raise on duplicate
    - FK violations raise on bad references
