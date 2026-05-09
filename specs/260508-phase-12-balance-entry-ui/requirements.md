# Phase 12 — Balance Entry UI: Requirements

## Scope

### Included

The existing placeholder `BalancesPage` becomes fully functional.

| Page | Route | Operations |
|------|-------|------------|
| Balances | `/balances` | View by month, create/edit balance amounts inline |

**Balance row fields displayed:**

| Field | Source | Notes |
|-------|--------|-------|
| Account name | `account_name` on `BalanceReadDetail` | |
| Institution | looked up via `institution_id` from institutions cache | displayed as institution name |
| Currency | `currency_code` on `BalanceReadDetail` | |
| Side | `side` on `BalanceReadDetail` | `asset` or `liability`; displayed capitalized |
| Amount | `amount` on `BalanceReadDetail`, or `null` if no balance exists | Integer whole-currency units; editable inline |

The list shows **all active accounts** for the selected month. Accounts that already have a balance entry show the amount; accounts with no entry for that month show a dash (`—`). In both cases the amount field is clickable.

Only **active** accounts are shown. Closed accounts are omitted.

### Not Included

- Roll-forward action (Phase 12 deferred — planned for a later phase)
- Transfer form (deferred)
- Server-side pagination or sorting
- Exchange-rate / USD conversion column
- Any backend changes — the API is complete

---

## Decisions

### Month selector

A simple prev/next control with the current month displayed as `MMM YYYY` (e.g. "Jan 2026"). Implemented with two icon buttons (`ChevronLeftIcon`, `ChevronRightIcon`) flanking a plain text label.

**Default month:** On first load, fetch `GET /balances` (no month param) to obtain all available months; pick the lexicographically greatest `YYYY-MM`. If the response is empty (no balance data at all), default to the current calendar month.

### Inline click-to-edit

Clicking anywhere in the Amount cell activates an inline `<input type="number">` pre-filled with the existing amount (or empty for new entries). No dialog is opened.

Save triggers:
- **Enter key** — commits the value
- **Blur** (clicking away) — commits the value

Cancel trigger:
- **Escape key** — restores the previous value and exits edit mode without saving

On commit:
- If the account already has a balance for the month → `PUT /balances/{id}` with `{ amount }`
- If no balance exists yet → `POST /balances` with `{ account_id, month, amount }`
- Mutations invalidate `['balances', selectedMonth]` on success
- An empty or unchanged value on blur is discarded (no API call)

### Data fetching

- `useQuery(['balances-months'])` → `GET /balances` — fetches all balances (flat list) to derive the set of months with data; used only to pick the initial month.
- `useQuery(['balances', selectedMonth])` → `GET /balances?month=YYYY-MM` — returns `BalanceReadDetail[]` for the selected month.
- `useQuery(['accounts'])` → `GET /accounts` — fetches all accounts; filtered client-side to `status === 'active'`.
- `useQuery(['institutions'])` → `GET /institutions` — for institution name lookup in the table.

The accounts and balances lists are merged client-side: for each active account, find the matching balance entry (by `account_id`) in the month's balance list.

### No delete

Balances cannot be deleted from this UI. The API supports it, but balance deletion is not in scope for this phase.

---

## Context

### Copy / tone

Same as other pages: plain action verbs, short messages.

- **Empty state (no accounts at all):** `"No active accounts found."` with a link to the Accounts page.
- **Empty state (month has no data yet):** Not shown as a special state — the table still renders all active accounts with `—` amounts (ready for entry).
- **Saving indicator:** While a mutation is pending, the cell shows a spinner or disabled input.
- **Mutation error:** Inline text below the row's amount cell: `"Failed to save."` (auto-clears when the user edits again).

### Stack pointers

- API types and query functions to create: `src/api/balances.ts`
- Page to replace: `src/pages/BalancesPage.tsx`
- Follow `AccountsPage.tsx` for query/mutation patterns
- No new shadcn/ui components needed — `Input`, `Button`, `Table`, `Badge` are already installed
- Month navigation: use `lucide-react` icons `ChevronLeftIcon` and `ChevronRightIcon` (already available)
- Month display: derive `MMM YYYY` label client-side from the `YYYY-MM` string using the local-time `Date(y, m-1, 1)` constructor — avoids the UTC-midnight timezone bug that `new Date('YYYY-MM-DD')` causes in timezones behind UTC
