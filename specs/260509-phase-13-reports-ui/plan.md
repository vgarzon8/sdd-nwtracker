# Phase 13 — Reports UI: Plan

## Task Group 1 — API Clients

1. Create `frontend/src/api/exchange-rates.ts`
   - `ExchangeRate` interface: `{ id: number; currency_code: string; month: string; rate: number }`
   - `listExchangeRates(month: string)` → `client.get<ExchangeRate[]>(\`/exchange-rates?month=${month}\`)`

2. Create `frontend/src/api/reports.ts`
   - `BalanceSummaryItem` interface: `{ group_key: string | null; balance_sum_usd: number }`
   - `getBalanceSummaryBySide(month: string)` → `client.get<BalanceSummaryItem[]>(\`/reports/balance-summary?attribute=side&month=${month}\`)`

3. Commit: `feat(phase-13): reports and exchange-rates API clients`

---

## Task Group 2 — Summary Cards

1. In `frontend/src/pages/ReportsPage.tsx`, replace the stub with:
   - State and derived values: `selectedMonth` (null initially), `effectiveMonth`, `defaultMonth` — same pattern as `BalancesPage`
   - Month selector UI: left/right chevron buttons, formatted month label
   - `useQuery` for `listBalancesFlat` (to derive `defaultMonth`)
   - `useQuery` for `getBalanceSummaryBySide(effectiveMonth)` — drives summary cards
   - Three summary cards: **Total Assets**, **Total Liabilities**, **Net Worth**
     - Assets = `balance_sum_usd` where `group_key === "asset"` (default 0 if missing)
     - Liabilities = `balance_sum_usd` where `group_key === "liability"` (default 0 if missing)
     - Net worth = assets − liabilities
   - Show 422 / other error as an inline error banner instead of the cards
   - Loading state: cards show `—` while query is pending

2. Commit: `feat(phase-13): summary cards with month selector`

---

## Task Group 3 — Breakdown Table

1. Add two more queries to `ReportsPage`:
   - `listBalancesByMonth(effectiveMonth)` → `BalanceDetail[]`
   - `listExchangeRates(effectiveMonth)` → `ExchangeRate[]`

2. Build a `rows` computed value:
   - Filter `BalanceDetail[]` to only accounts present in the month
   - Sort: assets first (A–Z by account name), then liabilities (A–Z by account name)
   - For each row compute `usd_eq`:
     - If `currency_code === "USD"`: `usd_eq = amount`
     - Otherwise: look up rate from exchange rates array; if found: `usd_eq = Math.round(amount / rate)`; if missing: `usd_eq = null` (show `—`)
   - Compute `assetTotal`, `liabilityTotal` (sum of `usd_eq` for each side; exclude nulls)

3. Render the breakdown table with columns: Account, Institution, Currency, Amount, USD eq.
   - Asset rows, then an "Assets" subtotal row
   - Liability rows, then a "Liabilities" subtotal row
   - Net worth footer row spanning columns

4. Commit: `feat(phase-13): breakdown table with subtotals`

---

## Task Group 4 — Error, Empty, and Loading States

1. Handle the case where `getBalanceSummaryBySide` returns a 422 error (missing exchange rate):
   - Show an inline error alert with the backend message
   - Do not hide the breakdown table — native amounts can still be shown (USD eq shows `—`)

2. Handle the case where no balances exist for the selected month:
   - Show an appropriate empty-state message below the cards

3. Verify loading states look reasonable (no flash of incorrect data)

4. Run `just frontend-typecheck` and `just frontend-lint` — fix any issues

5. Commit: `feat(phase-13): error and empty states; typecheck and lint clean`

---

## Task Group 5 — Final Validation & Roadmap Update

1. Run `just test` — confirm all backend tests still pass
2. Run `just frontend-typecheck` and `just frontend-lint` — confirm no regressions
3. Update `specs/260509-phase-13-reports-ui/validation.md` — tick all automated checks
4. Update `specs/roadmap.md` — mark Phase 13 `[X]`
5. Commit: `docs(phase-13): validation complete, roadmap updated`
