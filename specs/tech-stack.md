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
| UI framework       | React 18+               |                                                                       |
| Routing            | React Router v6         |                                                                       |
| Styling            | Tailwind CSS            | Utility-first; no custom CSS files except global resets               |
| Component library  | shadcn/ui               | Accessible, unstyled components built on Radix UI + Tailwind          |
| Data fetching      | TanStack Query (React Query) | Server state management; handles caching and invalidation        |
| HTTP client        | Axios or fetch          | Thin wrapper over FastAPI REST endpoints                              |

## Infrastructure

| Concern            | Choice                  | Notes                                                                 |
|--------------------|-------------------------|-----------------------------------------------------------------------|
| Containerization   | Docker                  | Separate `Dockerfile` for backend and frontend                        |
| Orchestration      | Docker Compose          | `compose.yml` at repo root runs the full stack locally                |
| DB persistence     | Named volume            | SQLite file mounted as a Docker volume so data survives container restarts |

## Key Conventions

- **Base currency:** USD. All exchange rates are expressed as `1 USD = X units of foreign currency`.
- **Amounts as integers:** Balance amounts are stored as whole currency units (e.g., whole USD). No floating-point arithmetic for balances.
- **Month format:** `YYYY-MM` strings throughout (stored in DB, used in API, displayed in UI).
- **API style:** RESTful JSON API. Frontend and backend are separate processes in development; served from the same origin in production.
- **No build-time secrets:** All configuration via environment variables or `.env` files.

## Project Layout (target)

```
nwtracker/
  compose.yml             # runs backend + frontend together
  backend/
    Dockerfile
    pyproject.toml        # uv-managed Python project
    .env                  # local config (gitignored)
    app/
      main.py             # FastAPI app entry point
      config.py           # env var loading
      models/             # SQLModel table definitions
      routers/            # FastAPI routers, one per domain
      services/           # Business logic (balance roll-forward, reports, etc.)
      db.py               # DB engine and session dependency
  frontend/
    Dockerfile
    package.json
    vite.config.ts
    src/
      main.tsx
      App.tsx
      components/         # shadcn/ui and custom components
      pages/              # One file per route
      api/                # API client functions
  specs/                  # This directory
```
