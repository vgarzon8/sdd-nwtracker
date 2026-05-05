# Phase 1 — DB Foundation: Validation Criteria

## Definition of Done

Phase 1 is complete and ready to merge when **all** of the following pass.

---

## 1. Project Scaffold

- [x] `backend/pyproject.toml` exists and is valid (`uv sync` succeeds with no errors)
- [x] `sqlmodel` and `python-dotenv` appear in runtime dependencies
- [x] `pytest`, `ruff`, and `mypy` appear in dev dependencies
- [x] `[tool.ruff]` and `[tool.mypy]` sections present in `pyproject.toml`
- [x] `justfile` exists at repo root with recipes: `db-init`, `db-seed`, `test`, `lint`, `typecheck`
- [x] `backend/.env.sample` is committed and lists all required variables
- [x] `backend/.env` is gitignored and absent from the repository

## 2. DB Init Script

- [x] `just db-init` runs without error on a clean environment
- [x] After running, `data/sqlite/nwtracker.db` exists at the repo root and contains all expected tables:
  - `currency`, `tag`, `institution`, `account`, `accounttag`, `balance`, `exchangerate`
- [x] `data/` is gitignored — the database file is never committed
- [x] Re-running `just db-init` on an existing DB does not raise an error (idempotent via `checkfirst=True` or equivalent)

## 3. Seed Script

- [x] `just db-seed` runs without error after `db-init`
- [x] After seeding, querying the DB returns:
  - 3 currencies (USD, CNY, CHF)
  - 4 tags (retirement, brokerage, checking, savings)
  - 4 institutions
  - 5 accounts with correct side, status, and currency
  - At least 1 account–tag association per tagged account
  - Balances for 2 months for all 5 accounts (10 rows total)
  - 4 exchange rate rows (2 currencies × 2 months)
- [x] Re-running `just db-seed` does not duplicate rows (idempotent via `session.merge()`)

## 4. Model Constraints

Verified via pytest tests:

- [x] Inserting a duplicate `currency.code` raises an integrity error
- [x] Inserting a duplicate `tag.name` raises an integrity error
- [x] Inserting a duplicate `(account_id, month)` balance raises an integrity error
- [x] Inserting a duplicate `(currency_code, month)` exchange rate raises an integrity error
- [x] Inserting an account with a non-existent `institution_id` raises an integrity error
- [x] Inserting an account with a non-existent `currency_code` raises an integrity error

## 5. Exchange Rate Precision

- [x] `Decimal("7.1000")` round-trips exactly: stored and retrieved as `Decimal('7.1000')`
- [x] `Decimal("0.9150")` round-trips exactly: stored and retrieved as `Decimal('0.9150')`

## 6. Test Suite

- [x] `just test` exits 0 with all 17 tests passing
- [x] Tests use an in-memory SQLite DB — no file created, no cleanup needed
- [x] No test depends on seed data or the dev `.env`

## 7. Code Quality

- [x] `just lint` passes with no errors (`ruff check` and `ruff format --check`)
- [x] `just typecheck` passes with no mypy errors
- [x] All models importable from `app.models` without circular imports
- [x] `app/db.py` `get_session()` is a generator suitable for FastAPI `Depends()` (even though FastAPI is not wired up yet)
