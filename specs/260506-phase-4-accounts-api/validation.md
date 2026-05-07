# Phase 4 — Accounts API: Validation Criteria

## Definition of Done

Phase 4 is complete and ready to merge when **all** of the following pass.

---

## 1. Router Registration

- [x] `backend/app/routers/accounts.py` exists
- [x] Router is registered in `app/main.py` with no prefix
- [x] `GET /openapi.json` includes all five account endpoints with tag `accounts`

---

## 2. Account List & Filtering

- [x] `GET /accounts` returns `200` with a list of account objects (each includes `tag_ids`)
- [x] `GET /accounts?status=active` returns only accounts with `status="active"`
- [x] `GET /accounts?status=closed` returns only accounts with `status="closed"`
- [x] `GET /accounts?tag=<id>` returns only accounts associated with that tag
- [x] `GET /accounts?status=active&tag=<id>` returns only accounts matching both conditions
- [x] With no query params, all accounts are returned

---

## 3. Account Create

- [x] `POST /accounts` with valid body returns `201` with all fields, including `tag_ids`
- [x] Omitting `status` from the body creates an account with `status="active"`
- [x] `POST /accounts` with a duplicate `name` returns `409`
- [x] `POST /accounts` with a nonexistent `institution_id` returns `404`
- [x] `POST /accounts` with a nonexistent `currency_code` returns `404`
- [x] `POST /accounts` with a nonexistent id in `tag_ids` returns `404`
- [x] `POST /accounts` with valid `tag_ids` returns those ids in the response `tag_ids` list

---

## 4. Account Get

- [x] `GET /accounts/{id}` returns `200` with all fields for an existing account
- [x] `GET /accounts/{id}` returns `404` for an unknown id

---

## 5. Account Update

- [x] `PUT /accounts/{id}` with `{"name": "New Name"}` returns `200` with updated `name`; other fields unchanged
- [x] `PUT /accounts/{id}` with `{"status": "closed"}` returns `200` with updated `status`; other fields unchanged
- [x] `PUT /accounts/{id}` with `{"tag_ids": [<new_id>]}` replaces existing tags; old tags gone, new tags present
- [x] `PUT /accounts/{id}` without `tag_ids` field leaves existing tags unchanged
- [x] `PUT /accounts/{id}` with a colliding `name` returns `409`
- [x] `PUT /accounts/{id}` for an unknown id returns `404`

---

## 6. Account Delete

**Dry-run (no `confirm` param):**
- [x] `DELETE /accounts/{id}` (no param) returns `200` with `{"balances_to_delete": 0}` when account has no balances
- [x] `DELETE /accounts/{id}` (no param) returns `200` with correct non-zero count when balances exist
- [x] No data is modified during a dry-run (account still retrievable after)
- [x] Returns `404` for an unknown id

**Destructive (`?confirm=true`):**
- [x] `DELETE /accounts/{id}?confirm=true` returns `204`
- [x] After confirm-delete: `GET /accounts/{id}` returns `404`
- [x] After confirm-delete: all `Balance` rows for the account are gone (verified via direct session query)
- [x] After confirm-delete: all `AccountTag` rows for the account are gone (verified via direct session query)
- [x] After confirm-delete: associated `Tag` rows still exist (tag itself not deleted)
- [x] Returns `404` for an unknown id even with `?confirm=true`

---

## 7. Test Suite

- [x] `just test` exits `0` with all tests passing
- [x] Phases 1–3 tests (≥ 52) + Phase 4 tests all pass together with no regressions (77 total)
- [x] Phase 4 test count: **24 new tests** (1 list + 7 create + 2 get + 6 update + 5 delete + 3 filter)
- [x] No test hits a real database file; all use the in-memory SQLite fixture from `conftest.py`
- [x] No test depends on seed data or the dev `.env`
- [x] `test_delete_account_confirm` verifies `Balance` and `AccountTag` rows are gone via direct `session` query
- [x] `test_delete_account_confirm_leaves_tag` verifies the `Tag` row survives after account deletion
- [x] `test_update_account_tags_none_leaves_unchanged` verifies that omitting `tag_ids` in PUT does not clear tags

---

## 8. Code Quality

- [x] `just lint` passes (`ruff check` and `ruff format --check`)
- [x] `just typecheck` passes with no mypy errors
- [x] All request/response bodies are typed Pydantic models (no plain `dict` returns)
- [x] No SQLModel table class is used directly as a request body
- [x] `just check` (lint + typecheck + test) exits `0`
