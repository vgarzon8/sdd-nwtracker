# Phase 11 — Accounts UI: Validation

## Automated

- [x] `just frontend-typecheck` passes with zero errors
- [x] `just frontend-lint` passes with zero warnings/errors
- [x] `just check` passes (backend tests + lint + typecheck + frontend lint + frontend typecheck)

---

## Manual Walkthrough

Start both servers (`just dev` and `just frontend-dev`) and exercise the Accounts page.

### Accounts (`/accounts`)

- [x] Page loads and displays existing accounts from the API
- [x] Status filter: selecting "Active" shows only active accounts; "Closed" shows only closed; "All" restores full list
- [x] Tag filter: selecting a tag shows only accounts with that tag; "All" restores full list
- [x] Combining status + tag filters applies AND logic (e.g. Active + Tag X shows only accounts that are both active and tagged X)
- [x] Closed accounts are visually dimmed in the list
- [x] **Add account** opens a Dialog with empty fields; Institution, Currency, Side, Status, and Tag dropdowns/lists are populated
- [x] Submitting a valid new account creates the record and closes the dialog; the new row appears without a page reload
- [x] Submitting a duplicate account name surfaces a server error (inline banner) — does not navigate away
- [x] Submitting with empty required fields (name, institution, currency, side) shows inline validation errors
- [x] **Edit** (pencil icon): Dialog pre-populates all fields correctly, including tags; saving updates the row in place
- [x] Changing an account's status from active to closed dims the row after save; changing it back restores full opacity
- [x] **Delete** button awaits preview then opens an AlertDialog naming the account
- [x] AlertDialog shows balance count: "This will also delete N balance(s)." when N > 0; omits that line when N = 0
- [x] Confirming delete removes the row from the list; cancelling leaves it intact

### Edge Cases

- [x] Empty state (no accounts at all): shows "No accounts yet." with an Add account button
- [x] Empty state (filters yield no results): shows "No accounts match the selected filters."
- [x] Institutions and currencies dropdowns reflect current reference data (add a new institution, verify it appears in the form)

### Cross-cutting

- [x] No TypeScript `any` escapes introduced; all API response shapes explicitly typed
- [x] Navigating away and back resets filter state; no stale data shown
- [x] Other pages (currencies, tags, institutions) remain functional

---

## Definition of Done

All automated checks pass, all manual checklist items above are ticked, and the `AccountsPage` placeholder is replaced with a working UI. No regressions in other pages.
