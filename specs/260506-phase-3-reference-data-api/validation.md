# Phase 3 — Reference Data API: Validation Criteria

## Definition of Done

Phase 3 is complete and ready to merge when **all** of the following pass.

---

## 1. Router Registration

- [x] `backend/app/routers/currencies.py`, `tags.py`, and `institutions.py` exist
- [x] All three routers are registered in `app/main.py` with no prefix
- [x] `GET /openapi.json` includes all endpoints from this phase with correct tags (`currencies`, `tags`, `institutions`)

---

## 2. Currency Endpoints

- [x] `GET /currencies` returns `200` with a list of currency objects
- [x] `POST /currencies` with `{"code": "EUR", "name": "Euro"}` returns `201` with the created object
- [x] `POST /currencies` with a duplicate code returns `409`
- [x] `GET /currencies/{code}` returns `200` for an existing currency
- [x] `GET /currencies/{code}` returns `404` for an unknown code
- [x] `DELETE /currencies/{code}` returns `204` when no accounts or exchange rates reference it
- [x] `DELETE /currencies/{code}` returns `409` when at least one account references the currency
- [x] `DELETE /currencies/{code}` returns `404` for an unknown code

---

## 3. Tag Endpoints

- [x] `GET /tags` returns `200` with a list of tag objects (each has `id` and `name`)
- [x] `POST /tags` with `{"name": "retirement"}` returns `201` with `id` and `name`
- [x] `POST /tags` with a duplicate name returns `409`
- [x] `GET /tags/{id}` returns `200` for an existing tag
- [x] `GET /tags/{id}` returns `404` for an unknown id
- [x] `PUT /tags/{id}` with a new name returns `200` with updated `name`
- [x] `PUT /tags/{id}` with a name that already belongs to another tag returns `409`
- [x] `PUT /tags/{id}` for an unknown id returns `404`
- [x] `DELETE /tags/{id}` returns `204`
- [x] After `DELETE /tags/{id}`, `GET /tags/{id}` returns `404`
- [x] After `DELETE /tags/{id}`, all `account_tag` rows for that tag are removed; the associated accounts still exist and are queryable (verified by direct DB query in test)
- [x] `DELETE /tags/{id}` returns `404` for an unknown id

---

## 4. Institution Endpoints

- [x] `GET /institutions` returns `200` with a list of institution objects
- [x] `POST /institutions` returns `201` with `id` and `name`
- [x] `POST /institutions` with a duplicate name returns `409`
- [x] `GET /institutions/{id}` returns `200` for an existing institution
- [x] `GET /institutions/{id}` returns `404` for an unknown id
- [x] `PUT /institutions/{id}` with a new name returns `200` with updated name
- [x] `PUT /institutions/{id}` with a colliding name returns `409`
- [x] `PUT /institutions/{id}` for an unknown id returns `404`

**Dry-run delete (no `confirm` param):**
- [x] `DELETE /institutions/{id}` (no param) returns `200` with `{"accounts_to_delete": 0, "balances_to_delete": 0}` when the institution has no accounts
- [x] `DELETE /institutions/{id}` (no param) returns `200` with correct non-zero counts when accounts (and balances) exist
- [x] No data is modified during a dry-run
- [x] Returns `404` for an unknown id

**Destructive delete (`?confirm=true`):**
- [x] `DELETE /institutions/{id}?confirm=true` returns `204`
- [x] After confirm-delete: `GET /institutions/{id}` returns `404`
- [x] After confirm-delete: all accounts that belonged to the institution are gone (verified in test)
- [x] After confirm-delete: all balances for those accounts are gone
- [x] After confirm-delete: all `account_tag` rows for those accounts are gone
- [x] Returns `404` for an unknown id even with `?confirm=true`

---

## 5. Test Suite

- [x] `just test` exits `0` with all tests passing
- [x] Phase 1 (17) + Phase 2 (4) + Phase 3 tests all pass together
- [x] Phase 3 test count: at least 8 currency tests + 11 tag tests + 12 institution tests = **31 new tests** (total ≥ 52)
- [x] No test hits a real database file; all use the in-memory SQLite fixture from `conftest.py`
- [x] No test depends on seed data or the dev `.env`
- [x] The `test_delete_tag_clears_account_tag` test verifies account survival explicitly (not just absence of the tag row)
- [x] The `test_delete_institution_confirm` test verifies balances and account_tag rows are removed via direct session query

---

## 6. Code Quality

- [x] `just lint` passes (`ruff check` and `ruff format --check`)
- [x] `just typecheck` passes with no mypy errors
- [x] All request/response bodies are typed Pydantic models (no plain `dict` returns)
- [x] No SQLModel table class is used directly as a request body
- [x] `just check` (lint + typecheck + test) exits `0`
