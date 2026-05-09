# Phase 15 — Exchange Rates UI: Validation

## Automated

- [x] `just test` passes (153 passed — all backend tests green, no regressions)
- [x] `just frontend-typecheck` passes with no errors
- [x] `just frontend-lint` passes with no errors

---

## Manual Walkthrough

### Setup

- [ ] Dev servers running: `just dev` and `just frontend-dev`
- [ ] At least two non-USD currencies exist (e.g., EUR, CNY)
- [ ] Balance data exists for at least one month (to test default month derivation)

### Navigation

- [ ] "Exchange Rates" appears in the sidebar under Reference Data
- [ ] Clicking it navigates to `/exchange-rates`
- [ ] Page title is "Exchange Rates"

### Month selector

- [ ] Page loads with the most recent month that has balance data selected
- [ ] Prev/next chevron buttons change the displayed month
- [ ] Month label formats correctly (e.g., "May 2026")

### Table display

- [ ] All non-USD currencies are listed (one row per currency)
- [ ] USD does not appear in the list
- [ ] Currencies with no rate for the selected month show `—` in the Rate column
- [ ] Currencies with an existing rate show the rate formatted to 4 decimal places

### Inline create (new rate)

- [ ] Clicking `—` opens an inline input in that cell
- [ ] Entering a valid positive decimal and pressing Enter saves the rate (calls POST)
- [ ] Blur also saves
- [ ] Pressing Escape cancels and restores `—`
- [ ] Entering a blank value on Enter/blur cancels without saving
- [ ] Entering a non-numeric or zero/negative value cancels without saving (or shows an error)

### Inline edit (existing rate)

- [ ] Clicking an existing rate opens an inline input pre-populated with the current value
- [ ] Changing the value and pressing Enter saves (calls PUT)
- [ ] Blur also saves
- [ ] Pressing Escape restores the original value
- [ ] Submitting the same value as before cancels without a network call

### Delete

- [ ] Trash icon appears on rows with an existing rate
- [ ] Clicking trash icon opens a confirmation dialog
- [ ] Confirmation dialog shows the currency code and month
- [ ] Clicking "Cancel" closes the dialog with no change
- [ ] Clicking "Confirm" calls DELETE and removes the rate; cell reverts to `—`

### Edge cases

- [ ] Navigating to a month with no rates at all shows all currencies with `—`
- [ ] Empty state shown if no non-USD currencies exist (with link to /currencies)
- [ ] No regressions on other pages (Balances, Reports, Reference Data)

---

## Definition of Done

- `/exchange-rates` page is accessible from the sidebar
- Month selector defaults to most recent month with balance data
- All non-USD currencies are listed; USD is hidden
- Inline create, edit, and delete all work correctly
- All automated checks pass
- No regressions to any other page
