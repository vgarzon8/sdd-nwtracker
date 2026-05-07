# Roadmap

Each phase is a small, self-contained unit of work with a clear deliverable. Phases build on each other but each one leaves the project in a working state.

---

## Phase 1 — DB Foundation [X]

**Deliverable:** SQLite database initialized with all tables and seed data. No API or UI yet.

- Initialize `uv` project under `backend/`
- Define SQLModel models for all entities: `Currency`, `Tag`, `Institution`, `Account`, `Balance`, `ExchangeRate`
- Wire up DB engine and session management (`db.py`)
- Write a `db init` script to create all tables
- Write seed data fixtures for local development (a few currencies, institutions, accounts, balances)

---

## Phase 2 — FastAPI Skeleton & Config [X]

**Deliverable:** A running FastAPI server with health endpoint, logging, and environment-based config.

- Set up `FastAPI` app in `app/main.py`
- Load config from `.env` via `python-dotenv` (DB path, log level, log file path, rotation settings)
- Configure file-based logging with rotation (`RotatingFileHandler`) and stdout echo
- Add `GET /health` endpoint (200 with DB check + version; 503 on DB failure)
- Add OpenAPI docs available at `/docs` and `/redoc`
- Add `just dev` recipe to run the uvicorn dev server

---

## Phase 3 — Reference Data API (Currencies, Tags, Institutions) [X]

**Deliverable:** Full CRUD REST endpoints for currencies, tags, and institutions.

- `GET/POST /currencies`, `GET/DELETE /currencies/{code}`
- `GET/POST /tags`, `GET/PUT/DELETE /tags/{id}`
- `GET/POST /institutions`, `GET/PUT/DELETE /institutions/{id}`
- Cascade delete: deleting an institution cascades to its accounts (with a `confirm` query param)
- Integration tests covering happy paths and constraint violations

---

## Phase 4 — Accounts API [X]

**Deliverable:** Full CRUD for accounts, including tag association.

- `GET/POST /accounts`, `GET/PUT/DELETE /accounts/{id}`
- Filter by `status` and `tag` on list endpoint
- Cascade delete: deleting an account cascades to its balances (with `confirm` query param)
- Account name uniqueness enforced at DB level
- Integration tests

---

## Phase 5 — Balances API [X]

**Deliverable:** CRUD for balances, roll-forward, and transfer endpoints.

- `GET/POST /balances`, `GET/PUT/DELETE /balances/{id}`
- `GET /balances?month=YYYY-MM` — list balances for a month with account details and category summaries
- `POST /balances/roll-forward` — copy last month's balances to a new month for all active accounts (insert-or-ignore)
- `POST /balances/transfer` — apply a transfer between two accounts for a given month
- Integration tests for roll-forward idempotency and transfer accounting logic

---

## Phase 6 — Exchange Rates API [ ]

**Deliverable:** CRUD for exchange rates.

- `GET/POST /exchange-rates`, `GET/PUT/DELETE /exchange-rates/{id}`
- Filter by currency and/or month on list endpoint
- Composite unique constraint enforced: `(currency_code, month)`
- Integration tests

---

## Phase 7 — Reports API [ ]

**Deliverable:** Net worth snapshot report endpoint.

- `GET /reports/net-worth?month=YYYY-MM`
  - Returns: total assets, total liabilities, net worth (all in base currency USD)
  - Per-account detail with currency, original amount, and USD-equivalent
- Integration tests

---

## Phase 8 — CSV Import & Export [ ]

**Deliverable:** Idempotent CSV import and full CSV export.

- `POST /import` — populate DB from a set of named CSV files; validates data integrity; safe to re-run
- `GET /export` — export all tables to CSV (zipped or individual files)
- CSV format documented in `specs/csv-format.md`
- Integration tests for idempotency and round-trip (export → import)

---

## Phase 9 — Frontend Scaffold [ ]

**Deliverable:** React app running in dev with routing and API client wired up to the backend.

- Initialize Vite + React + TypeScript project under `frontend/`
- Install and configure Tailwind CSS and shadcn/ui
- Install React Router v6 and TanStack Query
- Set up Vite proxy to forward `/api/*` to FastAPI dev server
- Define route structure (placeholder pages for each section)
- Shared layout: sidebar navigation, header

---

## Phase 10 — Reference Data UI (Currencies, Tags, Institutions) [ ]

**Deliverable:** List and CRUD forms for currencies, tags, and institutions.

- Institutions: list, create, edit, delete (with cascade confirmation)
- Tags: list, create, edit, delete
- Currencies: list, create, delete

---

## Phase 11 — Accounts UI [ ]

**Deliverable:** Account list and CRUD forms.

- List view with filter by status and tag
- Create/edit form: name, institution, currency, side (asset/liability), status, tags
- Delete with cascade confirmation

---

## Phase 12 — Balance Entry UI [ ]

**Deliverable:** Monthly balance entry and roll-forward workflow.

- Month selector
- Balance list for selected month: account name, institution, balance, currency
- Inline edit for individual balance amounts
- Roll-forward action: copy previous month to current month
- Transfer form between two accounts

---

## Phase 13 — Reports UI [ ]

**Deliverable:** Net worth dashboard.

- Month selector
- Summary cards: total assets, total liabilities, net worth
- Breakdown table by account with currency and USD equivalent
- (Optional stretch) Sparkline or simple chart of net worth over trailing months

---

## Phase 14 — Import / Export UI [ ]

**Deliverable:** CSV import and export accessible from the browser.

- Export: button to download all tables as CSV (or zip)
- Import: file upload form; shows validation errors and import summary

---

## Phase 15 — AI Foundation [ ]

**Deliverable:** Configurable AI provider wired into the backend; tool framework in place; no UI yet.

- Add `anthropic` and `openai` Python SDK dependencies
- Implement provider abstraction layer in `app/ai/`: selects Claude, OpenAI, or Ollama based on `AI_PROVIDER` env var
- Define and register the core tool set (read-only tools first): `get_net_worth`, `get_accounts`, `get_balances`, `get_trends`
- Add `conversations` table to DB (session id, role, content, timestamp); enabled by `AI_HISTORY_ENABLED` env var
- `POST /ai/chat` endpoint: accepts a message, runs tool-use loop, returns assistant reply + any tool calls made
- Integration tests using a stubbed provider (no real API calls in CI)

---

## Phase 16 — AI Write Tools & Confirmation Flow [ ]

**Deliverable:** Assistant can propose data changes; backend returns structured diffs for user confirmation.

- Add write tools: `propose_balance_update`, `propose_account_update`
- Write tools do **not** commit; they return a structured `Proposal` object (what would change)
- Add `POST /ai/confirm` endpoint: accepts a proposal id and applies the change after user approval
- Proposals are short-lived (in-memory or TTL'd in DB); never auto-applied
- Integration tests for the full propose → confirm → verify cycle

---

## Phase 17 — Chat Assistant UI [ ]

**Deliverable:** Persistent chat panel in the frontend; user can converse with the assistant.

- Sidebar or slide-over drawer: always accessible, collapsible
- Message thread: user messages, assistant replies, tool-call summaries (e.g., "I looked up your March balances")
- Input box with submit; streaming responses if the provider supports it
- Proposal cards: when assistant proposes a change, show a diff card with Approve / Reject buttons
- Conversation history toggle in settings (calls `AI_HISTORY_ENABLED` config)

---

## Phase 18 — Anomaly & Trend Alerts [ ]

**Deliverable:** AI scans each month's balances and surfaces notable changes.

- Backend job / endpoint `POST /ai/analyze-month?month=YYYY-MM`: runs after balance entry is complete
- Detects: large balance swings (configurable threshold), net worth direction changes, accounts with no update
- Returns structured alerts with plain-language descriptions
- Alerts displayed in the balance entry UI and/or a dedicated Alerts panel
- User can dismiss individual alerts; dismissed state stored in DB

---

## Phase 19 — Monthly Narrative Report [ ]

**Deliverable:** AI generates a written summary of the month's financial picture.

- `POST /ai/narrative?month=YYYY-MM`: assembles month data, calls AI, returns markdown narrative
- Narrative covers: net worth vs prior month, biggest movers, notable trends, any active alerts
- Displayed on the Reports page alongside the numerical summary
- Narrative is cached in DB per month (regenerable on demand)

---

## Phase 20 — Smart CSV Import Assistance [ ]

**Deliverable:** AI helps the user map and clean CSV data during import.

- During import, if column headers or values are ambiguous, the backend calls AI to suggest mappings
- AI returns a proposed mapping (e.g., "column 'bal' → `amount`") with confidence; user can accept or override
- Validation errors are explained in plain language ("Row 12 has a non-numeric amount: 'n/a'")
- UI shows the AI-suggested mapping as an editable table before the import is committed
