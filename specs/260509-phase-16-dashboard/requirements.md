# Phase 16 — Dashboard: Requirements

## Scope

### Included

- Replace the `DashboardPage.tsx` stub with a fully populated page
- **Section 1 — Summary cards**: three cards (Total Assets, Total Liabilities, Net Worth), each showing the current month's USD value and a signed delta vs. the prior month (e.g., `+$1,200` or `−$800`)
- **Section 2 — Net worth history chart**: vertical bar chart of net worth over time built with Recharts; range picker with three presets (6 months, 12 months, All); defaults to 12 months
- **Section 3 — Balances by tag**: horizontal bar chart of USD totals per tag for the current month; tag names resolved from `GET /tags`; accounts with no tag grouped under "Untagged"; bars sorted alphabetically, Untagged last
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
| History chart type | Bar chart (`BarChart`/`Bar`) | User preference: bars are always visible; line chart with `dot={false}` only showed a marker on hover |
| History range | 12 months default; presets 6m / 12m / All | Trailing 12 months is the most useful default for monthly financial tracking |
| "All" range | `from` = `"2000-01"` sentinel | The history endpoint silently omits months with no data, so a far-past from date is safe |
| Tag breakdown data | `GET /reports/balance-summary?attribute=tags&month=YYYY-MM` | Direct API support; `group_key` is an integer tag ID (not name); `null` for untagged |
| Tag name resolution | Fetch `GET /tags` separately; join `group_key` (int) to `tag.name` via a `Map<number, string>` | The reports API returns tag IDs, not names; names must be looked up from the tags list. Fallback label: `Tag {id}` |
| Tag `balance_sum_usd` sign | Always positive; no negative bars | The backend sums all balances for each tag regardless of account side — liability balances are stored as positive integers and are not negated in the reports service. Negative per-tag values are not possible with the current API. |
| Tag chart type | Horizontal `BarChart` (`layout="vertical"`) | Shows relative magnitude across tags; bars labeled with tag name on the Y-axis; more readable than a table for comparison |
| Tag chart height | Dynamic: `Math.max(120, tagCount * 44)` px | Prevents cramped bars with many tags while avoiding excessive whitespace for few tags |
| Null group_key | Displayed as "Untagged", sorted last | User-friendly label; placed after named tags to keep the named entries prominent |
| `balance_sum_usd` coercion | Wrap in `Number()` before arithmetic and display | Pydantic v2 can serialize numeric fields as strings in some model configurations; `Number()` is safe even when the value is already a number |
| `group_key` type | `string \| number \| null` (not `string \| null`) | Actual backend model is `str \| int \| None`; integer tag IDs appear for the tags attribute; always use `String(group_key)` before string methods like `localeCompare` |
| History response shape | Wrapper object: `{from_month, to_month, items: BalanceSummaryHistoryItem[]}` | Actual backend response wraps items; spec said "plain array" but implementation uses a named wrapper — always read the router source, not just the spec |
| TanStack Query array default | Use `response?.items ?? []` not `data = []` destructuring default | TanStack Query can return `null` (not `undefined`) in some states, bypassing the `= []` default; also apply `Array.isArray` guard before iterating any API-returned array |

---

## Context

- **Stack**: TypeScript, React 19, TanStack Query, shadcn/ui, Tailwind CSS v4, Recharts (new)
- **Current page stub**: `src/pages/DashboardPage.tsx` — replace entirely
- **Backend endpoints** (fully implemented):
  - `GET /reports/balance-summary?attribute=side&month=YYYY-MM` → `BalanceSummaryItem[]` where `group_key` is `"asset"` or `"liability"`; returns 422 if any non-USD account is missing an exchange rate
  - `GET /reports/balance-summary?attribute=tags&month=YYYY-MM` → `BalanceSummaryItem[]` where `group_key` is an **integer tag ID** or `null` (untagged); resolve to names via `GET /tags`
  - `GET /reports/balance-summary/history?attribute=side&from=YYYY-MM&to=YYYY-MM` → `BalanceSummaryHistoryResponse` `{from_month, to_month, items: [{month, group_key, balance_sum_usd}]}`; silently omits months with no data; 422 if any rate is missing
- **Existing API client**: `src/api/reports.ts` has `BalanceSummaryItem` and `getBalanceSummaryBySide` — extend, do not replace
- **Deriving prior month**: filter `listBalancesFlat()` to months strictly less than `effectiveMonth`, then take the max — same pattern already used in `BalancesPage.tsx`
- **Chart net worth**: for each month in history data, compute `asset.balance_sum_usd - liability.balance_sum_usd`
- **No copy-style constraints**: labels should be plain and functional
- **ReportsPage**: the existing `SummaryCard` component in `ReportsPage.tsx` is local; the Dashboard should define its own variant with delta support rather than sharing
