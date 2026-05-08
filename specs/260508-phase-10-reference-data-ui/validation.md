# Phase 10 — Reference Data UI: Validation

## Automated

- [ ] `just frontend-typecheck` passes with zero errors
- [ ] `just frontend-lint` passes with zero warnings/errors
- [ ] `just check` passes (backend tests + lint + typecheck + frontend lint + frontend typecheck)

---

## Manual Walkthrough

Start both servers (`just dev` and `just frontend-dev`) and exercise each page.

### Currencies (`/currencies`)

- [ ] Page loads and displays existing currencies from the API
- [ ] Client-side filter narrows rows as you type; clearing the input restores all rows
- [ ] Filter with no matches shows empty state message
- [ ] **Add currency** opens a dialog; submitting with a new valid code + name creates the record and closes the dialog; the new row appears in the list without a page reload
- [ ] Submitting a duplicate currency code surfaces an error (inline or banner) — does not navigate away
- [ ] Submitting with an empty code or name shows inline validation error
- [ ] **Delete** button on a row opens a confirmation dialog naming the currency code
- [ ] Confirming the delete removes the row from the list; cancelling does nothing

### Tags (`/tags`)

- [ ] Page loads and displays existing tags
- [ ] Client-side filter works on name
- [ ] **Add tag** dialog: submitting creates a new tag; it appears in the list
- [ ] **Edit** (pencil icon): dialog pre-populates with current name; saving updates the row in place
- [ ] Delete confirmation dialog names the tag; confirming removes it

### Institutions (`/institutions`)

- [ ] Page loads and displays existing institutions
- [ ] Client-side filter works on name
- [ ] **Add institution** dialog: submitting with a valid name creates the institution
- [ ] **Edit**: dialog pre-populates with current name; saving updates the row
- [ ] Delete — institution with **no accounts**:
  - [ ] Confirmation dialog shows `0 account(s) and 0 balance(s)` will be deleted
  - [ ] Confirming deletes the institution
- [ ] Delete — institution with **linked accounts**:
  - [ ] Confirmation dialog shows the correct account and balance counts
  - [ ] Confirming deletes the institution and its accounts (verify via Accounts page or API)
  - [ ] Cancelling leaves everything intact

### Cross-cutting

- [ ] Empty state is shown on each page when the list has no records (or when a filter yields no matches)
- [ ] Navigating between pages using the sidebar and returning preserves nothing unexpected (filter resets, no stale data)
- [ ] No TypeScript `any` escapes introduced; all API response shapes are explicitly typed

---

## Definition of Done

All automated checks pass, all manual checklist items above are ticked, and the three placeholder pages are replaced with working UIs. No regressions in other pages.
