# Phase 16 — Dashboard: Plan

## Task Group 1 — Dependency & API Client

1. Install Recharts:
   ```
   cd frontend && npm install recharts
   ```

2. Extend `frontend/src/api/reports.ts`:
   - Add `BalanceSummaryHistoryItem` interface: `{ month: string; group_key: string | null; balance_sum_usd: number }`
   - Add `getBalanceSummaryByTags(month: string)` → `GET /reports/balance-summary?attribute=tags&month=${month}` returning `BalanceSummaryItem[]`
   - Add `getBalanceSummaryHistory(from: string, to: string)` → `GET /reports/balance-summary/history?attribute=side&from=${from}&to=${to}` returning `BalanceSummaryHistoryItem[]`

3. Run `just frontend-typecheck` — confirm no errors

4. Commit: `feat(phase-16): install recharts; extend reports API client`

---

## Task Group 2 — Summary Cards

1. In `frontend/src/pages/DashboardPage.tsx`, replace the stub with a skeleton that:
   - Derives `effectiveMonth` (most recent month with balance data) and `priorMonth` (the month immediately before in `listBalancesFlat`) using the same pattern as `BalancesPage.tsx`
   - Fetches current month summary via `getBalanceSummaryBySide(effectiveMonth)` with `queryKey: ["reports-summary-side", effectiveMonth]`
   - Fetches prior month summary via `getBalanceSummaryBySide(priorMonth)` with `queryKey: ["reports-summary-side", priorMonth]`; skipped (`enabled: !!priorMonth`) when no prior month exists

2. Define a local `NetWorthCard` component:
   - Props: `label: string`, `value: number | null`, `delta: number | null`, `loading: boolean`, `error: boolean`
   - Displays label, `$value` (or `—` if null/loading/error), and a signed delta badge (`+$X` in green, `−$X` in red, `—` if null)
   - Uses shadcn Card/border styling consistent with ReportsPage

3. Render three cards in a `grid grid-cols-3 gap-4`:
   - Total Assets: `asset` group from current summary; delta = current assets − prior assets
   - Total Liabilities: `liability` group; delta = current liabilities − prior liabilities
   - Net Worth: assets − liabilities for each month; delta = current net worth − prior net worth

4. When current summary returns 422, show an inline warning banner above the cards:
   - Text: "Exchange rates missing for [month]. Some figures cannot be calculated."
   - Link to `/exchange-rates` with text "Enter exchange rates"
   - Cards render with `—` values

5. Run `just frontend-typecheck` and `just frontend-lint` — fix any issues

6. Commit: `feat(phase-16): DashboardPage — summary cards with delta vs prior month`

---

## Task Group 3 — Net Worth History Chart

1. In `DashboardPage.tsx`, add state: `range: "6m" | "12m" | "all"` defaulting to `"12m"`

2. Compute `historyFrom` from `effectiveMonth` and `range`:
   - `"6m"`: subtract 5 months from `effectiveMonth` (shows 6 months including current)
   - `"12m"`: subtract 11 months
   - `"all"`: use `"2000-01"` as sentinel

3. Fetch history via `getBalanceSummaryHistory(historyFrom, effectiveMonth)` with `queryKey: ["reports-history", historyFrom, effectiveMonth]`

4. Transform history data into chart-ready `{ month, netWorth }[]`:
   - For each unique month in the result, compute `netWorth = asset.balance_sum_usd - liability.balance_sum_usd`
   - Sort ascending by month
   - Format the `month` label for display (e.g., "May '26")

5. Render a Recharts `LineChart` wrapped in `ResponsiveContainer`:
   - X-axis: formatted month label
   - Y-axis: USD value, formatted with `$` prefix and `k` abbreviation for thousands (e.g., `$120k`)
   - Single `Line` for net worth, no dots on individual data points, smooth curve (`type="monotone"`)
   - `Tooltip` showing full formatted USD value on hover
   - No legend (single line, self-explanatory)

6. Render range picker as three toggle buttons (`6m`, `12m`, `All`) above the chart; active button uses solid/muted-foreground style

7. If history returns 422, show the same warning banner as the summary cards section (or share the same error state)

8. Run `just frontend-typecheck` and `just frontend-lint` — fix any issues

9. Commit: `feat(phase-16): DashboardPage — net worth history chart with range picker`

---

## Task Group 4 — Balances by Tag Table

1. Fetch tag breakdown via `getBalanceSummaryByTags(effectiveMonth)` with `queryKey: ["reports-summary-tags", effectiveMonth]`

2. Sort rows: named tags alphabetically, then "Untagged" last

3. Render a table with columns: Tag, Total (USD)
   - `group_key === null` displays as "Untagged"
   - Format values as `$X` using the existing `formatUsd` helper
   - If the query returns 422, show the shared warning banner and skip the table body

4. If no tag data exists for the month (empty array), show "No balance data for [month]."

5. Run `just frontend-typecheck` and `just frontend-lint` — fix any issues

6. Commit: `feat(phase-16): DashboardPage — balances by tag table`

---

## Task Group 5 — Final Validation & Roadmap Update

1. Run `just test` — confirm all backend tests still pass
2. Run `just frontend-typecheck` and `just frontend-lint` — confirm clean
3. Update `specs/260509-phase-16-dashboard/validation.md` — tick all automated checks
4. Update `specs/roadmap.md` — mark Phase 16 `[X]`
5. Commit: `docs(phase-16): validation complete, roadmap updated`
