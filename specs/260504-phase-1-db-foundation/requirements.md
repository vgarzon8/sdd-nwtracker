# Phase 1 — DB Foundation: Requirements

## Scope

Initialize the Python backend project and define the full SQLite database schema via SQLModel. No API, no UI. Deliverable is a working `db init` command and seed data that can be loaded for local development.

## Out of Scope

- FastAPI app or any HTTP endpoints (Phase 2)
- Alembic / migration tooling — schema is created fresh via `SQLModel.metadata.create_all()`
- Docker (used in production; dev runs directly with `uv`)

---

## Data Models

### `Currency`

| Column | Type | Constraints |
|--------|------|-------------|
| `code` | `str` | PK, e.g. `"USD"`, `"CNY"` |
| `name` | `str` | not null |

### `Tag`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `int` | PK, autoincrement |
| `name` | `str` | unique, not null |

### `Institution`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `int` | PK, autoincrement |
| `name` | `str` | unique, not null |

### `Account`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `int` | PK, autoincrement |
| `name` | `str` | unique, not null |
| `institution_id` | `int` | FK → `institution.id`, not null |
| `currency_code` | `str` | FK → `currency.code`, not null |
| `side` | `str` | `"asset"` or `"liability"` (Enum) |
| `status` | `str` | `"active"` or `"closed"` (Enum) |

Account–Tag association is a many-to-many join table `account_tag` (`account_id`, `tag_id`).

### `Balance`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `int` | PK, autoincrement |
| `account_id` | `int` | FK → `account.id`, not null |
| `month` | `str` | `YYYY-MM` format, not null |
| `amount` | `int` | whole currency units, not null |

Composite unique constraint: `(account_id, month)`.

### `ExchangeRate`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `int` | PK, autoincrement |
| `currency_code` | `str` | FK → `currency.code`, not null |
| `month` | `str` | `YYYY-MM` format, not null |
| `rate` | `Decimal` | `Numeric(10, 4)` — foreign units per 1 USD, e.g. `7.1000` for CNY |

Composite unique constraint: `(currency_code, month)`.

---

## Key Decisions

- **Amount storage:** `int` (whole units). No cents. Aligns with monthly-granularity use case.
- **Account side:** Python `Enum` stored as string column (`"asset"` | `"liability"`). Readable in the raw DB.
- **Account status:** String enum (`"active"` | `"closed"`). No intermediate states.
- **Exchange rate precision:** `Numeric(10, 4)` — 4 decimal places. Represents foreign currency units per 1 USD (e.g., `7.1000` CNY/USD). No float arithmetic.
- **Month format:** `YYYY-MM` string in all tables and throughout the system.
- **Schema creation:** `SQLModel.metadata.create_all()` — no migration tooling in Phase 1.
- **DB path:** Configurable via `DATABASE_URL` env var (loaded from `.env`). Defaults to `backend/nwtracker.db`.

---

## Project Initialization

- `uv init` under `backend/` — creates `pyproject.toml`, `.python-version`, and `.venv`
- Required dependencies: `sqlmodel`, `python-dotenv`
- Dev dependencies: `pytest`
- Entry points:
  - `uv run db-init` — creates all tables
  - `uv run db-seed` — inserts seed fixtures (idempotent)

---

## Seed Data (local development)

Enough data to exercise every table and relationship:

- **Currencies:** USD, CNY, CHF
- **Tags:** retirement, brokerage, checking, savings
- **Institutions:** Chase, Fidelity, ICBC, UBS
- **Accounts:**
  - Chase Checking (USD, asset, active) — tagged: checking
  - Chase Savings (USD, asset, active) — tagged: savings
  - Fidelity 401k (USD, asset, active) — tagged: retirement, brokerage
  - ICBC Savings (CNY, asset, active) — tagged: savings
  - Chase Credit Card (USD, liability, active)
- **Balances** (two months: 2026-03, 2026-04):
  - Representative amounts for each account in each month
- **Exchange Rates:**
  - CNY: 7.1000 for 2026-03, 7.2000 for 2026-04
  - CHF: 0.8900 for 2026-03, 0.8850 for 2026-04
