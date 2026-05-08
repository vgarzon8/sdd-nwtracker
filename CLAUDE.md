# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Spec-Driven Development

All feature work follows a spec-driven process. Before writing code for a new phase, read the relevant spec files.

### Constitution files (`specs/`)

These files define the project's guiding principles and must be respected at all times:

- `specs/mission.md` — Purpose, target user, core values, and explicit scope boundaries (what the app does and does not do)
- `specs/tech-stack.md` — Canonical technology choices, key conventions (month format, integer amounts, exchange rate precision, API style), and the target project layout
- `specs/roadmap.md` — Ordered list of phases; each phase is a self-contained deliverable that leaves the project in a working state

Before making architectural decisions or technology choices, verify they are consistent with `mission.md` and `tech-stack.md`. Do not introduce technologies or patterns not listed there without explicit discussion.

### Phase spec directories (`specs/<date>-phase-N-<slug>/`)

Each completed or in-progress phase has a directory containing:
- `plan.md` — Implementation steps and approach
- `requirements.md` — Functional requirements and acceptance criteria
- `validation.md` — Checklist confirming the phase is complete

When starting a new phase, use the `/feature-spec` skill, which reads the roadmap, creates the branch, interviews for scope, and writes the three spec files before any code is written.

## Commands

All dev commands run through `just` (the justfile at the project root):

```bash
just dev          # Start FastAPI dev server (auto-reload, port 8000)
just test         # Run all tests
just test <path>  # Run specific test file or function, e.g. just test backend/tests/test_accounts.py::test_create_account
just lint         # ruff check + format check
just format       # Auto-format with ruff
just typecheck    # mypy strict mode
just check        # Run test + lint + typecheck (CI equivalent)
just db-init      # Create SQLite schema
just db-seed      # Populate sample data
```

## Architecture

**nwtracker** is a local-first personal net worth tracker. Currently backend-only (phases 1–6 complete); frontend is planned for a later phase.

**Stack:** Python 3.12+, FastAPI, SQLModel (SQLAlchemy + Pydantic), SQLite, managed by `uv`.

**Backend layout (`backend/`):**
- `app/models/` — SQLModel table definitions: `Currency`, `Institution`, `Account`, `AccountTag`, `Balance`, `ExchangeRate`
- `app/routers/` — One file per resource, registered in `main.py`
- `app/db.py` — Engine, `init_db()`, and `get_session()` dependency
- `app/config.py` — Loads `.env` from the backend directory; exports `DATABASE_URL`, log settings, `APP_VERSION`
- `scripts/` — `db_init.py` and `db_seed.py` (called via `uv run`)
- `tests/` — pytest integration tests; `conftest.py` provides `session` (in-memory SQLite) and `client` (TestClient with overridden DB dependency)

**Key domain rules:**
- Month format is always `YYYY-MM`
- Amounts are integer whole-currency units (no fractional cents)
- Exchange rates are `Decimal(10, 4)` stored as CNY-per-USD (or X-per-USD)
- Base currency is USD; all net worth is normalized to USD
- Cascade-delete endpoints require `?confirm=true` and return a preview without it

**API docs:** `http://localhost:8000/docs` (Swagger) and `/redoc` when the dev server is running.

