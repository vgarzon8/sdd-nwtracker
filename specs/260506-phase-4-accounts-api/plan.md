# Phase 4 — Accounts API: Implementation Plan

## Group 1 — Router Scaffolding

1. Create `backend/app/routers/accounts.py` — empty router, `APIRouter(tags=["accounts"])`
2. Register the router in `backend/app/main.py` (no prefix; import and `app.include_router(...)`)

## Group 2 — Account CRUD Endpoints

3. Define Pydantic models in `accounts.py`:
   - `AccountCreate` — `name`, `institution_id`, `currency_code`, `side`, `status` (default `"active"`), `tag_ids` (default `[]`)
   - `AccountRead` — `id`, `name`, `institution_id`, `currency_code`, `side`, `status`, `tag_ids`
   - `AccountUpdate` — all fields optional; `tag_ids: list[int] | None = None`
   - `AccountDeletePreview` — `balances_to_delete: int`
   - Add a helper `_get_tag_ids(session, account_id) -> list[int]` to fetch current tag associations (used by read and list handlers)

4. `GET /accounts` — query all `Account` rows; apply optional `status` and `tag` query param filters (AND logic if both present); return `list[AccountRead]` with `tag_ids` populated

5. `POST /accounts`:
   - Validate `institution_id` exists; raise `404` if not
   - Validate `currency_code` exists; raise `404` if not
   - Validate each id in `tag_ids` exists; raise `404` if any missing
   - Check name uniqueness; raise `409` on duplicate
   - Insert `Account` row; insert `AccountTag` rows for each tag id
   - Return `201 AccountRead`

6. `GET /accounts/{id}` — fetch by PK; raise `404` if missing; return `AccountRead` with `tag_ids`

7. `PUT /accounts/{id}`:
   - Raise `404` if account missing
   - For each non-`None` field in the body:
     - `name`: check uniqueness (excluding current id); raise `409` if collision
     - `institution_id`: validate exists; raise `404` if not
     - `currency_code`: validate exists; raise `404` if not
     - Apply field update to account row
   - If `tag_ids` is not `None`: delete all existing `AccountTag` rows for this account; validate each new tag id; raise `404` if any missing; insert new `AccountTag` rows
   - Commit; return `200 AccountRead`

8. `DELETE /accounts/{id}` (dry-run + destructive combined handler, `confirm: bool = False`):
   - Raise `404` if account missing
   - Count `Balance` rows for the account
   - If `confirm` is `False`: return `200 AccountDeletePreview`
   - If `confirm` is `True`:
     - Delete all `Balance` rows for the account
     - Delete all `AccountTag` rows for the account
     - `session.flush()` to remove FK children before the account
     - Delete the `Account` row
     - Commit; return `204 No Content`

## Group 3 — Tests

9. Create `backend/tests/test_accounts.py`. All tests use the `client` and `session` fixtures from `conftest.py`; no real DB file; no seed data.

    **Setup helpers** (define as local fixtures or helper functions):
    - `make_currency(client, code="USD")` — POST `/currencies`
    - `make_institution(client, name="Bank A")` — POST `/institutions`
    - `make_tag(client, name="retirement")` — POST `/tags`
    - `make_account(client, **overrides)` — POST `/accounts` with sensible defaults

    **List:**
    - `test_list_accounts_empty` — GET returns `[]`

    **Create:**
    - `test_create_account` — POST 201; response fields match input
    - `test_create_account_default_status` — POST without `status`; response has `status="active"`
    - `test_create_account_duplicate_name` — second POST with same name returns 409
    - `test_create_account_invalid_institution` — nonexistent `institution_id` returns 404
    - `test_create_account_invalid_currency` — nonexistent `currency_code` returns 404
    - `test_create_account_with_tags` — POST with valid `tag_ids`; `tag_ids` appear in response
    - `test_create_account_invalid_tag` — nonexistent id in `tag_ids` returns 404

    **Get:**
    - `test_get_account` — create then GET; 200 with all fields
    - `test_get_account_not_found` — unknown id returns 404

    **Update:**
    - `test_update_account_name` — PUT new name; 200 with updated name
    - `test_update_account_status` — PUT `{"status": "closed"}`; 200 with updated status
    - `test_update_account_tags_replace` — PUT with new `tag_ids`; verifies old tags removed, new tags present
    - `test_update_account_tags_none_leaves_unchanged` — PUT without `tag_ids` field; existing tags remain
    - `test_update_account_not_found` — 404
    - `test_update_account_duplicate_name` — 409

    **Filter:**
    - `test_list_filter_by_status` — create active + closed accounts; filter `status=active`; only active returned
    - `test_list_filter_by_tag` — create two accounts, one with a tag; filter `tag=<id>`; only tagged account returned
    - `test_list_filter_status_and_tag` — both filters combined; only account matching both is returned

    **Delete:**
    - `test_delete_account_dry_run_no_balances` — returns `{"balances_to_delete": 0}`; account still exists after
    - `test_delete_account_dry_run_with_balances` — seed a balance row; returns correct non-zero count
    - `test_delete_account_confirm` — `?confirm=true`; returns 204; subsequent GET returns 404; balance and account_tag rows gone (verified via session query)
    - `test_delete_account_confirm_leaves_tag` — after confirm-delete, the associated `Tag` row still exists
    - `test_delete_account_not_found` — 404 on both dry-run and confirm paths
