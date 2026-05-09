# Phase 13 — Reports UI: Validation

## Automated

- [ ] `just test` passes (all backend tests green; no regressions)
- [ ] `just frontend-typecheck` passes with no errors
- [ ] `just frontend-lint` passes with no errors

---

## Manual Walkthrough

### Setup

- [ ] At least two active accounts exist with balances in some prior month (use `just db-seed` if needed)
- [ ] Dev servers running: `just dev` and `just frontend-dev`

### Summary Cards

- [ ] Navigate to `/reports`; the page loads without errors
- [ ] The month selector defaults to the most recent month that has balance data
- [ ] **Total Assets**, **Total Liabilities**, and **Net Worth** cards display USD amounts formatted with commas (e.g. `12,000`)
- [ ] Net worth = total assets − total liabilities
- [ ] Navigating to a different month using the chevron buttons updates all three cards
- [ ] Navigating to a month with no balance data shows 0 for all cards (or an appropriate empty state)

### Breakdown Table

- [ ] The breakdown table shows one row per account that has a balance for the selected month
- [ ] Asset rows appear before liability rows; each group is sorted A–Z by account name
- [ ] Asset subtotal row shows the correct sum of USD equivalents for asset accounts
- [ ] Liability subtotal row shows the correct sum of USD equivalents for liability accounts
- [ ] Net worth footer row shows assets − liabilities
- [ ] For USD accounts: the "USD eq." column equals the "Amount" column
- [ ] For non-USD accounts with an exchange rate: "USD eq." = `round(amount / rate)` in whole units
- [ ] For non-USD accounts with no exchange rate: "USD eq." shows `—` (no crash)

### Error State

- [ ] If the backend returns a 422 (missing exchange rate for a non-USD account), an inline error message is shown explaining the problem
- [ ] The breakdown table's native amount column still renders correctly even when USD equivalent is unavailable

### Edge Cases

- [ ] Navigating to the oldest available month works without errors
- [ ] A month where all accounts are USD (no exchange rates needed) renders correctly
- [ ] A month with no balance entries shows a clear empty state

---

## Definition of Done

- Month selector, summary cards, and breakdown table all present in `/reports`
- Net worth computation matches: assets − liabilities in USD
- Per-account USD equivalent computed correctly: amount / rate (rounded), or native amount for USD
- Backend 422 errors surface as an inline message rather than a crash
- All automated checks pass
- No regressions to any other page
