# Phase 4 — Accounts API: Validation Criteria

## Definition of Done

Phase 4 is complete and ready to merge when **all** of the following pass.

---

## 1. Router Registration

- [ ] `backend/app/routers/accounts.py` exists
- [ ] Router is registered in `app/main.py` with no prefix
- [ ] `GET /openapi.json` includes all five account endpoints with tag `accounts`

---

## 2. Account List & Filtering

- [ ] `GET /accounts` returns `200` with a list of account objects (each includes `tag_ids`)
- [ ] `GET /accounts?status=active` returns only accounts with `status="active"`
- [ ] `GET /accounts?status=closed` returns only accounts with `status="closed"`
- [ ] `GET /accounts?tag=<id>` returns only accounts associated with that tag
- [ ] `GET /accounts?status=active&tag=<id>` returns only accounts matching both conditions
- [ ] With no query params, all accounts are returned

---

## 3. Account Create

- [ ] `POST /accounts` with valid body returns `201` with all fields, including `tag_ids`
- [ ] Omitting `status` from the body creates an account with `status="active"`
- [ ] `POST /accounts` with a duplicate `name` returns `409`
- [ ] `POST /accounts` with a nonexistent `institution_id` returns `404`
- [ ] `POST /accounts` with a nonexistent `currency_code` returns `404`
- [ ] `POST /accounts` with a nonexistent id in `tag_ids` returns `404`
- [ ] `POST /accounts` with valid `tag_ids` returns those ids in the response `tag_ids` list

---

## 4. Account Get

- [ ] `GET /accounts/{id}` returns `200` with all fields for an existing account
- [ ] `GET /accounts/{id}` returns `404` for an unknown id

---

## 5. Account Update

- [ ] `PUT /accounts/{id}` with `{"name": "New Name"}` returns `200` with updated `name`; other fields unchanged
- [ ] `PUT /accounts/{id}` with `{"status": "closed"}` returns `200` with updated `status`; other fields unchanged
- [ ] `PUT /accounts/{id}` with `{"tag_ids": [<new_id>]}` replaces existing tags; old tags gone, new tags present
- [ ] `PUT /accounts/{id}` without `tag_ids` field leaves existing tags unchanged
- [ ] `PUT /accounts/{id}` with a colliding `name` returns `409`
- [ ] `PUT /accounts/{id}` for an unknown id returns `404`

---

## 6. Account Delete

**Dry-run (no `confirm` param):**
- [ ] `DELETE /accounts/{id}` (no param) returns `200` with `{"balances_to_delete": 0}` when account has no balances
- [ ] `DELETE /accounts/{id}` (no param) returns `200` with correct non-zero count when balances exist
- [ ] No data is modified during a dry-run (account still retrievable after)
- [ ] Returns `404` for an unknown id

**Destructive (`?confirm=true`):**
- [ ] `DELETE /accounts/{id}?confirm=true` returns `204`
- [ ] After confirm-delete: `GET /accounts/{id}` returns `404`
- [ ] After confirm-delete: all `Balance` rows for the account are gone (verified via direct session query)
- [ ] After confirm-delete: all `AccountTag` rows for the account are gone (verified via direct session query)
- [ ] After confirm-delete: associated `Tag` rows still exist (tag itself not deleted)
- [ ] Returns `404` for an unknown id even with `?confirm=true`

---

## 7. Test Suite

- [ ] `just test` exits `0` with all tests passing
- [ ] Phases 1–3 tests (≥ 52) + Phase 4 tests all pass together with no regressions
- [ ] Phase 4 test count: at least **20 new tests** (1 list + 7 create + 2 get + 6 update + 5 delete + 3 filter)
- [ ] No test hits a real database file; all use the in-memory SQLite fixture from `conftest.py`
- [ ] No test depends on seed data or the dev `.env`
- [ ] `test_delete_account_confirm` verifies `Balance` and `AccountTag` rows are gone via direct `session` query
- [ ] `test_delete_account_confirm_leaves_tag` verifies the `Tag` row survives after account deletion
- [ ] `test_update_account_tags_none_leaves_unchanged` verifies that omitting `tag_ids` in PUT does not clear tags

---

## 8. Code Quality

- [ ] `just lint` passes (`ruff check` and `ruff format --check`)
- [ ] `just typecheck` passes with no mypy errors
- [ ] All request/response bodies are typed Pydantic models (no plain `dict` returns)
- [ ] No SQLModel table class is used directly as a request body
- [ ] `just check` (lint + typecheck + test) exits `0`
