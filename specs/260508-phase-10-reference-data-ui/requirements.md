# Phase 10 — Reference Data UI: Requirements

## Scope

### Included

Three existing placeholder pages become fully functional:

| Page | Route | Operations |
|------|-------|------------|
| Currencies | `/currencies` | List, create, delete |
| Tags | `/tags` | List, create, edit, delete |
| Institutions | `/institutions` | List, create, edit, delete (cascade) |

**Currencies** — `code` is the primary key so there is no edit operation.

| Field | Type | Notes |
|-------|------|-------|
| code | string | 3-char ISO code, e.g. `USD` |
| name | string | Human-readable name, e.g. `US Dollar` |

**Tags** — fully editable.

| Field | Type | Notes |
|-------|------|-------|
| id | integer | PK, auto-assigned |
| name | string | Required |
| description | string | Optional |

**Institutions** — fully editable; delete cascades to accounts.

| Field | Type | Notes |
|-------|------|-------|
| id | integer | PK, auto-assigned |
| name | string | Required |
| country | string | Optional |
| notes | string | Optional |

All three list views include a **client-side text filter** (searches across all visible string columns).

### Not Included

- Accounts page (Phase 11)
- Any backend changes — the API is complete
- Server-side search or pagination
- Sorting controls (default order from the API is acceptable)

---

## Decisions

### Forms: modal dialogs
Create and edit forms open in a `shadcn/ui` `Dialog`. The list stays visible behind it. Each dialog contains a labelled form with a primary action button and a Cancel button.

### Client-side filter
A single text `<input>` above each list filters rows as the user types. Filtering is case-insensitive and matches any column value. The filter state is local to the page (not persisted to the URL).

### Delete: simple confirmation
For Tags and Currencies, a brief inline confirmation is shown before the DELETE call is made (e.g., a `shadcn/ui` `AlertDialog` — "Delete this tag? This cannot be undone.").

### Institutions: cascade delete with preview
The institution delete flow uses the two-step backend protocol:
1. `DELETE /institutions/{id}` (without `?confirm=true`) — returns a preview showing how many accounts would be deleted.
2. User sees the count in the confirmation dialog.
3. On confirm, `DELETE /institutions/{id}?confirm=true` — executes the delete.

### Data fetching
TanStack Query (`useQuery` / `useMutation`) for all server state. Mutations call `queryClient.invalidateQueries` on success to refresh the list.

### shadcn/ui components to use
`Table`, `Dialog`, `AlertDialog`, `Button`, `Input`, `Label`, `Badge` (for currency codes). These are already available via the phase-9 scaffold.

---

## Context

### Copy / tone
Short, human-readable copy. Avoid jargon. Use plain action verbs: "Add", "Save", "Delete", "Cancel".

- **Empty states:** one sentence + a call to action button.
  - Example: `"No currencies yet."` with an **Add currency** button.
- **Delete confirmations:** name what will be deleted.
  - Tag: `"Delete tag "Budget"? This cannot be undone."`
  - Institution cascade: `"Deleting "Chase" will also delete 3 account(s). This cannot be undone."`
- **Form validation errors:** brief inline message below the field, e.g. `"Code is required."` (rely on HTML5 `required` and display server 422 errors inline).
- **Mutation errors:** surface via a toast or inline banner — pick whichever shadcn/ui pattern is simpler to add without a new dependency. An inline error message below the form is acceptable.

### Stack pointers
- Components live in `src/components/`; page files in `src/pages/`.
- API query functions go in `src/api/` (one file per resource, following `client.ts`).
- TypeScript types should mirror the backend response shapes (no code generation required; write them by hand).
- `cn()` utility is already available via `src/lib/utils.ts`.
