# Phase 12 — Balance Entry UI: Validation

## Automated

- [x] `just frontend-typecheck` passes with zero errors
- [x] `just frontend-lint` passes with zero warnings/errors
- [x] `just check` passes (backend tests + lint + typecheck + frontend lint + frontend typecheck)

---

## Manual Walkthrough

Start both servers (`just dev` and `just frontend-dev`) and navigate to `/balances`.

### Month selector

- [x] Page loads and defaults to the most recent month that has balance data
- [x] If no balance data exists at all, defaults to the current calendar month
- [x] Month label displays in `MMM YYYY` format (e.g. "Apr 2026") — timezone-safe constructor used
- [x] Clicking the left arrow decrements the month by one; clicking the right arrow increments by one
- [x] Navigating months updates the balance list immediately (re-fetches from the API)

### Balance list

- [x] All active accounts appear in the table, one row per account
- [x] Closed accounts are not shown
- [x] For accounts that have a balance entry for the selected month, the amount is displayed
- [x] For accounts with no entry for the selected month, the Amount column shows `—`
- [x] Institution name is resolved correctly (matches what's shown on the Accounts page)
- [x] Side column shows "Asset" or "Liability" (capitalized)

### Inline editing — existing balance

- [x] Clicking the amount cell of an account that has a balance activates an inline input pre-filled with the current amount
- [x] Pressing Enter saves the new value; the cell returns to display mode showing the updated amount
- [x] Clicking away (blur) saves the new value; same result as Enter
- [x] Pressing Escape cancels the edit; the original value is restored, no API call is made
- [x] Submitting an unchanged value on blur discards without an API call

### Inline editing — new balance (no entry yet)

- [x] Clicking the `—` in the Amount column activates an inline input (empty)
- [x] Entering a number and pressing Enter creates a new balance; the cell shows the amount
- [x] Entering a number and blurring creates the balance
- [x] Pressing Escape with an empty input cancels without creating a balance
- [x] Leaving the input empty and blurring discards without an API call

### Error handling

- [x] If a save fails (e.g. server error), an inline error message appears near the cell: `"Failed to save."`
- [x] The error clears when the user begins editing the same cell again

### Empty state

- [x] If there are no active accounts, the page shows `"No active accounts found."` with a link to `/accounts`

### Cross-cutting

- [x] No TypeScript `any` escapes introduced; all API response shapes explicitly typed
- [x] Navigating to another page and back resets to the default month (no stale selection persisted)
- [x] Other pages (accounts, institutions, etc.) remain functional after completing this phase

---

## Definition of Done

All automated checks pass, all manual checklist items above are ticked, and the `BalancesPage` placeholder is replaced with a working balance entry UI. No regressions in other pages.
