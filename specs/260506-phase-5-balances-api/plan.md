# Phase 5 — Balances API: Plan

## Task Groups

---

### 1. Balance Router — Core CRUD

**File:** `backend/app/routers/balances.py`

1.1 Define Pydantic schemas: `BalanceCreate`, `BalanceRead`, `BalanceReadDetail` (with account fields), `BalanceUpdate`

1.2 Implement `GET /balances`
- Optional `month: str | None` query param
- If `month` is provided: join with account table, return `BalanceReadDetail` list
- If `month` is omitted: return plain `BalanceRead` list (no join)

1.3 Implement `POST /balances`
- Validate `account_id` exists → 404 if not
- Insert balance; catch unique constraint violation → 409

1.4 Implement `GET /balances/{id}`
- Return `BalanceReadDetail` (always include account context)
- 404 if not found

1.5 Implement `PUT /balances/{id}`
- Accept `BalanceUpdate` (amount only)
- 404 if not found

1.6 Implement `DELETE /balances/{id}`
- 204 on success, 404 if not found

---

### 2. Roll-Forward Endpoint

**File:** `backend/app/routers/balances.py` (same file, added to router)

2.1 Define `RollForwardRequest` (body: `month: str`) and `RollForwardResult` (body: `month`, `inserted`, `skipped`)

2.2 Implement `POST /balances/roll-forward`
- Validate target `month` format
- Query all active accounts
- Find the most recent source month: `SELECT MAX(month) FROM balance WHERE account_id IN (...active account ids...)`
- If no source month found → 422 with message `"No balances found to roll forward from"`
- If source month == target month → 422 with message `"Target month is the same as the source month"`
- For each active account that has a balance in the source month, attempt to insert a balance for the target month with the same amount; skip if `(account_id, target_month)` already exists
- Return `RollForwardResult`

---

### 3. Transfer Endpoint

**File:** `backend/app/routers/balances.py` (same file, added to router)

3.1 Define `TransferRequest` (`from_account_id`, `to_account_id`, `amount: int > 0`, `month: str`) and `TransferResult` (`from_balance: BalanceRead`, `to_balance: BalanceRead`)

3.2 Implement `POST /balances/transfer`
- Validate both accounts exist → 404 if not
- Fetch balance for `from_account_id` at `month` → 422 if missing
- Fetch balance for `to_account_id` at `month` → 422 if missing
- Load account records for both to read `side`
- Apply delta:
  - `from_account` asset: `from_balance.amount -= amount`
  - `from_account` liability: `from_balance.amount += amount`
  - `to_account` asset: `to_balance.amount += amount`
  - `to_account` liability: `to_balance.amount -= amount`
- Commit; return `TransferResult`

---

### 4. Router Registration

**File:** `backend/app/main.py`

4.1 Import `balances` router and add `app.include_router(balances.router)`

---

### 5. Tests

**File:** `backend/tests/test_balances.py`

Use `_make_currency`, `_make_institution`, `_make_account` helpers (mirroring existing test files). Add a `_make_balance` helper.

**CRUD**
5.1 `test_list_balances_empty` — GET /balances returns []
5.2 `test_create_balance` — POST creates a balance, 201, fields match
5.3 `test_create_balance_duplicate` — second POST for same (account, month) → 409
5.4 `test_create_balance_invalid_account` — account_id not found → 404
5.5 `test_get_balance` — GET /balances/{id} returns balance with account details
5.6 `test_get_balance_not_found` — 404
5.7 `test_update_balance` — PUT updates amount
5.8 `test_update_balance_not_found` — 404
5.9 `test_delete_balance` — DELETE returns 204; subsequent GET → 404
5.10 `test_delete_balance_not_found` — 404

**Month filter**
5.11 `test_list_by_month` — create balances for two months; filter returns only the requested month
5.12 `test_list_by_month_includes_account_detail` — response includes account_name, currency_code, side

**Roll-forward**
5.13 `test_roll_forward_basic` — seeds balances for month A; roll forward to month B; all active accounts get balances in B
5.14 `test_roll_forward_idempotent` — roll forward twice to same target month; second call: inserted=0, all skipped
5.15 `test_roll_forward_skips_existing` — one account already has a balance in target month; that one is skipped, others inserted
5.16 `test_roll_forward_excludes_closed_accounts` — closed account has balance in source month; not rolled forward
5.17 `test_roll_forward_no_balances` — no balances exist → 422
5.18 `test_roll_forward_same_month` — target month equals source month → 422

**Transfer**
5.19 `test_transfer_asset_to_asset` — asset sends to asset: from decreases, to increases
5.20 `test_transfer_asset_to_liability` — asset → liability (paydown): asset decreases, liability decreases
5.21 `test_transfer_liability_to_asset` — liability → asset (borrowing): liability increases, asset increases
5.22 `test_transfer_liability_to_liability` — liability → liability: from increases, to decreases
5.23 `test_transfer_missing_from_balance` — from account has no balance for month → 422
5.24 `test_transfer_missing_to_balance` — to account has no balance for month → 422
5.25 `test_transfer_account_not_found` — from_account_id doesn't exist → 404
