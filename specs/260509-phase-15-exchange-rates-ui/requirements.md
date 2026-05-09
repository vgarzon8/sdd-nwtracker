# Phase 15 — Exchange Rates UI: Requirements

## Scope

### Included

- New `/exchange-rates` route and `ExchangeRatesPage.tsx`
- Month selector (prev/next chevrons) defaulting to most recent month with balance data
- Table showing all non-USD currencies with their exchange rate for the selected month; currencies with no rate for that month display `—`
- **Inline create**: clicking `—` opens an inline decimal input; Enter or blur saves (calls `POST /exchange-rates`); Escape cancels
- **Inline edit**: clicking an existing rate opens the same inline input; Enter or blur saves (calls `PUT /exchange-rates/{id}`); Escape cancels
- **Delete**: trash icon button on rows with an existing rate; clicking opens a confirmation dialog before calling `DELETE /exchange-rates/{id}`
- USD is hidden — it is the base currency (implicit rate 1.0) and cannot be managed here
- New API functions in `src/api/exchange-rates.ts`: `createExchangeRate`, `updateExchangeRate`, `deleteExchangeRate`
- "Exchange Rates" sidebar entry added under the Reference Data group

### Not included

- Bulk entry or paste
- Rate history per currency (month navigation is the history mechanism)
- Import from external source or auto-fill
- Filtering by currency on this page (month navigation is the primary axis)

---

## Decisions

| Decision | Choice | Reason |
|---|---|---|
| Page organization | By month | Consistent with Balance Entry; rates are entered monthly so month is the natural primary axis |
| Editing UX | Inline (click-to-edit) | Same pattern as Balance Entry; avoids modal overhead for simple numeric entry |
| USD visibility | Hidden | USD is the base currency; its rate is always implicit 1.0 and is never stored in the DB |
| Currency list | All non-USD currencies | Ensures the user can see which currencies still need a rate for the month |
| Default month | Most recent month with balance data | Same convention used by Balance Entry and Reports; keeps the month context consistent |
| Rate precision | Decimal input (up to 4 places) | Backend stores `Numeric(10,4)`; display rounds to 4 places |
| Delete flow | Confirm dialog | Destructive action; low risk but consistent with other delete patterns in the app |
| Rate validation | Must be a positive number | Backend enforces this; frontend validates before submit to give immediate feedback |
| `rate` display | `Number(existing.rate).toFixed(4)` | Pydantic v2 serializes `Decimal` fields as JSON strings, not numbers; `toFixed` would throw without coercion |
| Commit-on-blur double-fire | Guard `commitEdit` with `if (createMutation.isPending \|\| updateMutation.isPending) return` | Setting `disabled={isPending}` on a focused `<Input>` triggers `onBlur` in browsers, which fires `commitEdit` a second time while the first POST is still in flight — the duplicate request gets a 409 and shows "Failed to save" |

---

## Context

- **Stack**: TypeScript, React 19, TanStack Query, shadcn/ui, Tailwind CSS v4
- **Backend endpoints** (fully implemented):
  - `GET /exchange-rates?month=YYYY-MM` → `ExchangeRate[]` filtered to a month
  - `POST /exchange-rates` body: `{ currency_code, month, rate }` → 201 `ExchangeRate`; 409 if already exists
  - `PUT /exchange-rates/{id}` body: `{ rate }` → `ExchangeRate`
  - `DELETE /exchange-rates/{id}` → 204
- **Currencies endpoint**: `GET /currencies` already exists and is used by CurrenciesPage; use it to build the full currency list
- **Existing API file**: `src/api/exchange-rates.ts` already has `listExchangeRates(month)` and the `ExchangeRate` interface — extend it, don't replace it
- **Month default**: derive from the `["balances-months"]` query (same as BalancesPage) — `listBalancesFlat` from `src/api/balances.ts`
- **Inline edit pattern**: follow `BalancesPage.tsx` exactly — `editState: { key: string; value: string } | null`, controlled `Input`, `onBlur` commits, `onKeyDown` handles Enter/Escape, `autoFocus`
- **Pydantic Decimal serialization**: this backend serializes `Decimal` fields (e.g., `ExchangeRate.rate`) as JSON strings. Always wrap in `Number()` before arithmetic, `.toFixed()`, or comparison. Use `Number(a) === Number(b)` for unchanged-value checks.
- **No copy-style constraints**: labels should be plain and functional
