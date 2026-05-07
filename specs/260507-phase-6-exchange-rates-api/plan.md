# Phase 6 — Exchange Rates API: Plan

## Task Groups

---

### 1. Exchange Rates Router — CRUD

**File:** `backend/app/routers/exchange_rates.py`

1.1 Define Pydantic schemas:
- `ExchangeRateCreate`: `currency_code: str`, `month: str`, `rate: Decimal`
- `ExchangeRateRead`: `id: int`, `currency_code: str`, `month: str`, `rate: Decimal`
- `ExchangeRateUpdate`: `rate: Decimal`

1.2 Implement `GET /exchange-rates`
- Optional query params: `currency: str | None`, `month: str | None`
- Apply filters independently (both, either, or neither)
- Return `list[ExchangeRateRead]`

1.3 Implement `POST /exchange-rates`
- Validate `currency_code` exists → 404 if not
- Validate `rate > 0` → 422 if not
- Insert; catch `IntegrityError` on `(currency_code, month)` duplicate → 409
- Return `ExchangeRateRead`, status 201

1.4 Implement `GET /exchange-rates/{id}`
- Return `ExchangeRateRead`; 404 if not found

1.5 Implement `PUT /exchange-rates/{id}`
- Accept `ExchangeRateUpdate` (rate only)
- Validate `rate > 0` → 422 if not
- 404 if not found
- Return `ExchangeRateRead`

1.6 Implement `DELETE /exchange-rates/{id}`
- 204 on success; 404 if not found

---

### 2. Router Registration

**File:** `backend/app/main.py`

2.1 Import `exchange_rates` router and add `app.include_router(exchange_rates.router)`

---

### 3. Tests

**File:** `backend/tests/test_exchange_rates.py`

Use `_make_currency` and `_make_exchange_rate` helpers consistent with existing test files.

**CRUD**
3.1 `test_list_exchange_rates_empty` — GET returns []
3.2 `test_create_exchange_rate` — POST returns 201, fields match; rate is string `"7.1000"`
3.3 `test_create_exchange_rate_duplicate` — second POST for same (currency, month) → 409
3.4 `test_create_exchange_rate_invalid_currency` — unknown currency_code → 404
3.5 `test_create_exchange_rate_zero_rate` — rate=0 → 422
3.6 `test_create_exchange_rate_negative_rate` — rate=-1 → 422
3.7 `test_get_exchange_rate` — GET /exchange-rates/{id} returns correct fields
3.8 `test_get_exchange_rate_not_found` — 404
3.9 `test_update_exchange_rate` — PUT changes rate; reflected in response and subsequent GET
3.10 `test_update_exchange_rate_not_found` — 404
3.11 `test_update_exchange_rate_zero_rate` — rate=0 → 422
3.12 `test_delete_exchange_rate` — DELETE returns 204; subsequent GET → 404
3.13 `test_delete_exchange_rate_not_found` — 404

**Filtering**
3.14 `test_list_filter_by_currency` — two currencies, two months; filter returns only the requested currency
3.15 `test_list_filter_by_month` — filter returns only the requested month across currencies
3.16 `test_list_filter_by_currency_and_month` — combined filter returns exactly one record
3.17 `test_list_filter_no_match` — filter with currency+month that has no rate returns []

**Precision**
3.18 `test_rate_precision_preserved` — POST rate `"0.9150"`; GET returns `"0.9150"` not `0.915` or float
