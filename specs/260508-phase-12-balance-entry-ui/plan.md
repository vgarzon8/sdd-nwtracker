# Phase 12 — Balance Entry UI: Plan

## Task Group 1 — API Layer

Create `frontend/src/api/balances.ts` with all types and query functions needed by the page.

1. Define types mirroring the backend response shapes:
   - `Balance` (flat, no account detail) — from `GET /balances` without month param
   - `BalanceDetail` — from `GET /balances?month=YYYY-MM`; includes `account_name`, `institution_id`, `currency_code`, `side`
   - `BalanceCreate` — `{ account_id, month, amount }`
   - `BalanceUpdate` — `{ amount }`
2. Define query functions:
   - `listBalancesFlat()` → `client.get<Balance[]>('/balances')`
   - `listBalancesByMonth(month: string)` → `client.get<BalanceDetail[]>(\`/balances?month=\${month}\`)`
   - `createBalance(body: BalanceCreate)` → `client.post<Balance>('/balances', body)`
   - `updateBalance(id: number, body: BalanceUpdate)` → `client.put<Balance>(\`/balances/\${id}\`, body)`
3. Commit: `feat(phase-12): balances API layer — types and query functions`

---

## Task Group 2 — BalancesPage Implementation

Replace the placeholder `src/pages/BalancesPage.tsx` with the full implementation.

1. **State**: `selectedMonth: string`, `editingId: string | null` (composite key `\`new-\${accountId}\`` or `\`\${balanceId}\``), `editValue: string`, `saveError: Record<string, string>`
2. **Queries**:
   - `useQuery(['balances-months'])` → `listBalancesFlat()` — derive initial month from max month in result; fall back to current calendar month if empty
   - `useQuery(['balances', selectedMonth])` → `listBalancesByMonth(selectedMonth)` — re-fetches when month changes
   - `useQuery(['accounts'])` → `listAccounts()` — filter to `status === 'active'` client-side
   - `useQuery(['institutions'])` → `listInstitutions()` — for institution name lookup
3. **Month selector**: prev/next `Button` (variant `ghost`, size `icon`) + `ChevronLeftIcon` / `ChevronRightIcon` + month label between them
4. **Merged row list**: for each active account (sorted by name), find the matching `BalanceDetail` by `account_id`. Produce a merged row: `{ account, balance: BalanceDetail | null }`.
5. **Table**: columns — Name, Institution, Currency, Side, Amount. Amount cell:
   - Viewing: show formatted amount or `—` if no balance; entire cell is clickable to enter edit mode
   - Editing: `<Input type="number">` focused on mount; `onKeyDown` handles Enter (save) and Escape (cancel); `onBlur` saves
6. **Save logic** (called on Enter/blur):
   - If value is empty or unchanged: exit edit mode, no API call
   - If balance exists: `updateMutation.mutate({ id: balance.id, amount: Number(value) })`
   - If no balance: `createMutation.mutate({ account_id: account.id, month: selectedMonth, amount: Number(value) })`
7. **Mutations**: both invalidate `['balances', selectedMonth]` and `['balances-months']` on success; set `saveError[key]` on error
8. **Empty state**: if `activeAccounts.length === 0`, show `"No active accounts found."` with a link (`<a href="/accounts">`) to the Accounts page
9. Commit: `feat(phase-12): BalancesPage — month selector and inline balance entry`

---

## Task Group 3 — Validation & Spec Update

1. Run `just frontend-typecheck` — fix any type errors
2. Run `just frontend-lint` — fix any lint errors
3. Run `just check` — confirm all automated checks pass
4. Start both servers and perform the manual walkthrough in `validation.md`
5. Tick all completed items in `validation.md`
6. Commit: `docs(phase-12): validation checklist complete`
