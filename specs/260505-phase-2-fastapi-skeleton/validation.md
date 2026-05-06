# Phase 2 — FastAPI Skeleton & Config: Validation Criteria

## Definition of Done

Phase 2 is complete and ready to merge when **all** of the following pass.

---

## 1. Dependencies & Config

- [ ] `fastapi[standard]` appears in runtime dependencies in `pyproject.toml`
- [ ] `httpx` appears in dev dependencies in `pyproject.toml`
- [ ] `uv sync` succeeds with no errors
- [ ] `app/config.py` exports `LOG_LEVEL`, `LOG_FILE`, `LOG_MAX_BYTES`, `LOG_BACKUP_COUNT`, and `APP_VERSION`
- [ ] `backend/.env.sample` documents all four new log-related variables with their defaults

## 2. Application Startup

- [ ] `just dev` starts the server without error (uvicorn output visible on stdout)
- [ ] Server is reachable at `http://localhost:8000`
- [ ] `backend/main.py` stub is absent (deleted or never existed in working tree)

## 3. Health Endpoint

- [ ] `GET /health` returns `200 OK` with body `{"status": "ok", "db": "ok", "version": "<x.y.z>"}`
- [ ] `version` value matches the version string in `backend/pyproject.toml`
- [ ] `GET /health` returns `503 Service Unavailable` with body `{"status": "degraded", "db": "error"}` when DB is unreachable
- [ ] 503 response body does **not** contain a `version` key

## 4. OpenAPI Docs

- [ ] `GET /docs` returns `200 OK` (Swagger UI) when server is running
- [ ] `GET /redoc` returns `200 OK` when server is running
- [ ] `/health` endpoint and its response schemas appear in the OpenAPI spec at `/openapi.json`

## 5. Logging

- [ ] After `just dev` starts, a log file is created at the path specified by `LOG_FILE` (default: `backend/logs/nwtracker.log`)
- [ ] Log entries appear in the file in the format `%(asctime)s %(levelname)s %(name)s — %(message)s`
- [ ] Setting `LOG_LEVEL=DEBUG` in `.env` causes debug-level messages to appear
- [ ] `backend/logs/` is listed in `.gitignore`

## 6. Test Suite

- [ ] `just test` exits 0 with all tests passing (Phase 1's 17 + Phase 2's 4 = 21 total)
- [ ] `test_health_ok` — asserts 200, `status == "ok"`, `db == "ok"`, `version` non-empty
- [ ] `test_health_ok_response_schema` — asserts response has exactly keys `status`, `db`, `version`
- [ ] `test_health_db_error` — asserts 503, `status == "degraded"`, `db == "error"`
- [ ] `test_health_db_error_no_version` — asserts `version` key absent from 503 response
- [ ] No test starts a real server or creates any files on disk

## 7. Code Quality

- [ ] `just lint` passes with no errors (`ruff check` and `ruff format --check`)
- [ ] `just typecheck` passes with no mypy errors
- [ ] `HealthOkResponse` and `HealthDegradedResponse` are typed Pydantic models (not plain dicts)
