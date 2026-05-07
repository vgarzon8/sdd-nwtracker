# Phase 3 — Reference Data API: Implementation Plan

## Group 1 — Router Scaffolding

1. Create `backend/app/routers/currencies.py` — empty router, `APIRouter(tags=["currencies"])`
2. Create `backend/app/routers/tags.py` — empty router, `APIRouter(tags=["tags"])`
3. Create `backend/app/routers/institutions.py` — empty router, `APIRouter(tags=["institutions"])`
4. Register all three routers in `backend/app/main.py` (no prefix; import and `app.include_router(...)`)

## Group 2 — Currency Endpoints

5. Define `CurrencyCreate` and `CurrencyRead` Pydantic models in `currencies.py`
6. `GET /currencies` — query all `Currency` rows, return `list[CurrencyRead]`
7. `POST /currencies` — insert new `Currency`; return `201 CurrencyRead`; raise `409` on duplicate code
8. `GET /currencies/{code}` — fetch by PK; raise `404` if missing; return `CurrencyRead`
9. `DELETE /currencies/{code}` — check for referencing `Account` or `ExchangeRate` rows; raise `409` if any exist; otherwise delete and return `204`

## Group 3 — Tag Endpoints

10. Define `TagCreate`, `TagRead`, and `TagUpdate` Pydantic models in `tags.py`
11. `GET /tags` — query all `Tag` rows, return `list[TagRead]`
12. `POST /tags` — insert new `Tag`; return `201 TagRead`; raise `409` on duplicate name
13. `GET /tags/{id}` — fetch by PK; raise `404` if missing; return `TagRead`
14. `PUT /tags/{id}` — update `name`; raise `404` if missing, `409` on name collision; return `TagRead`
15. `DELETE /tags/{id}` — delete all `AccountTag` rows for this tag, then delete `Tag`; raise `404` if tag missing; return `204`

## Group 4 — Institution Endpoints

16. Define `InstitutionCreate`, `InstitutionRead`, `InstitutionUpdate`, and `InstitutionDeletePreview` Pydantic models in `institutions.py`
17. `GET /institutions` — query all `Institution` rows, return `list[InstitutionRead]`
18. `POST /institutions` — insert new `Institution`; return `201 InstitutionRead`; raise `409` on duplicate name
19. `GET /institutions/{id}` — fetch by PK; raise `404` if missing; return `InstitutionRead`
20. `PUT /institutions/{id}` — update `name`; raise `404` if missing, `409` on name collision; return `InstitutionRead`
21. `DELETE /institutions/{id}` (dry-run, no `confirm` param):
    - Raise `404` if institution missing
    - Count affected accounts and their balances
    - Return `200 InstitutionDeletePreview`
22. `DELETE /institutions/{id}?confirm=true` (destructive):
    - Raise `404` if institution missing
    - Delete all `Balance` rows for affected accounts
    - Delete all `AccountTag` rows for affected accounts
    - Delete all `Account` rows for this institution
    - Delete the `Institution` row
    - Return `204 No Content`

    Note: implement steps 21 and 22 as a single endpoint handler using an optional `confirm: bool = False` query parameter.

## Group 5 — Tests

23. Create `backend/tests/test_currencies.py`:
    - `test_list_currencies_empty` — GET returns `[]`
    - `test_create_currency` — POST 201, body matches input
    - `test_create_currency_duplicate` — second POST with same code returns 409
    - `test_get_currency` — create then GET by code; 200
    - `test_get_currency_not_found` — GET unknown code; 404
    - `test_delete_currency` — create, delete; 204; subsequent GET returns 404
    - `test_delete_currency_blocked_by_account` — seed account with currency; DELETE returns 409
    - `test_delete_currency_not_found` — 404

24. Create `backend/tests/test_tags.py`:
    - `test_list_tags_empty`
    - `test_create_tag` — POST 201
    - `test_create_tag_duplicate` — 409
    - `test_get_tag` — 200
    - `test_get_tag_not_found` — 404
    - `test_update_tag` — PUT returns updated name
    - `test_update_tag_not_found` — 404
    - `test_update_tag_duplicate_name` — 409
    - `test_delete_tag` — 204; GET returns 404
    - `test_delete_tag_clears_account_tag` — seed account+tag association; delete tag; confirm account still exists, account_tag row is gone
    - `test_delete_tag_not_found` — 404

25. Create `backend/tests/test_institutions.py`:
    - `test_list_institutions_empty`
    - `test_create_institution` — POST 201
    - `test_create_institution_duplicate` — 409
    - `test_get_institution` — 200
    - `test_get_institution_not_found` — 404
    - `test_update_institution` — PUT returns updated name
    - `test_update_institution_not_found` — 404
    - `test_update_institution_duplicate_name` — 409
    - `test_delete_institution_dry_run_no_accounts` — `{"accounts_to_delete": 0, "balances_to_delete": 0}`
    - `test_delete_institution_dry_run_with_accounts` — seed accounts+balances; verify counts
    - `test_delete_institution_confirm` — `?confirm=true`; 204; institution + accounts + balances + account_tags all gone
    - `test_delete_institution_not_found` — 404 on both dry-run and confirm paths
