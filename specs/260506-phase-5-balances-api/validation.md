# Phase 5 — Balances API: Validation

## Automated

### Commands

```bash
cd backend
uv run pytest tests/test_balances.py -v   # all new tests pass
uv run pytest -v                           # full suite still passes
uv run mypy app/                           # no type errors
uv run ruff check app/                     # no lint errors
```

### Required Assertions

**CRUD**
- POST /balances with valid payload → 201, body contains `id`, `account_id`, `month`, `amount`
- POST /balances duplicate (account_id, month) → 409
- POST /balances unknown account_id → 404
- GET /balances/{id} → includes `account_name`, `currency_code`, `side`
- GET /balances/{id} unknown → 404
- PUT /balances/{id} → updated amount reflected in response and subsequent GET
- DELETE /balances/{id} → 204; GET → 404

**Month filter**
- GET /balances?month=2026-03 returns only records for 2026-03
- Each item includes `account_name`, `institution_id`, `currency_code`, `side`

**Roll-forward**
- POST /balances/roll-forward with adjacent target month → 200, `months` list has one entry with `month`, `inserted`, `skipped`
- `inserted + skipped == number of active accounts with a source balance` (per month entry)
- Second call to same target month: entry has `inserted == 0`, `skipped == N`
- Skipping months: response `months` list contains one entry per intermediate month plus the target, in order
- Closed accounts are absent from all rolled-forward months
- No balances in DB → 422
- No months strictly before target → 422

**Transfer**
- Transfer asset → asset: from balance decreases, to balance increases
- Transfer asset → liability: both balances decrease
- Transfer liability → asset: both balances increase
- Transfer liability → liability: from increases, to decreases
- Missing from-account balance → 422
- Missing to-account balance → 422
- Unknown account_id → 404

---

## Manual Walkthrough

Run against the dev DB after seeding with `just db-seed`.

1. **List balances for a known month**
   - `GET /balances?month=2026-03`
   - Verify response includes account names, currencies, and sides

2. **Create a balance manually**
   - Find an account with no balance in a future month (e.g., 2026-07)
   - `POST /balances` with that account_id and month
   - Verify 201 and correct fields

3. **Roll-forward — adjacent month**
   - `POST /balances/roll-forward` with `{"month": "2026-05"}`
   - Verify response has `months` list with one entry for 2026-05
   - Verify each active account from 2026-04 appears in 2026-05
   - Run again — verify entry has `inserted=0`

3b. **Roll-forward — cascade**
   - `POST /balances/roll-forward` with `{"month": "2026-07"}` (assuming last data is in 2026-04)
   - Verify response `months` list has entries for 2026-05, 2026-06, 2026-07
   - Verify `GET /balances?month=2026-06` returns balances for all active accounts

4. **Transfer — paydown scenario**
   - Pick a checking account (asset) and a credit card account (liability) that both have balances in 2026-05
   - `POST /balances/transfer` with `{"from_account_id": <checking>, "to_account_id": <credit_card>, "amount": 500, "month": "2026-05"}`
   - Verify checking balance decreased by 500, credit card balance decreased by 500

5. **Transfer — missing balance guard**
   - Pick a month with no balances for one account
   - Attempt a transfer referencing that account → verify 422 with a descriptive message

---

## Edge Cases

| Case | Expected |
|---|---|
| Roll-forward when all active accounts already have target-month balances | 200; single entry with `inserted=0`, `skipped=N` |
| Transfer with `amount=0` | 422 (amount must be positive) |
| Transfer between same account (`from == to`) | 422 or 200 with net-zero change — spec doesn't require special handling; implementation may return 422 for clarity |
| PUT /balances/{id} with no body fields | 422 (amount is required) |
| GET /balances with no query param | Returns all balances without account detail enrichment |
| Month format `2026-3` (no zero-pad) | 422 — only `YYYY-MM` accepted |

---

## Implementation Status

### Task Group 1 — Balance CRUD + Router Registration
- `ruff check app/routers/balances.py` — PASS
- `mypy app/routers/balances.py` — PASS
- Committed: `feat(phase-5): Balance CRUD endpoints and router registration`

### Task Group 2 — Roll-Forward Endpoint
- `ruff check app/routers/balances.py` — PASS
- `mypy app/routers/balances.py` — PASS
- Committed: `feat(phase-5): POST /balances/roll-forward endpoint`

### Task Group 3 — Transfer Endpoint
- `ruff check app/routers/balances.py` — PASS
- `mypy app/routers/balances.py` — PASS
- Committed: `feat(phase-5): POST /balances/transfer endpoint`

### Task Group 5 — Tests
- `uv run pytest tests/test_balances.py -v` — 25/25 PASS
- `uv run pytest -v` — 102/102 PASS (no regressions)
- `ruff check app/` — PASS
- `mypy app/routers/balances.py app/main.py` — PASS (2 pre-existing errors in unmodified files)
- Committed: `feat(phase-5): balance tests and roll-forward source-month fix`

**Note:** Roll-forward source-month logic was refined during testing. The source is now the most recent month strictly before the target month, not the absolute max. This prevents false 422 errors when the target month already has partial balances. requirements.md updated accordingly.

### Cascade roll-forward (post-phase addition)
- `uv run pytest tests/test_balances.py -v` — 26/26 PASS
- `uv run pytest -v` — 103/103 PASS
- `ruff check app/routers/balances.py` — PASS
- `mypy app/routers/balances.py` — PASS
- Committed: `feat(phase-5): roll-forward auto-cascades through intermediate months`

---

## Definition of Done

- [x] All `test_balances.py` tests pass (26/26)
- [x] No regressions in existing test files (103/103)
- [x] `mypy app/routers/balances.py` exits 0
- [x] `ruff check app/` exits 0
- [ ] Roll-forward and transfer endpoints visible and documented in `/docs`
- [ ] Manual walkthrough completed against seeded dev DB
