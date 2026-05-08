# Tech Stack

## Backend

| Concern            | Choice                  | Notes                                                                 |
|--------------------|-------------------------|-----------------------------------------------------------------------|
| Language           | Python 3.12+            |                                                                       |
| Package manager    | uv                      | Handles virtualenv, lockfile, and script runner                       |
| Web framework      | FastAPI                 | Async, automatic OpenAPI docs at `/docs`                              |
| ORM / DB layer     | SQLModel                | Combines SQLAlchemy + Pydantic; integrates cleanly with FastAPI       |
| Database           | SQLite                  | Single local file; path configured via environment variable           |
| Config             | python-dotenv           | Reads `.env` file; env vars override for production-like environments |
| Logging            | Python `logging` stdlib | File-based with rotation; level configurable via env                  |
| Testing            | pytest                  | Integration-focused; tests run against a real SQLite DB, minimal mocking |

## Frontend

| Concern            | Choice                  | Notes                                                                 |
|--------------------|-------------------------|-----------------------------------------------------------------------|
| Language           | TypeScript              |                                                                       |
| Build tool         | Vite                    | Fast dev server and build; proxies API calls to FastAPI in dev        |
| UI framework       | React 19                |                                                                       |
| Routing            | React Router v7         |                                                                       |
| Styling            | Tailwind CSS v4         | Utility-first; integrated via `@tailwindcss/vite` plugin (no PostCSS); CSS custom properties in `src/index.css` |
| Component library  | shadcn/ui               | Accessible, unstyled components built on Radix UI + Tailwind          |
| Data fetching      | TanStack Query (React Query) | Server state management; handles caching and invalidation        |
| HTTP client        | fetch                   | Thin wrapper in `src/api/`; base URL `/api`, proxied to FastAPI in dev |
| Linter             | ESLint                  | Ships with Vite `react-ts` template; extended with `typescript-eslint`, `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh` |
| Formatter          | Prettier                | `prettier` + `eslint-config-prettier`; `.prettierrc` at `frontend/` root |

## AI / Generative Features

| Concern              | Choice                        | Notes                                                                                      |
|----------------------|-------------------------------|--------------------------------------------------------------------------------------------|
| AI provider          | Configurable                  | Supports Anthropic Claude, OpenAI, and Ollama (local); selected and keyed at setup via env |
| Anthropic SDK        | `anthropic` (Python)          | Used when provider is Claude                                                               |
| OpenAI SDK           | `openai` (Python)             | Used when provider is OpenAI; also used for Ollama (OpenAI-compatible API)                 |
| Interaction pattern  | Tool use / function calling   | AI calls structured tools to query the DB; never receives a raw DB dump                    |
| Write access         | Propose + confirm             | AI proposes data changes; user sees a diff and approves before any write is committed      |
| Conversation history | SQLite (optional)             | Chat history stored in a `conversations` table; user can enable/disable in settings        |
| AI features          | Chat assistant, anomaly/trend alerts, monthly narrative report, smart CSV import assistance | |

### AI Tool Surface

The assistant is given a set of callable tools backed by the existing API layer:

- `get_net_worth(month)` — assets, liabilities, net worth for a month
- `get_accounts(filters)` — list accounts with optional tag/status filters
- `get_balances(month, account_id?)` — balance data for a month
- `get_trends(months)` — net worth and balance history over a range of months
- `propose_balance_update(account_id, month, amount)` — returns a diff for user confirmation
- `propose_account_update(account_id, fields)` — returns a diff for user confirmation

### AI Provider Configuration

Configured via environment variables:

```
AI_PROVIDER=claude          # claude | openai | ollama
AI_MODEL=claude-opus-4-6    # model name, provider-specific
AI_API_KEY=sk-...           # not required for ollama
AI_BASE_URL=                # override for ollama or proxies
AI_HISTORY_ENABLED=true     # persist conversation history
```

## Developer Tools

| Concern          | Choice | Notes                                                                                  |
|------------------|--------|----------------------------------------------------------------------------------------|
| Command runner        | just | `justfile` at repo root; covers both backend (`test`, `lint`, `typecheck`, `dev`) and frontend (`frontend-dev`, `frontend-lint`, `frontend-typecheck`, `frontend-format`) |
| Linter/formatter (BE) | ruff | Replaces flake8 + black; configured in `pyproject.toml`                                |
| Type checker (BE)     | mypy | Static type checking for Python; configured in `pyproject.toml`                        |

## Infrastructure

| Concern            | Choice                  | Notes                                                                 |
|--------------------|-------------------------|-----------------------------------------------------------------------|
| Containerization   | Docker                  | Separate `Dockerfile` for backend and frontend                        |
| Orchestration      | Docker Compose          | `compose.yml` at repo root runs the full stack locally                |
| DB persistence     | Named volume            | `data/` at repo root mounted as a Docker volume; SQLite file at `data/sqlite/nwtracker.db` |

## Key Conventions

- **Base currency:** USD. All exchange rates are expressed as `1 USD = X units of foreign currency` (e.g., 7.1 CNY per USD is stored as `7.1000`).
- **Exchange rate precision:** Stored as a fixed-point decimal with 4 decimal places (`Numeric(10, 4)` in SQLAlchemy). No floating-point arithmetic for rates.
- **Amounts as integers:** Balance amounts are stored as whole currency units (e.g., whole USD). No floating-point arithmetic for balances.
- **Month format:** `YYYY-MM` strings throughout (stored in DB, used in API, displayed in UI).
- **API style:** RESTful JSON API. Frontend and backend are separate processes in development; served from the same origin in production.
- **No build-time secrets:** All configuration via environment variables or `.env` files. `.env` files are gitignored; each service includes a `.env.sample` documenting all required variables.

## Project Layout (target)

```
nwtracker/
  compose.yml             # runs backend + frontend together
  justfile                # common dev tasks (db-init, db-seed, test, dev, etc.)
  data/                   # gitignored; all local data files
    sqlite/
      nwtracker.db        # SQLite database (default location)
  backend/
    Dockerfile
    pyproject.toml        # uv-managed Python project
    .env                  # local config (gitignored; never committed)
    .env.sample           # template with all required variables (committed)
    app/
      main.py             # FastAPI app entry point
      config.py           # env var loading
      models/             # SQLModel table definitions
      routers/            # FastAPI routers, one per domain
      services/           # Business logic (balance roll-forward, reports, etc.)
      ai/                 # AI assistant: provider client, tool definitions, conversation service
      db.py               # DB engine and session dependency
  frontend/
    Dockerfile            # (planned; not yet implemented)
    package.json
    vite.config.ts        # Tailwind v4 plugin + /api proxy + @/* alias
    eslint.config.js      # ESLint flat config with typescript-eslint + prettier
    components.json       # shadcn/ui config
    .prettierrc           # Prettier options
    index.html
    src/
      main.tsx            # Entry: QueryClientProvider wraps App
      App.tsx             # createBrowserRouter route definitions
      index.css           # Tailwind @import + shadcn CSS custom properties
      components/         # Shared layout (AppLayout, Sidebar) and UI components
      pages/              # One file per route
      api/                # fetch wrapper (client.ts) and per-resource query fns
      lib/                # Utilities: cn() helper (utils.ts)
  specs/                  # This directory
```
