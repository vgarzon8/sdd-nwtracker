# Validation — Phase 7: Reports API

## Automated — single-month endpoint

- [x] `just check` passes (tests, lint, typecheck all green)
- [x] `GET /reports/balance-summary?attribute=side&month=2024-01` returns a list of `{group_key, balance_sum_usd}` items
- [x] `attribute=side` with one asset account and one liability account returns exactly two items
- [x] `attribute=currency` groups accounts correctly by currency code
- [x] `attribute=institution` groups accounts by institution ID (int)
- [x] `attribute=tags` with a multi-tag account: that account's balance appears in each tag's `balance_sum_usd`
- [x] `attribute=tags` with an untagged account: response contains an item with `group_key: null`
- [x] Missing exchange rate → 422 with JSON body listing the missing `(currency_code, month)` pair
- [x] Closed account with a balance row is absent from the response
- [x] Active account with no balance row for the month is absent from the response
- [x] Invalid `attribute` value → 422
- [x] Invalid month format → 422
- [x] Month with no qualifying accounts → `[]` (200, not 404)
- [x] mypy reports no errors on `app/services/reports.py`, `app/models/report.py`, `app/routers/reports.py`

## Automated — history endpoint

- [x] `GET /reports/balance-summary/history?attribute=side&from=2024-01&to=2024-03` returns items across all three months sorted ascending by `(month, group_key)`
- [x] `to` omitted: `to_month` in response equals the max balance month in the DB
- [x] Months with no balance data in the range are absent from `items`
- [x] Missing exchange rate in any month of the range → 422 listing the specific pair(s)
- [x] `from > to` → 422
- [x] Invalid `from` or `to` format → 422
- [x] No balance data at all with `to` omitted → 200 with `items: []`

## Manual walkthrough

1. Run `just db-seed` to load sample data.
2. `GET /reports/balance-summary?attribute=side&month=<seeded-month>` — verify two items (`"asset"` and `"liability"`); manually compute net worth as their difference.
3. `GET /reports/balance-summary?attribute=currency&month=<seeded-month>` — verify one item per currency; check a non-USD item by computing `round(native_amount / rate)` against the seeded exchange rate.
4. `GET /reports/balance-summary?attribute=institution&month=<seeded-month>` — verify items keyed by integer institution IDs.
5. `GET /reports/balance-summary?attribute=tags&month=<seeded-month>` — verify tag IDs as `group_key`; if any account is untagged, confirm `group_key: null` item present.
6. `GET /reports/balance-summary/history?attribute=side&from=<earliest-month>` — verify `to_month` is the latest seeded month; verify items sorted by month then group_key.
7. Delete one exchange rate for a non-USD currency; re-run step 2 — confirm 422 naming the missing pair.
8. Check `/docs`: both endpoints are visible with correct request/response schemas including the `AccountAttribute` enum values.

## Edge cases

- `attribute=tags` with all accounts tagged: no `null` group key in response.
- Single month in history range (`from == to`): valid; returns items for that one month only.
- All accounts in portfolio are USD: no exchange rate lookups needed; endpoint returns successfully with no rate data.
- Account with `side="liability"` and large balance: `balance_sum_usd` is positive; presentation layer applies the sign.

## Definition of done

- All automated checks above pass.
- Manual walkthrough completed without errors.
- `specs/roadmap.md` Phase 7 checkbox updated to `[X]`.
