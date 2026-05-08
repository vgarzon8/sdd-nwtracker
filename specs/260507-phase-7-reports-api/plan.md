# Plan — Phase 7: Reports API

## 1. Response models (`app/models/report.py`)

1.1. Define `AccountAttribute` enum: `side`, `currency`, `institution`, `tags`.  
1.2. Define `BalanceSummaryItem(BaseModel)`: `group_key: str | int | None`, `balance_sum_usd: int`.  
1.3. Define `BalanceSummaryHistoryItem(BaseModel)`: `month: str`, `group_key: str | int | None`, `balance_sum_usd: int`.  
1.4. Define `BalanceSummaryHistoryResponse(BaseModel)`: `from_month: str`, `to_month: str`, `items: list[BalanceSummaryHistoryItem]`.  
  - All are response-only schemas; no SQLModel table decorator.

## 2. Service layer (`app/services/reports.py`)

2.1. Create `backend/app/services/` directory with `__init__.py`.

2.2. Implement shared helper `_compute_groups(rows, attribute) -> list[BalanceSummaryItem]`:
  - `rows`: list of `(account, usd_equivalent)` tuples already converted to USD.
  - For `side`, `currency`, `institution`: group by the corresponding account field; sum `usd_equivalent` per group.
  - For `tags`: expand each account's tags — add `usd_equivalent` to each tag's running sum; accounts with no tags go to `group_key=None`.
  - Return sorted list: `group_key` ascending, `None` last.

2.3. Implement `get_balance_summary(attribute, month, session) -> list[BalanceSummaryItem]`:
  - Query all active accounts joined with their balance for `month`; omit accounts with no balance row.
  - Collect non-USD `(currency_code, month)` pairs; query exchange rates.
  - If any pairs missing, raise `HTTPException(422)` with the list of missing pairs.
  - Compute `usd_equivalent` per account: `round(native_amount / rate)` (USD → rate=1).
  - Call `_compute_groups`; return result.

2.4. Implement `get_balance_summary_history(attribute, from_month, to_month_or_none, session) -> BalanceSummaryHistoryResponse`:
  - Resolve `to_month`: query `MAX(month)` from `Balance`; if `None`, return empty response.
  - Validate `from_month <= to_month`; raise `HTTPException(422)` if not.
  - Query all active accounts with balances where `month BETWEEN from_month AND to_month` in one query.
  - Collect all non-USD `(currency_code, month)` pairs from the result; query exchange rates for those pairs in one query.
  - Validate no pairs missing; raise `HTTPException(422)` with full list if any.
  - Group rows by month; for each month call `_compute_groups` to get per-group sums.
  - Flatten into `list[BalanceSummaryHistoryItem]` sorted by `(month, group_key)`, `None` last.
  - Return `BalanceSummaryHistoryResponse`.

## 3. Router (`app/routers/reports.py`)

3.1. Create router with prefix `/reports`.  
3.2. Implement `GET /balance-summary`:
  - `attribute: AccountAttribute` and `month: str` as query params.
  - Validate `month` matches `YYYY-MM`.
  - Call `get_balance_summary`; return list.
3.3. Implement `GET /balance-summary/history`:
  - `attribute: AccountAttribute`, `from_: str` (aliased from `from`), `to: str | None` as query params.
  - Validate `from_` and `to` (if provided) match `YYYY-MM`.
  - Call `get_balance_summary_history`; return response.

## 4. Register router (`app/main.py`)

4.1. Import and include the reports router in `main.py`.

## 5. Tests (`backend/tests/test_reports.py`)

### Single-month endpoint (`GET /reports/balance-summary`)

5.1. `attribute=side` — USD only: seed 1 asset account + 1 liability account with balances; assert two items with correct `balance_sum_usd` values.  
5.2. `attribute=side` — multi-currency: add a CNY asset account with a balance and exchange rate; assert `balance_sum_usd` correctly converts and aggregates with other USD assets.  
5.3. `attribute=currency`: assert one item per currency present, correct sums.  
5.4. `attribute=institution`: assert items keyed by `institution_id`, correct sums.  
5.5. `attribute=tags` — multi-tag account: account with two tags appears in both groups; assert both group sums include its balance.  
5.6. `attribute=tags` — untagged account: assert item with `group_key: null`.  
5.7. Missing exchange rate → 422 with missing pair listed.  
5.8. Closed account with balance row → omitted from response.  
5.9. Active account with no balance row for month → omitted.  
5.10. Invalid `attribute` value → 422.  
5.11. Invalid month format → 422.  
5.12. Month with no data → empty list `[]` (not a 404).

### History endpoint (`GET /reports/balance-summary/history`)

5.13. Happy path: seed 3 months of balances; `attribute=side`; assert items span all 3 months in ascending order.  
5.14. `to` omitted: assert `to_month` in response equals max balance month in DB.  
5.15. Month with no data in range omitted: seed Jan + Mar only, query Jan–Mar; assert no Feb items.  
5.16. Missing exchange rate in one month of range → 422 listing that specific pair.  
5.17. `from > to` → 422.  
5.18. No balance data at all with `to` omitted → 200 with `items: []`.
