# Phase 11 — Accounts UI: Requirements

## Scope

### Included

The existing placeholder `AccountsPage` becomes fully functional.

| Page | Route | Operations |
|------|-------|------------|
| Accounts | `/accounts` | List, create, edit, delete (cascade) |

**Account fields:**

| Field | Type | Notes |
|-------|------|-------|
| id | integer | PK, auto-assigned |
| name | string | Required; must be unique |
| institution_id | integer | FK → Institution; displayed as institution name in table |
| currency_code | string | FK → Currency; displayed as currency code in table |
| side | `asset` \| `liability` | Required |
| status | `active` \| `closed` | Default: `active` |
| tag_ids | integer[] | FK → Tag[]; multi-select; optional |

The list view includes two **client-side filters** rendered as dropdowns above the table:
- **Status**: All / Active / Closed
- **Tag**: All / &lt;tag name&gt;

Filters are combined (AND logic) and are local to the page (not persisted to the URL).

**Closed accounts are visually dimmed** (`opacity-50` on the table row).

### Not Included

- Balances page (Phase 12)
- Server-side pagination, sorting, or text search
- Any backend changes — the API is complete

---

## Decisions

### Forms: modal dialogs
Create and edit forms open in a `shadcn/ui` `Dialog`. Same pattern as Phase 10. The list stays visible behind it.

### Institution and currency fields: dropdowns
Both are `shadcn/ui Select` elements backed by `GET /institutions` and `GET /currencies`. These lists are fetched once and cached by TanStack Query alongside the accounts list.

### Tags: inline checkboxes
Tags are shown as a labelled list of checkboxes inside the Dialog, using `shadcn/ui Checkbox` + `Label`. No new external dependency; `Checkbox` is added via `npx shadcn@latest add checkbox`.

### Status and tag list filters: `shadcn/ui Select`
Two `Select` dropdowns rendered above the table (not inline with the filter bar of previous pages — these are value-based, not text-based). `Select` is added via `npx shadcn@latest add select`.

### Delete: cascade preview
Same two-step pattern as institution delete in Phase 10:
1. `DELETE /accounts/{id}` (no `?confirm=true`) → `{ balances_to_delete }` preview
2. `AlertDialog` names the account and shows the balance count
3. On confirm → `DELETE /accounts/{id}?confirm=true` → 204 (no body)

The preview call is awaited imperatively (not a mutation) before opening the dialog, exactly as `InstitutionsPage` handles it.

### Data fetching
All data is fetched client-side in full and filtered locally:
- `useQuery(['accounts'])` → `GET /accounts` (full list)
- `useQuery(['institutions'])` → `GET /institutions` (for form dropdown and name lookup)
- `useQuery(['currencies'])` → `GET /currencies` (for form dropdown and code display)
- `useQuery(['tags'])` → `GET /tags` (for form checkboxes and tag name lookup in table)

Mutations invalidate `['accounts']` on success.

---

## Context

### Copy / tone
Same as other pages: plain action verbs, short messages.

- **Empty state (no accounts at all):** `"No accounts yet."` with an **Add account** button.
- **Empty state (filters yield no results):** `"No accounts match the selected filters."`
- **Delete confirmation (with balances):** `"Delete account "Savings"? This will also delete N balance(s). This cannot be undone."`
- **Delete confirmation (no balances):** `"Delete account "Savings"? This cannot be undone."`
- **Inline form validation:** `"Name is required."`, `"Select an institution."`, `"Select a currency."`, `"Select a side."`
- **Mutation errors:** inline banner below the form (same as Phase 10 pages).

### Stack pointers
- API types and query functions: `src/api/accounts.ts`
- Page: `src/pages/AccountsPage.tsx`
- Follow patterns from `InstitutionsPage.tsx` (cascade delete) and `TagsPage.tsx` (edit dialog)
- Reuse `Badge` for tag display in the table (already installed)
- New shadcn/ui components to add: `Select`, `Checkbox`
