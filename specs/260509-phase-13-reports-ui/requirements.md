# Phase 13 — Reports UI: Requirements

## Scope

### Included

- **Month selector** in the page header, defaulting to the most recent month that has balance data (same pattern as `BalancesPage`)
- **Summary cards**: total assets (USD), total liabilities (USD), net worth (USD)
- **Breakdown table**: one row per account with a balance entry for the selected month — account name, institution, currency, native amount, USD equivalent; asset rows grouped first (with subtotal), liability rows second (with subtotal), net worth row at the bottom
- New `src/api/reports.ts` API client for `GET /reports/balance-summary`
- New `src/api/exchange-rates.ts` API client for `GET /exchange-rates`
- Inline error state when the backend returns 422 (exchange rate missing for a non-USD account)

### Not included

- Sparkline or history charts (Phase 13 scope is cards + table only)
- Grouping by institution, currency, or tags
- Breakdown by accounts with no balance entry for the selected month
- Exchange rate management (already covered by reference data UI)

---

## Decisions

| Decision | Choice | Reason |
|---|---|---|
| Summary card data source | `GET /reports/balance-summary?attribute=side&month=YYYY-MM` | Single call returns pre-computed USD totals grouped by side; backend handles exchange-rate conversion and raises 422 if a rate is missing |
| Breakdown table data sources | `GET /balances?month=YYYY-MM` + `GET /exchange-rates?month=YYYY-MM` | Combines per-account native amounts with rates for client-side USD equivalent computation |
| USD equivalent formula | `Math.round(amount / rate)` where rate is "1 USD = X units of foreign currency" | Matches backend convention: `rate` is CNY-per-USD (or X-per-USD) |
| USD accounts in breakdown | USD equivalent = native amount (no rate lookup needed) | Avoids requiring a USD exchange rate entry |
| Table sort order | Assets first (A–Z), then liabilities (A–Z) | Matches the preview layout and the `side` field already present on `BalanceDetail` |
| Month default | Most recent month in `listBalancesFlat()` result | Identical to `BalancesPage` derivation; reuses already-understood pattern |
| 422 error handling | Inline error banner replacing the content area | Surface the backend message rather than hiding data; user must add the exchange rate to resolve |
| Loading state | TanStack Query `isLoading` flags; show skeleton or disabled state | Consistent with other pages |

---

## Context

- **Stack**: TypeScript, React 19, TanStack Query, shadcn/ui, Tailwind CSS v4
- **Existing patterns to follow**:
  - Month selector navigation: `prevMonth` / `nextMonth` helpers + `ChevronLeftIcon` / `ChevronRightIcon` — copy from `BalancesPage`
  - `defaultMonth` derivation from `listBalancesFlat()` — copy from `BalancesPage`
  - Inline error display pattern from `BalancesPage`
- **Backend endpoints** (both implemented and tested):
  - `GET /reports/balance-summary?attribute=side&month=YYYY-MM` → `[{group_key: "asset"|"liability", balance_sum_usd: int}]`
  - `GET /balances?month=YYYY-MM` → `BalanceDetail[]` (already in `src/api/balances.ts` as `listBalancesByMonth`)
  - `GET /exchange-rates?month=YYYY-MM` → `[{id, currency_code, month, rate}]` (no frontend client yet)
- **Integer amounts**: all balance amounts and computed USD equivalents are whole currency units
- **Exchange rate** is stored as `Decimal(10, 4)` — "1 USD = X units of foreign currency" (e.g., 7.1000 CNY per USD)
- **No copy-style constraints**: labels should be plain and functional
