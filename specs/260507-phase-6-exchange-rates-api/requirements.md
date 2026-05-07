# Phase 6 — Exchange Rates API: Requirements

## Scope

### Included

Full CRUD for exchange rate records, with optional filtering by currency and/or month on the list endpoint.

| Endpoint | Description |
|---|---|
| `GET /exchange-rates` | List all exchange rates; optional `?currency=XXX` and/or `?month=YYYY-MM` filters |
| `POST /exchange-rates` | Create a new exchange rate |
| `GET /exchange-rates/{id}` | Retrieve one exchange rate by ID |
| `PUT /exchange-rates/{id}` | Update the rate value of an existing record |
| `DELETE /exchange-rates/{id}` | Delete a single exchange rate record |

### Not Included

- Latest-rate lookup endpoint (deferred; will be addressed in Phase 7 — Reports API if needed)
- Bulk import endpoint
- Automatic rate fetching from external sources (out of scope per mission)

---

## Data Shape

### ExchangeRate (DB table — already defined)

| Field | Type | Notes |
|---|---|---|
| `id` | int | Primary key, auto-increment |
| `currency_code` | str | FK → `currency.code` |
| `month` | str | Format: `YYYY-MM` |
| `rate` | Decimal | `Numeric(10, 4)` — `1 USD = rate units of currency` |

Unique constraint: `(currency_code, month)` — one rate per currency per month.

### ExchangeRateCreate

| Field | Required | Notes |
|---|---|---|
| `currency_code` | yes | Must reference an existing currency |
| `month` | yes | `YYYY-MM` format |
| `rate` | yes | Positive decimal; stored to 4 decimal places |

### ExchangeRateRead

| Field | Type | Notes |
|---|---|---|
| `id` | int | |
| `currency_code` | str | |
| `month` | str | |
| `rate` | Decimal | Serialized as a string (e.g. `"7.1000"`) to preserve 4-decimal precision |

### ExchangeRateUpdate

| Field | Required | Notes |
|---|---|---|
| `rate` | yes | Only the rate value may be updated; `currency_code` and `month` are immutable |

---

## Decisions

### `currency_code` and `month` are immutable after creation

`PUT /exchange-rates/{id}` accepts only `rate`. If the currency or month needs to change, delete and recreate. This matches the balance pattern from Phase 5 and keeps the unique-constraint semantics simple.

### Duplicate `(currency_code, month)` → 409

`POST` returns 409 if a rate for that pair already exists. No upsert behaviour.

### Rate serialized as `Decimal` string, not float

The `rate` field is `Numeric(10, 4)` in the DB and `Decimal` in the Pydantic schema. Pydantic v2 serializes `Decimal` as a string in JSON output, preserving all four decimal places (e.g. `"7.1000"`, `"0.9150"`). Clients must treat this field as a fixed-point string, not a float.

### `rate` must be positive

A rate of 0 or negative is semantically invalid (`1 USD = 0 units` is meaningless). Validated at the router level; return 422.

### Filter behaviour

Both `currency` and `month` query params are optional and independently combinable:

| `?currency` | `?month` | Behaviour |
|---|---|---|
| absent | absent | Return all exchange rates |
| present | absent | Return all rates for that currency |
| absent | present | Return all rates for that month |
| present | present | Return rate for the specific (currency, month) pair |

---

## Context

- Follow the same router patterns as Phase 3–5: `APIRouter`, Pydantic schemas, `Depends(get_session)`, `HTTPException`.
- Error codes: `404` for not-found resources and unknown `currency_code`, `409` for unique constraint violations, `422` for semantic validation failures (non-positive rate).
- Register the router in `app/main.py` alongside existing routers.
- Tests use in-memory SQLite, FastAPI `TestClient`, `_make_*` helpers consistent with existing test files.
- Month strings are `YYYY-MM` throughout — no parsing beyond basic format.
- Convention: `1 USD = X units of foreign currency` (e.g. 7.1000 CNY per USD). The API stores and returns the rate as provided; no inversion logic.
