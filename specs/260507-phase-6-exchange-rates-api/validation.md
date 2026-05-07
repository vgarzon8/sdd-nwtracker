# Phase 6 — Exchange Rates API: Validation

## Automated

### Commands

```bash
cd backend
uv run pytest tests/test_exchange_rates.py -v   # all new tests pass
uv run pytest -v                                 # full suite still passes
uv run mypy app/                                 # no type errors
uv run ruff check app/                           # no lint errors
```

### Required Assertions

**CRUD**
- POST with valid payload → 201; body contains `id`, `currency_code`, `month`, `rate`
- POST duplicate `(currency_code, month)` → 409
- POST unknown `currency_code` → 404
- POST `rate=0` → 422; POST `rate=-1` → 422
- GET /exchange-rates/{id} → 200 with correct fields
- GET /exchange-rates/{id} unknown → 404
- PUT /exchange-rates/{id} → updated `rate` reflected in response and subsequent GET
- PUT `rate=0` → 422
- PUT unknown → 404
- DELETE → 204; subsequent GET → 404
- DELETE unknown → 404

**Filtering**
- `?currency=EUR` returns only EUR rates
- `?month=2026-03` returns only March rates across all currencies
- `?currency=EUR&month=2026-03` returns at most one record
- Filter with no match → `[]`

**Precision**
- Rate posted as `"0.9150"` must be returned as `"0.9150"` (string, four decimal places — trailing zero preserved)
- Note: SQLite does not enforce Numeric precision at the storage level; trailing zeros are preserved only when the value is submitted as a string with explicit decimal places (e.g. `"7.1000"`). Submitting `7.1` as a JSON number may return `"7.1"` rather than `"7.1000"`. Clients should always submit rates as 4dp strings.

---

## Manual Walkthrough

Run against the dev DB after seeding with `just db-seed`.

1. **List all exchange rates**
   - `GET /exchange-rates` — verify non-empty list from seed data

2. **Create a rate**
   - `POST /exchange-rates` with `{"currency_code": "EUR", "month": "2026-05", "rate": "1.0800"}`
   - Verify 201; verify `rate` in response is `"1.0800"` not `1.08`

3. **Filter by currency**
   - `GET /exchange-rates?currency=EUR` — verify only EUR rates returned

4. **Filter by month**
   - `GET /exchange-rates?month=2026-05` — verify only May 2026 rates returned

5. **Duplicate guard**
   - Repeat step 2 — verify 409

6. **Update rate**
   - `PUT /exchange-rates/{id}` with `{"rate": "1.0900"}`
   - Verify updated value in response

7. **Invalid rate**
   - `PUT /exchange-rates/{id}` with `{"rate": "0"}` → verify 422

8. **Delete**
   - `DELETE /exchange-rates/{id}` → 204; subsequent GET → 404

---

## Edge Cases

| Case | Expected |
|---|---|
| POST with `rate` as integer `7` | Stored and returned as `"7.0000"` |
| POST with more than 4 decimal places (e.g. `"7.12345"`) | Stored rounded/truncated to 4dp by DB; returned as `"7.1235"` (SQLite Numeric behaviour) |
| GET /exchange-rates with no rates in DB | `[]` |
| PUT changes only rate, not currency_code or month | currency_code and month unchanged in response |
| DELETE a rate that is referenced by a report (future phase) | 204 — no FK constraint from reports to exchange_rates in current schema |

---

## Implementation Status

### Task Groups 1 & 2 — CRUD Router + Registration
- `ruff check app/routers/exchange_rates.py` — PASS
- `mypy app/routers/exchange_rates.py` — PASS
- `ruff check app/main.py` — PASS
- Committed: `feat(phase-6): Exchange Rates CRUD endpoints and router registration`

### Task Group 3 — Tests
- `uv run pytest tests/test_exchange_rates.py -v` — 18/18 PASS
- `uv run pytest -v` — 121/121 PASS (no regressions)
- `ruff check app/` — PASS
- `mypy app/routers/exchange_rates.py` — PASS
- Committed: `feat(phase-6): exchange rate tests (18 cases)`

---

## Definition of Done

- [x] All `test_exchange_rates.py` tests pass (18/18)
- [x] No regressions in existing test files (121/121)
- [x] `mypy app/routers/exchange_rates.py` exits 0
- [x] `ruff check app/` exits 0
- [ ] Exchange rate endpoints visible in `/docs`
- [ ] Manual walkthrough completed against seeded dev DB
