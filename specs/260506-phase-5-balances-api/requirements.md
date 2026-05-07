# Phase 5 — Balances API: Requirements

## Scope

### Included

Full CRUD for balance records, a month-filtered list with account details, an idempotent roll-forward operation, and a side-aware transfer operation.

| Endpoint | Description |
|---|---|
| `GET /balances` | List all balances, optionally filtered by `month=YYYY-MM` |
| `POST /balances` | Create a single balance record |
| `GET /balances/{id}` | Retrieve one balance by ID |
| `PUT /balances/{id}` | Update the amount of an existing balance |
| `DELETE /balances/{id}` | Delete a single balance record |
| `POST /balances/roll-forward` | Copy last month's balances to a new month (insert-or-ignore) |
| `POST /balances/transfer` | Apply a transfer between two accounts for a given month |

### Not Included

- Currency conversion or USD-equivalent totals (deferred to Phase 7 — Reports API)
- Per-account balance history endpoint
- Bulk update endpoint
- Category summaries with cross-currency totals (meaningless without exchange rates)

---

## Data Shape

### Balance (DB table — already defined)

| Field | Type | Notes |
|---|---|---|
| `id` | int | Primary key, auto-increment |
| `account_id` | int | FK → `account.id` |
| `month` | str | Format: `YYYY-MM` |
| `amount` | int | Whole currency units; no decimals |

Unique constraint: `(account_id, month)` — one balance per account per month.

### BalanceRead (API response)

Returns all DB fields. When `month` query param is provided, the list response enriches each item with account context:

| Field | Source |
|---|---|
| `id` | balance |
| `account_id` | balance |
| `month` | balance |
| `amount` | balance |
| `account_name` | account |
| `institution_id` | account |
| `currency_code` | account |
| `side` | account (`"asset"` or `"liability"`) |

### BalanceCreate

| Field | Required | Notes |
|---|---|---|
| `account_id` | yes | Must reference an existing account |
| `month` | yes | `YYYY-MM` format |
| `amount` | yes | Integer |

### BalanceUpdate

| Field | Required | Notes |
|---|---|---|
| `amount` | yes | `account_id` and `month` are immutable after creation |

### RollForwardRequest

| Field | Required | Notes |
|---|---|---|
| `month` | yes | Target month to roll forward into (`YYYY-MM`) |

### RollForwardResult

| Field | Notes |
|---|---|
| `month` | Target month |
| `inserted` | Number of new balance records created |
| `skipped` | Number skipped because a record already existed for that (account, month) |

### TransferRequest

| Field | Required | Notes |
|---|---|---|
| `from_account_id` | yes | Source account |
| `to_account_id` | yes | Destination account |
| `amount` | yes | Positive integer; units of the source account's currency |
| `month` | yes | `YYYY-MM`; both accounts must have an existing balance for this month |

### TransferResult

Returns the two updated balance records (both as `BalanceRead`).

---

## Decisions

### Roll-forward: source month is the most recent month strictly before the target

The most recent month **strictly before the target month** for which any active account has a balance is used as the source. Using the absolute max would falsely block idempotent re-runs when the target month already has some balances. If no such month exists, return `422`.

### Roll-forward: only active accounts

Closed accounts are excluded. Active accounts with no balance in the source month are also skipped (no zero-fill).

### Roll-forward is idempotent

Uses insert-or-ignore semantics. Re-running for the same target month returns `inserted=0, skipped=N` with no data change.

### Transfer requires existing balance records

Both accounts must have a balance record for the given month before a transfer can be applied. Transfers do not create new balance records. If either is missing, return `422` with a message identifying which account(s) have no balance for that month.

The rationale: balance records represent end-of-month snapshots. Creating a record implicitly via a transfer would bypass the roll-forward workflow and could produce dangling records with no historical baseline.

### Transfer delta logic depends on account side

A transfer moves money from one account to another. The `amount` field is always positive; direction is inferred from account `side`:

| Account role | Side | Effect |
|---|---|---|
| `from_account` | asset | `balance -= amount` (money leaves) |
| `from_account` | liability | `balance += amount` (borrowing more) |
| `to_account` | asset | `balance += amount` (money arrives) |
| `to_account` | liability | `balance -= amount` (debt paid down) |

### `account_id` and `month` are immutable after creation

`PUT /balances/{id}` only accepts `amount`. If an account or month needs to change, delete and recreate.

### No category summaries in Phase 5

The month-filtered list returns per-balance data with account details. Cross-currency totals require exchange rates, which belong in Phase 7.

---

## Context

- Follow the same router pattern established in Phases 3–4: `APIRouter`, Pydantic `Create/Read/Update` schemas, `Depends(get_session)`, `HTTPException` for validation errors.
- Error codes: `404` for not-found resources, `409` for unique constraint violations, `422` for semantic validation failures (e.g., missing balance records for transfer).
- Register the router in `app/main.py` alongside existing routers.
- Tests use in-memory SQLite, FastAPI `TestClient`, and `_make_*` helper functions consistent with existing test files.
- Amounts are always integers — no float arithmetic.
- Month strings are always `YYYY-MM` — no parsing beyond format validation.
