# Phase 2 — FastAPI Skeleton & Config: Requirements

## Scope

Stand up a running FastAPI application with environment-based config, structured file logging, and a health endpoint. No domain routers yet — this phase delivers the application shell that all future phases will build on.

## Out of Scope

- Any domain routers (currencies, accounts, balances, etc.) — those are Phase 3+
- Database initialization on startup — `init_db()` remains a manual `just db-init` step; the app fails fast if tables are missing
- Frontend / Vite proxy — Phase 9
- Docker / Compose — production concern; dev runs directly with `uv`

---

## New Dependencies

| Package | Kind | Purpose |
|---------|------|---------|
| `fastapi[standard]` | runtime | Web framework; `[standard]` bundles `uvicorn`, `python-multipart`, `email-validator` |
| `httpx` | dev | Required by FastAPI `TestClient` for integration tests |

`fastapi[standard]` replaces the need to list `uvicorn` separately — it is included transitively.

---

## Configuration

Extend `app/config.py` with the following new variables (all read from `.env`, all have defaults):

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Python logging level name (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `LOG_FILE` | `logs/nwtracker.log` | Path to log file, relative to `backend/` |
| `LOG_MAX_BYTES` | `10485760` | Rotate log when it reaches this size (10 MB) |
| `LOG_BACKUP_COUNT` | `5` | Number of rotated backup files to keep |

`APP_VERSION` is not an env var — it is read at import time from `importlib.metadata.version("nwtracker")` so it always matches `pyproject.toml`.

`.env.sample` must be updated to document all four new variables.

---

## Application Entry Point (`app/main.py`)

- Create `backend/app/main.py` as the FastAPI application module.
- Remove the `uv init` stub `backend/main.py` (it was never committed; ensure it is not imported or referenced).
- The app is created with `title`, `description`, and `version` pulled from config/metadata.
- Logging is configured once at module load time (not inside a lifespan or endpoint), using a `RotatingFileHandler` plus a `StreamHandler` (so logs appear in both the file and stdout during dev).
- Log directory is created automatically (`mkdir -p`) when `app/main.py` is first imported.
- No lifespan hook needed for this phase — `init_db()` is not called on startup.

---

## `GET /health` Endpoint

**Happy path (DB accessible):**

```
GET /health
→ 200 OK
{
  "status": "ok",
  "db": "ok",
  "version": "0.1.0"
}
```

**Degraded path (DB raises):**

```
GET /health
→ 503 Service Unavailable
{
  "status": "degraded",
  "db": "error"
}
```

Implementation notes:
- Opens a DB session via `get_session()` and executes `SELECT 1` to verify connectivity.
- Catches any `Exception` from the DB check; on failure returns 503 with `status: "degraded"`.
- `version` field is omitted from the 503 response (only present on 200).
- Response is typed with a Pydantic model (`HealthResponse`) so the shape is documented in OpenAPI.

---

## Logging

- Handler: `RotatingFileHandler` — rotates when file exceeds `LOG_MAX_BYTES`, keeps `LOG_BACKUP_COUNT` backups.
- Second handler: `StreamHandler` to stdout.
- Format: `%(asctime)s %(levelname)s %(name)s — %(message)s`
- Root logger level: `LOG_LEVEL` from config.
- Log directory (`dirname(LOG_FILE)`) is created with `mkdir -p` before the handler is instantiated.
- File path is resolved relative to `backend/` (same anchor as `config.py`: `Path(__file__).resolve().parent.parent`).

---

## OpenAPI Docs

FastAPI exposes `/docs` (Swagger UI) and `/redoc` automatically. No additional configuration required. Both endpoints should be accessible when the dev server is running.

---

## Justfile

Add a `dev` recipe to `justfile`:

```
dev:
    uv run --project {{backend}} uvicorn app.main:app --reload --app-dir {{backend}}
```

The `--app-dir` flag tells uvicorn to add `backend/` to `sys.path` so `app.main` resolves correctly when invoked from the repo root.

---

## Key Decisions

- **`fastapi[standard]`** — bundles uvicorn; keeps the dependency list short and ensures version compatibility between FastAPI and its ASGI server.
- **DB check via `SELECT 1`** — lightweight, uses the existing `get_session()` / engine path, exercises the full connection stack without touching any domain tables.
- **`version` absent from 503** — keeps the degraded response minimal; the app may not be fully initialized.
- **Logging at import time** — simpler than a lifespan hook; acceptable because there is no teardown required for file handlers in a single-process dev server.
- **`APP_VERSION` from `importlib.metadata`** — stays in sync with `pyproject.toml` automatically; no separate env var to keep updated.
