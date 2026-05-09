# Phase 16 — Dashboard: Requirements

## Scope

### Included

- Replace the `DashboardPage.tsx` stub with a fully populated page
- **Section 1 — Summary cards**: three cards (Total Assets, Total Liabilities, Net Worth), each showing the current month's USD value and a signed delta vs. the prior month (e.g., `+$1,200` or `−$800`)
- **Section 2 — Net worth history chart**: line chart of net worth over time built with Recharts; range picker with three presets (6 months, 12 months, All); defaults to 12 months
- **Section 3 — Balances by tag table**: table of USD totals per tag for the current month; accounts with no tag grouped under "Untagged"
- **Missing-rates warning**: when the Reports API returns 422 (missing exchange rates), show an inline warning banner with a link to `/exchange-rates`; affected cards show `—`
- New API functions in `src/api/reports.ts`: `getBalanceSummaryByTags`, `getBalanceSummaryHistory`
- Install `recharts` as a new frontend dependency

### Not included

- Month selector (Dashboard always shows the most recent month with data)
- Per-account breakdown (that is the Reports page)
- Drill-down from tag to account list
- Editable content on the Dashboard
- Custom date range (only the three presets)

---

## Decisions

| Decision | Choice | Reason |
|---|---|---|
| Current month | Most recent month with balance data | Consistent with Balance Entry, Reports, and Exchange Rates pages |
| Prior month | The month immediately before the current month in `listBalancesFlat` | Avoids assuming consecutive months; uses actual data presence |
| Delta display | Signed integer with `+`/`−` prefix and color (green/red) | Clear at a glance; consistent with financial dashboard conventions |
| Missing rates | Inline warning banner; cards show `—` | Actionable: tells the user exactly what is missing and links to the fix |
| Chart library | Recharts | Lightweight, React-native, widely used; no other chart library already present |
| History range | 12 months default; presets 6m / 12m / All | Trailing 12 months is the most useful default for monthly financial tracking |
| "All" range | `from` = `"2000-01"` sentinel | The history endpoint silently omits months with no data, so a far-past from date is safe |
| Tag breakdown data | `GET /reports/balance-summary?attribute=tags&month=YYYY-MM` | Direct API support; returns `null` group_key for untagged accounts |
| Null group_key | Displayed as "Untagged" | User-friendly label for accounts with no assigned tag |

---

## Context

- **Stack**: TypeScript, React 19, TanStack Query, shadcn/ui, Tailwind CSS v4, Recharts (new)
- **Current page stub**: `src/pages/DashboardPage.tsx` — replace entirely
- **Backend endpoints** (fully implemented):
  - `GET /reports/balance-summary?attribute=side&month=YYYY-MM` → `BalanceSummaryItem[]` where `group_key` is `"asset"` or `"liability"`; returns 422 if any non-USD account is missing an exchange rate
  - `GET /reports/balance-summary?attribute=tags&month=YYYY-MM` → `BalanceSummaryItem[]` where `group_key` is a tag name or `null` (untagged)
  - `GET /reports/balance-summary/history?attribute=side&from=YYYY-MM&to=YYYY-MM` → `BalanceSummaryHistoryItem[]` `{month, group_key, balance_sum_usd}`; silently omits months with no data; 422 if any rate is missing
- **Existing API client**: `src/api/reports.ts` has `BalanceSummaryItem` and `getBalanceSummaryBySide` — extend, do not replace
- **Deriving prior month**: filter `listBalancesFlat()` to months strictly less than `effectiveMonth`, then take the max — same pattern already used in `BalancesPage.tsx`
- **Chart net worth**: for each month in history data, compute `asset.balance_sum_usd - liability.balance_sum_usd`
- **No copy-style constraints**: labels should be plain and functional
- **ReportsPage**: the existing `SummaryCard` component in `ReportsPage.tsx` is local; the Dashboard should define its own variant with delta support rather than sharing
