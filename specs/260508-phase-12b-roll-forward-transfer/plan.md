# Phase 12b — Roll-Forward & Transfer: Plan

## 1. API Layer (`src/api/balances.ts`)

1.1 Add `RollForwardResult` and `RollForwardResponse` TypeScript interfaces matching the backend response shape (`{months: [{month, inserted, skipped}]}`).

1.2 Add `TransferRequest` and `TransferResponse` interfaces.

1.3 Add `rollForward(month: string)` function: `POST /balances/roll-forward`.

1.4 Add `transfer(body: TransferRequest)` function: `POST /balances/transfer`.

---

## 2. Roll-Forward Dialog Component

2.1 Create `RollForwardDialog` (inline in `BalancesPage.tsx` or extracted to `src/components/RollForwardDialog.tsx`).
  - Props: `open`, `onClose`, `targetMonth`, `sourceMonth`, `accountsToFillCount`
  - Shows: "Roll forward to {targetMonth}" heading, "Copies {sourceMonth} balances for {N} active accounts with no {targetMonth} entry.", Cancel + Confirm buttons
  - On Confirm: fires the roll-forward mutation; closes on success
  - Shows API error in dialog footer if the mutation fails

2.2 Wire up `useMutation` for `rollForward` in `BalancesPage`:
  - On success: invalidate `["balances", effectiveMonth]` and `["balances-months"]`, then show dialog success and close

---

## 3. Transfer Dialog Component

3.1 Create `TransferDialog` (inline or extracted).
  - Props: `open`, `onClose`, `month`, `activeAccounts`, `monthBalances`
  - Fields:
    - **From account** — `Select` populated with active accounts that have a balance entry for the current month
    - **To account** — `Select` populated with all active accounts except the selected from-account
    - **Amount** — `Input` type number; must be a positive integer
  - Month is pre-filled to `effectiveMonth` (displayed read-only in the dialog)
  - Validates client-side before submitting: from ≠ to, amount > 0, amount is a whole number
  - On submit: fires the transfer mutation; closes on success
  - Shows API error in dialog footer if the mutation fails

3.2 Wire up `useMutation` for `transfer` in `BalancesPage`:
  - On success: invalidate `["balances", effectiveMonth]`

---

## 4. Page Integration (`BalancesPage.tsx`)

4.1 Add **Roll forward** and **Transfer** buttons to the page header area (right side of the row that contains "Balances" heading).

4.2 Compute derived values for the roll-forward dialog (no API call needed):
  - `sourceMonth`: max month in `allBalances` where `month < effectiveMonth`; undefined if none
  - `accountsToFillCount`: active accounts with no entry in `monthBalances`

4.3 Disable the **Roll forward** button when `sourceMonth` is undefined (no prior data to copy from).

4.4 Control dialog open state with `useState` booleans: `rollForwardOpen`, `transferOpen`.

---

## 5. Tests

5.1 Verify the existing backend tests for roll-forward and transfer still pass (`just test`).

5.2 Run `just frontend-typecheck` and `just frontend-lint` — both must pass with no errors.

5.3 Manual walkthrough (see `validation.md`).
