# Requirements — Phase 7: Reports API

## Scope

### Included

**Endpoint 1 — single-month aggregation:** `GET /reports/balance-summary?attribute=<attr>&month=YYYY-MM`
- Returns balance amounts grouped by the specified account attribute, all converted to USD
- Response is a flat list of `{group_key, balance_sum_usd}` items

**Endpoint 2 — time series aggregation:** `GET /reports/balance-summary/history?attribute=<attr>&from=YYYY-MM&to=YYYY-MM`
- Same aggregation logic as endpoint 1, applied across a range of months
- Response is a flat list of `{month, group_key, balance_sum_usd}` items — the snapshot shape with `month` added
- `to` is optional; defaults to the most recent month with any balance data in the database
- Months in the range with no active account balances are silently omitted

**Valid `attribute` values:**

| Value | Groups by | `group_key` type |
|---|---|---|
| `side` | `account.side` | `str` — `"asset"` or `"liability"` |
| `currency` | `account.currency_code` | `str` — ISO code, e.g. `"USD"` |
| `institution` | `account.institution_id` | `int` — institution ID |
| `tags` | account tags (many-to-many) | `int` (tag ID) or `null` for untagged |

**Exchange rate handling:** all non-USD balance amounts are converted to USD at the API layer. Exchange rates must exist for every non-USD currency present in the result set. A missing `(currency_code, month)` pair causes a `422` listing all missing pairs before any computation. For the history endpoint, validation covers the entire range upfront.

**Account filtering:** only active accounts with a balance row for the requested month are included. Closed/inactive accounts and accounts with no balance row are silently omitted.

### Not included

- Multi-attribute grouping (e.g. group by institution AND currency simultaneously)
- Per-account detail rows (clients needing account-level detail use `GET /accounts` + `GET /balances`)
- Caching of computed results

### Fields and data shapes

**Snapshot item** (elements of the response list for endpoint 1):

| Field | Type | Notes |
|---|---|---|
| `group_key` | `str \| int \| null` | Value depends on `attribute`; see table above |
| `balance_sum_usd` | `int` | Sum of USD-converted balances for all accounts in this group; rounded to nearest whole USD |

**History item** (elements of the response list for endpoint 2):

| Field | Type | Notes |
|---|---|---|
| `month` | `str` (`YYYY-MM`) | |
| `group_key` | `str \| int \| null` | Same semantics as snapshot |
| `balance_sum_usd` | `int` | |

**Endpoint 1 response:** `list[BalanceSummaryItem]`

**Endpoint 2 response:**

| Field | Type |
|---|---|
| `from_month` | `str` (`YYYY-MM`) |
| `to_month` | `str` (`YYYY-MM`) — resolved value |
| `items` | `list[BalanceSummaryHistoryItem]` — sorted ascending by `(month, group_key)` |

## Decisions

**Net worth is a presentation-layer concern.**
Net worth = `asset balance_sum_usd − liability balance_sum_usd` from an `attribute=side` response. The API does not compute or name it.

**Tags are many-to-many; group sums are not a partition.**
An account tagged with both `"retirement"` and `"liquid"` contributes its full `usd_equivalent` to each tag's `balance_sum_usd`. The sum of all tag group values will exceed the portfolio total when accounts hold multiple tags. Clients must not treat tag sums as a partition of total balance.

**Untagged accounts use `group_key: null`.**
When `attribute=tags`, accounts with no tags are grouped under `group_key: null`. The presentation layer supplies the display label.

**USD conversion formula.**
Rates are stored as `X foreign units per 1 USD`. Conversion: `usd_equivalent = round(native_amount / rate)`. USD accounts use an implicit rate of 1.

**Liability amounts are positive.**
`balance_sum_usd` for liability accounts is a positive integer. The presentation layer applies the sign when computing net worth.

**Ordering.**
Snapshot response is sorted by `group_key` ascending, with `null` last. History response is sorted by `(month, group_key)` ascending, with `null` group keys last within each month.

**History `to` default.**
When `to` is omitted, the service queries `MAX(month)` from the `Balance` table. If no balances exist, the response has `items: []`.

**History batch query.**
All active-account balances for the full range are fetched in a single query (`month BETWEEN from AND to`), then grouped in Python to avoid N round-trips.

**`from > to` is a 422.**
Validated before any DB query.

**Service layer.**
All computation lives in `app/services/reports.py`. The router handles HTTP concerns only.

## Context

- Stack: Python 3.12, FastAPI, SQLModel/SQLAlchemy, SQLite — no new dependencies
- Follow the existing router pattern: one file `app/routers/reports.py`, registered in `main.py` under the `/reports` prefix
- Tests are integration tests against real in-memory SQLite (same `session` / `client` fixtures from `conftest.py`)
- Month format validation follows the pattern already established in `balances.py` and `exchange_rates.py`
- `attribute` should be validated as an enum; an unrecognised value returns 422
