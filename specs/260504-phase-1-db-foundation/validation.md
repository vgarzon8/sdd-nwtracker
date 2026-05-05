# Phase 1 — DB Foundation: Validation Criteria

## Definition of Done

Phase 1 is complete and ready to merge when **all** of the following pass.

---

## 1. Project Scaffold

- [ ] `backend/pyproject.toml` exists and is valid (`uv sync` succeeds with no errors)
- [ ] `sqlmodel` and `python-dotenv` appear in runtime dependencies
- [ ] `pytest`, `ruff`, and `mypy` appear in dev dependencies
- [ ] `[tool.ruff]` and `[tool.mypy]` sections present in `pyproject.toml`
- [ ] `justfile` exists at repo root with recipes: `db-init`, `db-seed`, `test`, `lint`, `typecheck`
- [ ] `backend/.env` exists locally (gitignored; not committed)

## 2. DB Init Script

- [ ] `uv run db-init` runs without error on a clean environment
- [ ] After running, `backend/nwtracker.db` exists and contains all expected tables:
  - `currency`, `tag`, `institution`, `account`, `accounttag`, `balance`, `exchangerate`
- [ ] Re-running `uv run db-init` on an existing DB does not raise an error (idempotent via `checkfirst=True` or equivalent)

## 3. Seed Script

- [ ] `uv run db-seed` runs without error after `db-init`
- [ ] After seeding, querying the DB returns:
  - 3 currencies (USD, CNY, CHF)
  - 4 tags (retirement, brokerage, checking, savings)
  - 4 institutions
  - 5 accounts with correct side, status, and currency
  - At least 1 account–tag association per tagged account
  - Balances for 2 months for all 5 accounts (10 rows total)
  - 4 exchange rate rows (2 currencies × 2 months)
- [ ] Re-running `uv run db-seed` does not duplicate rows (insert-or-ignore / upsert)

## 4. Model Constraints

Verified via pytest tests:

- [ ] Inserting a duplicate `currency.code` raises an integrity error
- [ ] Inserting a duplicate `tag.name` raises an integrity error
- [ ] Inserting a duplicate `(account_id, month)` balance raises an integrity error
- [ ] Inserting a duplicate `(currency_code, month)` exchange rate raises an integrity error
- [ ] Inserting an account with a non-existent `institution_id` raises an integrity error
- [ ] Inserting an account with a non-existent `currency_code` raises an integrity error

## 5. Exchange Rate Precision

- [ ] A rate of `7.1` is stored and retrieved as `7.1000` (4 decimal places, no float drift)
- [ ] A rate of `0.9150` round-trips exactly

## 6. Test Suite

- [ ] `just test` exits 0 with all tests passing
- [ ] Tests use an in-memory SQLite DB — no file created, no cleanup needed
- [ ] No test depends on seed data or the dev `.env`

## 7. Code Quality

- [ ] `just lint` passes with no errors (`ruff check` and `ruff format --check`)
- [ ] `just typecheck` passes with no mypy errors
- [ ] All models importable from `app.models` without circular imports
- [ ] `app/db.py` `get_session()` is a generator suitable for FastAPI `Depends()` (even though FastAPI is not wired up yet)
