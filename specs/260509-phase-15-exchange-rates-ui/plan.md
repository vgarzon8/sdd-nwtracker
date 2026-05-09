# Phase 15 — Exchange Rates UI: Plan

## Task Group 1 — API Client

1. Extend `frontend/src/api/exchange-rates.ts`:
   - Add `ExchangeRateCreate` interface: `{ currency_code: string; month: string; rate: number }`
   - Add `ExchangeRateUpdate` interface: `{ rate: number }`
   - Add `createExchangeRate(body: ExchangeRateCreate): Promise<ExchangeRate>` → `POST /exchange-rates`
   - Add `updateExchangeRate(id: number, body: ExchangeRateUpdate): Promise<ExchangeRate>` → `PUT /exchange-rates/{id}`
   - Add `deleteExchangeRate(id: number): Promise<void>` → `DELETE /exchange-rates/{id}`

2. Run `just frontend-typecheck` — confirm no errors

3. Commit: `feat(phase-15): exchange rates API client — create, update, delete`

---

## Task Group 2 — ExchangeRatesPage

1. Create `frontend/src/pages/ExchangeRatesPage.tsx`:

   **Data loading**
   - `useQuery(["balances-months"], listBalancesFlat)` to derive the default month (most recent with data)
   - `useQuery(["currencies"], listCurrencies)` to get the full currency list (filter out USD)
   - `useQuery(["exchange-rates", effectiveMonth], () => listExchangeRates(effectiveMonth))` for the month's rates

   **State**
   - `selectedMonth: string | null` — null until user navigates (derives default from balance data)
   - `editState: { key: string; value: string } | null`
   - `saveErrors: Record<string, string>`
   - `deleteTarget: ExchangeRate | null` — controls the confirm dialog

   **Month selector**
   - Prev/next chevron buttons (`ChevronLeftIcon`, `ChevronRightIcon`)
   - Formatted month label (`MMM YYYY`)

   **Table** — columns: Currency, Rate
   - One row per non-USD currency
   - Row key: currency code (stable; each currency appears at most once per month)
   - Rate cell: if no rate exists, display `—` (clickable); if a rate exists, display the rate formatted to 4 decimal places (clickable)
   - Clicking the rate cell enters edit mode (inline `Input` with `type="number"`, `step="0.0001"`, `autoFocus`)
   - Enter or blur commits; Escape cancels
   - If the value is blank or unchanged on commit, cancel silently
   - Trash icon button (`Trash2Icon`) on rows with an existing rate; disabled while an edit or delete is pending

   **Delete confirmation dialog** (shadcn `Dialog`)
   - Opens when trash icon is clicked; sets `deleteTarget`
   - Shows: "Delete exchange rate for {currency} in {month}?"
   - Confirm calls `deleteExchangeRate(deleteTarget.id)`; on success invalidates `["exchange-rates", effectiveMonth]`
   - Cancel closes without action

   **Empty state**
   - If no non-USD currencies exist: "No currencies found. Add currencies first." with a link to `/currencies`

2. Run `just frontend-typecheck` and `just frontend-lint` — fix any issues

3. Commit: `feat(phase-15): ExchangeRatesPage — month view with inline edit and delete`

---

## Task Group 3 — Route & Navigation

1. Add route in `frontend/src/App.tsx`:
   - Import `ExchangeRatesPage`
   - Add `{ path: "/exchange-rates", element: <ExchangeRatesPage /> }` to the children array

2. Add sidebar entry in `frontend/src/components/Sidebar.tsx`:
   - Add `{ to: "/exchange-rates", label: "Exchange Rates" }` to the Reference Data group (after Currencies, Tags, Institutions)

3. Run `just frontend-typecheck` and `just frontend-lint` — confirm clean

4. Commit: `feat(phase-15): add /exchange-rates route and sidebar entry`

---

## Task Group 4 — Final Validation & Roadmap Update

1. Run `just test` — confirm all backend tests still pass
2. Run `just frontend-typecheck` and `just frontend-lint` — confirm clean
3. Update `specs/260509-phase-15-exchange-rates-ui/validation.md` — tick all automated checks
4. Update `specs/roadmap.md` — mark Phase 15 `[X]`
5. Commit: `docs(phase-15): validation complete, roadmap updated`
