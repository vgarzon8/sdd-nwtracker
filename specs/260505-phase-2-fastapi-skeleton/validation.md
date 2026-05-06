# Phase 2 — FastAPI Skeleton & Config: Validation Criteria

## Definition of Done

Phase 2 is complete and ready to merge when **all** of the following pass.

---

## 1. Dependencies & Config

- [x] `fastapi[standard]` appears in runtime dependencies in `pyproject.toml`
- [x] `httpx` appears in dev dependencies in `pyproject.toml`
- [x] `uv sync` succeeds with no errors
- [x] `app/config.py` exports `LOG_LEVEL`, `LOG_FILE`, `LOG_MAX_BYTES`, `LOG_BACKUP_COUNT`, and `APP_VERSION`
- [x] `backend/.env.sample` documents all four new log-related variables with their defaults

## 2. Application Startup

- [x] `just dev` starts the server without error (uvicorn output visible on stdout)
- [x] Server is reachable at `http://localhost:8000`
- [x] `backend/main.py` stub is absent (deleted or never existed in working tree)

## 3. Health Endpoint

- [x] `GET /health` returns `200 OK` with body `{"status": "ok", "db": "ok", "version": "<x.y.z>"}`
- [x] `version` value matches the version string in `backend/pyproject.toml`
- [x] `GET /health` returns `503 Service Unavailable` with body `{"status": "degraded", "db": "error"}` when DB is unreachable
- [x] 503 response body does **not** contain a `version` key

## 4. OpenAPI Docs

- [x] `GET /docs` returns `200 OK` (Swagger UI) when server is running
- [x] `GET /redoc` returns `200 OK` when server is running
- [x] `/health` endpoint and its response schemas appear in the OpenAPI spec at `/openapi.json`

## 5. Logging

- [x] After `just dev` starts, a log file is created at the path specified by `LOG_FILE` (default: `backend/logs/nwtracker.log`)
- [x] Log entries appear in the file in the format `%(asctime)s %(levelname)s %(name)s — %(message)s`
- [x] Setting `LOG_LEVEL=DEBUG` in `.env` causes debug-level messages to appear
- [x] `backend/logs/` is listed in `.gitignore`

## 6. Test Suite

- [x] `just test` exits 0 with all tests passing (Phase 1's 17 + Phase 2's 4 = 21 total)
- [x] `test_health_ok` — asserts 200, `status == "ok"`, `db == "ok"`, `version` non-empty
- [x] `test_health_ok_response_schema` — asserts response has exactly keys `status`, `db`, `version`
- [x] `test_health_db_error` — asserts 503, `status == "degraded"`, `db == "error"`
- [x] `test_health_db_error_no_version` — asserts `version` key absent from 503 response
- [x] No test starts a real server or creates any files on disk

## 7. Code Quality

- [x] `just lint` passes with no errors (`ruff check` and `ruff format --check`)
- [x] `just typecheck` passes with no mypy errors
- [x] `HealthOkResponse` and `HealthDegradedResponse` are typed Pydantic models (not plain dicts)
