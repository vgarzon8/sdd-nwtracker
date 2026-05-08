# Phase 11 — Accounts UI: Plan

## Task Group 1 — API Layer

1.1 Create `src/api/accounts.ts`:
  - TypeScript types: `AccountSide` (`"asset" | "liability"`), `AccountStatus` (`"active" | "inactive"`), `Account`, `AccountCreate`, `AccountUpdate`, `AccountDeletePreview`
  - `listAccounts()` → `GET /accounts`
  - `createAccount(body: AccountCreate)` → `POST /accounts`
  - `updateAccount(id: number, body: AccountUpdate)` → `PUT /accounts/{id}`
  - `deleteAccountPreview(id: number)` → `DELETE /accounts/{id}` (no confirm; returns JSON via `client.del_json`)
  - `deleteAccountConfirm(id: number)` → `DELETE /accounts/{id}?confirm=true` (returns 204 via `client.del`)

---

## Task Group 2 — shadcn/ui Components

2.1 Run `npx shadcn@latest add select` from `frontend/`
2.2 Run `npx shadcn@latest add checkbox` from `frontend/`
2.3 Verify files land in `frontend/src/components/ui/` (not `frontend/@/`); move if needed
2.4 Check for ESLint `react-refresh/only-export-components` issues in generated files; add disable comment if present (same fix as `badge.tsx` and `button.tsx` in Phase 10)

---

## Task Group 3 — Accounts Page

3.1 Replace `src/pages/AccountsPage.tsx` placeholder with full implementation:
  - `useQuery` for accounts, institutions, currencies, tags
  - Two `Select` filter dropdowns: Status (All / Active / Inactive) and Tag (All / tag name); state held in `useState`
  - Client-side filter logic combining both filters (AND)
  - `shadcn/ui Table` with columns: Name, Institution, Currency, Side, Tags, Actions (edit + delete)
  - `opacity-50` on `<tr>` for inactive accounts
  - Tags column: one `Badge` per tag name (look up from tags list by id)
  - Institution column: institution name looked up from institutions list by id
  - Empty state (no accounts): message + Add account button
  - Empty state (filter yields nothing): "No accounts match the selected filters."

3.2 Create/edit Dialog form:
  - `useState` for `dialogOpen` and `editTarget` (null = create mode)
  - Fields: Name (`Input`), Institution (`Select`), Currency (`Select`), Side (`Select`: Asset / Liability), Status (`Select`: Active / Inactive), Tags (mapped list of `Checkbox` + `Label`)
  - `tag_ids` state: `number[]`; checkbox checked iff id is in array
  - Pre-populate all fields when `editTarget !== null`
  - Client-side required field validation: name, institution, currency, side
  - `formError` state for server errors; displayed as inline banner
  - `createMutation` / `updateMutation` via `useMutation`; on success: close dialog, `invalidateQueries(['accounts'])`
  - Primary button: "Add account" (create) / "Save changes" (edit); Cancel button closes without saving

3.3 Delete flow:
  - `deleteState`: `{ account: Account; preview: AccountDeletePreview } | null`
  - Click Delete → `await deleteAccountPreview(id)` → set `deleteState`
  - `AlertDialog` controlled by `deleteState !== null`; body: account name + balance count
  - Confirm → `deleteAccountConfirm(id)` → `invalidateQueries(['accounts'])` → clear `deleteState`
  - Cancel → clear `deleteState`

---

## Task Group 4 — Validation & QA

4.1 Run `just frontend-typecheck` — zero errors
4.2 Run `just frontend-lint` — zero warnings/errors
4.3 Run `just check` — all checks pass
4.4 Mark automated checks in `validation.md`
4.5 Manual walkthrough
