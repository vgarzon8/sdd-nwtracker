# Phase 2 — FastAPI Skeleton & Config: Implementation Plan

## Group 1 — Dependencies & Config

1. Add `fastapi[standard]` to runtime dependencies in `backend/pyproject.toml` (`uv add fastapi[standard]`)
2. Add `httpx` to dev dependencies (`uv add --dev httpx`)
3. Extend `backend/app/config.py` — add `LOG_LEVEL`, `LOG_FILE`, `LOG_MAX_BYTES`, `LOG_BACKUP_COUNT`, and `APP_VERSION` (from `importlib.metadata`)
4. Update `backend/.env.sample` with the four new env vars and their defaults

## Group 2 — Application & Logging Setup

5. Create `backend/app/routers/__init__.py` (empty — establishes the routers package for future phases)
6. Create `backend/app/main.py`:
   - Configure root logger with `RotatingFileHandler` + `StreamHandler` using format and levels from config; create log directory with `mkdir -p`
   - Instantiate `FastAPI(title=..., version=APP_VERSION)` app
7. Delete the `uv init` stub `backend/main.py` (untracked; was never committed — confirm it is absent or remove it)

## Group 3 — Health Endpoint

8. Create `backend/app/routers/health.py`:
   - Define `HealthOkResponse` and `HealthDegradedResponse` Pydantic models
   - Implement `GET /health`: open a session, execute `SELECT 1`, return 200 `HealthOkResponse` on success or 503 `HealthDegradedResponse` on any exception
9. Register the health router on the app in `main.py` (no prefix — endpoint lives at `/health`)

## Group 4 — Tests

10. Create `backend/tests/test_health.py` using `fastapi.testclient.TestClient`:
    - `test_health_ok` — client gets `/health`, asserts 200, `status == "ok"`, `db == "ok"`, `version` is a non-empty string
    - `test_health_ok_response_schema` — asserts response JSON has exactly the keys `status`, `db`, `version` (no extras)
    - `test_health_db_error` — override `get_session` dependency to raise `RuntimeError`; assert 503, `status == "degraded"`, `db == "error"`
    - `test_health_db_error_no_version` — same override; assert `version` key is absent from the 503 response

## Group 5 — Justfile & Cleanup

11. Add `dev` recipe to `justfile`:
    ```
    dev:
        uv run --project {{backend}} uvicorn app.main:app --reload --app-dir {{backend}}
    ```
12. Add `backend/logs/` to `.gitignore` (log files must not be committed)
13. Run `just lint` and `just typecheck` — fix any issues before committing
