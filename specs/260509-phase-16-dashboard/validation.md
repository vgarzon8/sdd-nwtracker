# Phase 16 — Dashboard: Validation

## Automated

- [ ] `just test` passes (all backend tests green, no regressions)
- [ ] `just frontend-typecheck` passes with no errors
- [ ] `just frontend-lint` passes with no errors

---

## Manual Walkthrough

### Setup

- [ ] Dev servers running: `just dev` and `just frontend-dev`
- [ ] At least two months of balance data exist (to test delta and history)
- [ ] Exchange rates entered for all non-USD accounts in at least one month

### Navigation

- [ ] Dashboard is the default route (`/` → `/dashboard`)
- [ ] Clicking "Dashboard" in the sidebar navigates to `/dashboard`
- [ ] Page title is "Dashboard"

### Summary cards

- [ ] Three cards visible: Total Assets, Total Liabilities, Net Worth
- [ ] Each card shows a USD value for the most recent month with data
- [ ] Each card shows a signed delta vs the prior month (e.g., `+$1,200` or `−$800`)
- [ ] Delta is green for positive, red for negative
- [ ] Delta shows `—` when there is no prior month with data
- [ ] Cards show `—` and a warning banner when exchange rates are missing for any non-USD account

### Missing rates warning

- [ ] Warning banner appears above the cards when any exchange rate is missing
- [ ] Banner text identifies the affected month
- [ ] Banner contains a link to `/exchange-rates`
- [ ] Clicking the link navigates to the Exchange Rates page

### Net worth history chart

- [ ] Line chart renders with net worth on the Y-axis and months on the X-axis
- [ ] Default range shows trailing 12 months
- [ ] Switching to 6m reduces the visible range to 6 months
- [ ] Switching to All shows the full history
- [ ] Active range button is visually distinct from inactive ones
- [ ] Hovering a data point shows a tooltip with the formatted USD value
- [ ] Chart is responsive (resizes with the window)

### Balances by tag table

- [ ] Table shows all tags with a USD total for the current month
- [ ] Accounts with no tag appear under "Untagged" at the bottom
- [ ] Tags are sorted alphabetically; Untagged is last
- [ ] "No balance data" message appears when the current month has no entries

### Edge cases

- [ ] Page loads correctly when there is only one month of data (delta shows `—`, history shows a single point)
- [ ] Page loads correctly when all accounts are USD (no exchange rate issues)
- [ ] No regressions on other pages (Reports, Balances, Exchange Rates)

---

## Definition of Done

- Dashboard shows summary cards with current values and deltas
- Net worth history chart renders with working range picker
- Balances by tag table shows correct USD totals with Untagged group
- Missing exchange rate condition is handled gracefully with a warning and link
- All automated checks pass
- No regressions to any other page
