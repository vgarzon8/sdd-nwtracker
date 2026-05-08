# Phase 10 — Reference Data UI: Plan

## Task Groups

Each group is independently implementable after the API layer (Group 1) is done.

---

### Group 1 — API Layer

Add TypeScript types and query/mutation functions for each resource. No UI yet.

1. Create `src/api/currencies.ts`
   - Type: `Currency { code: string; name: string }`
   - `listCurrencies()` → `GET /currencies`
   - `createCurrency(body)` → `POST /currencies`
   - `deleteCurrency(code)` → `DELETE /currencies/{code}`

2. Create `src/api/tags.ts`
   - Type: `Tag { id: number; name: string; description: string | null }`
   - `listTags()` → `GET /tags`
   - `createTag(body)` → `POST /tags`
   - `updateTag(id, body)` → `PUT /tags/{id}`
   - `deleteTag(id)` → `DELETE /tags/{id}`

3. Create `src/api/institutions.ts`
   - Type: `Institution { id: number; name: string; country: string | null; notes: string | null }`
   - Type: `InstitutionDeletePreview { account_count: number }` (shape returned by DELETE without `?confirm=true`)
   - `listInstitutions()` → `GET /institutions`
   - `createInstitution(body)` → `POST /institutions`
   - `updateInstitution(id, body)` → `PUT /institutions/{id}`
   - `deleteInstitutionPreview(id)` → `DELETE /institutions/{id}` (no confirm param)
   - `deleteInstitutionConfirm(id)` → `DELETE /institutions/{id}?confirm=true`

---

### Group 2 — Currencies Page

Replace the `CurrenciesPage` placeholder.

4. Build `CurrenciesPage.tsx`
   - `useQuery` to fetch and display currencies in a `Table` (Code, Name, Actions)
   - Client-side text filter `<Input>` above the table; filters on code or name (case-insensitive)
   - Empty state when list is empty or filter has no matches
   - **Add currency** button → opens a `Dialog` with Code + Name fields
   - `useMutation` for create; invalidates `['currencies']` on success
   - Delete button per row → `AlertDialog` confirmation → `useMutation` for delete

---

### Group 3 — Tags Page

Replace the `TagsPage` placeholder.

5. Build `TagsPage.tsx`
   - `useQuery` + `Table` (Name, Description, Actions)
   - Client-side text filter (name or description)
   - Empty state
   - **Add tag** button → `Dialog` with Name + Description fields
   - Edit (pencil icon) per row → same `Dialog` pre-populated
   - `useMutation` for create and update; both invalidate `['tags']`
   - Delete per row → `AlertDialog` showing tag name → `useMutation`

---

### Group 4 — Institutions Page

Replace the `InstitutionsPage` placeholder.

6. Build `InstitutionsPage.tsx`
   - `useQuery` + `Table` (Name, Country, Notes, Actions)
   - Client-side text filter (name, country, or notes)
   - Empty state
   - **Add institution** button → `Dialog` with Name, Country, Notes fields
   - Edit per row → same `Dialog` pre-populated
   - `useMutation` for create and update; both invalidate `['institutions']`
   - Delete per row → two-step cascade flow:
     a. Call `deleteInstitutionPreview(id)` to get account count
     b. Show `AlertDialog` with count in the message
     c. On confirm, call `deleteInstitutionConfirm(id)` and invalidate `['institutions']`

---

### Group 5 — QA

7. Run `just frontend-typecheck` — fix any TypeScript errors
8. Run `just frontend-lint` — fix any lint errors
9. Run `just check` — confirm all backend tests still pass and the full suite is green
