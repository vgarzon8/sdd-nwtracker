# Phase 12b — Roll-Forward & Transfer: Requirements

## Scope

### Included

- **Roll-forward button** in the balance list page header, alongside the month selector area
- **Roll-forward confirm dialog** that shows the source month and the count of active accounts that will be filled before committing
- **Transfer button** in the balance list page header
- **Transfer dialog form** with from-account, to-account (dropdowns), and amount fields, pre-filled to the current month
- New TypeScript types and API functions in `src/api/balances.ts` for both operations
- Query invalidation after both operations so the balance list refreshes

### Not included

- A backend dry-run / preview endpoint for roll-forward (count is derived client-side)
- Roll-forward to a month other than the currently selected month
- Undo / reversal of roll-forward
- Transfer between accounts in different currencies (backend already enforces this; the UI shows a backend error if it happens)
- A separate route or page for either operation

---

## Decisions

| Decision | Choice | Reason |
|---|---|---|
| Roll-forward confirmation count | Computed client-side from already-fetched `activeAccounts` and `monthBalances` | No extra API call needed; both datasets are already in the component |
| Source month in dialog | Derived client-side: max month in `allBalances` that is before `effectiveMonth` | Same data already fetched for the default-month logic |
| Transfer "from account" options | Filtered to active accounts **with** a balance for the current month | Backend returns 422 if from-account has no balance; pre-filtering gives better UX |
| Transfer "to account" options | All active accounts except the selected from-account | Backend handles same-account validation |
| Transfer amount | Positive integer (whole currency units); validated client-side before submit | Consistent with the integer-amounts convention throughout the app |
| Dialog component | shadcn/ui `Dialog` (already in `src/components/ui/dialog.tsx`) | No new dependencies |
| Select component | shadcn/ui `Select` (already in `src/components/ui/select.tsx`) | No new dependencies |
| Error display | Inline error text below the form field or dialog footer | Consistent with existing inline save-error pattern in `BalancesPage` |

---

## Context

- **Stack**: TypeScript, React 19, TanStack Query, shadcn/ui, Tailwind CSS v4
- **Existing patterns to follow**:
  - `useMutation` + `queryClient.invalidateQueries` pattern already used in `BalancesPage` for create/update
  - Dialog pattern: see `AccountsPage.tsx` for create/edit dialog usage
  - Inline error: see `saveErrors` pattern in `BalancesPage`
- **Backend endpoints** (both fully implemented and tested):
  - `POST /balances/roll-forward` — body `{month: string}` → `{months: [{month, inserted, skipped}]}`
  - `POST /balances/transfer` — body `{from_account_id, to_account_id, amount, month}` → `{from_balance, to_balance}`
- **No copy-style constraints**; labels should be plain and functional
- **Open question logged for implementation**: if no prior month with balances exists, the roll-forward button should be disabled (or show an appropriate empty-state message in the dialog)
