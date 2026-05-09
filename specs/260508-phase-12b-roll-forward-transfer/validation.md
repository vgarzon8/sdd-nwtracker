# Phase 12b — Roll-Forward & Transfer: Validation

## Automated

- [x] `just test` passes (153 passed — all backend tests green, including existing roll-forward and transfer tests)
- [x] `just frontend-typecheck` passes with no errors
- [x] `just frontend-lint` passes with no errors

---

## Manual Walkthrough

### Setup

- [ ] At least two active accounts exist with balances in some prior month (use `just db-seed` if needed)
- [ ] Dev servers running: `just dev` and `just frontend-dev`

### Roll-Forward

- [ ] Navigate to `/balances`; select a month that has no balances (e.g., a future month)
- [ ] **Roll forward** button is visible in the page header and enabled
- [ ] Clicking it opens a dialog showing the correct source month (most recent month with data) and the correct count of accounts to fill
- [ ] Clicking **Cancel** closes the dialog without making any changes
- [ ] Clicking **Confirm** calls `POST /balances/roll-forward`, closes the dialog, and the balance list refreshes to show the copied balances
- [ ] Re-opening the dialog after roll-forward: count shows 0 (all accounts already filled); Confirm still works (backend no-ops, returns `inserted: 0`)
- [ ] Navigate to the month that **already has** full balances: **Roll forward** button is still visible but disabled if no prior month with data exists

### Roll-Forward — Edge Cases

- [ ] When currently on the oldest month in the dataset (no prior month), the **Roll forward** button is disabled
- [ ] When all active accounts already have entries for the selected month, the dialog correctly shows count = 0

### Transfer

- [ ] **Transfer** button is visible in the page header at all times
- [ ] Clicking it opens the transfer dialog
- [ ] **From account** dropdown only shows active accounts that have a balance for the current month
- [ ] **To account** dropdown shows all active accounts except the selected from-account
- [ ] Selecting the same account for both from and to is prevented (either by dropdown filtering or inline validation)
- [ ] Entering a non-positive or non-integer amount shows a client-side validation error and blocks submit
- [ ] Submitting a valid transfer closes the dialog and the balance list refreshes with updated amounts
- [ ] If the backend returns an error (e.g., from-account has no balance), the error message is shown in the dialog footer

### Transfer — Edge Cases

- [ ] If no active accounts have a balance for the selected month, the **From account** dropdown is empty and the form shows an appropriate message
- [ ] Clicking **Cancel** at any time closes the dialog without making changes

---

## Definition of Done

- Both buttons appear in the `BalancesPage` header
- Roll-forward confirm dialog accurately previews source month and fill count before committing
- Transfer dialog validates inputs client-side and surfaces backend errors inline
- All automated checks pass
- No regressions to the existing inline balance-editing behavior
