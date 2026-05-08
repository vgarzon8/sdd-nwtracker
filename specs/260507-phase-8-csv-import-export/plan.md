# Plan — Phase 8: CSV Import & Export

## 1. CSV format documentation (`specs/csv-format.md`)

1.1. Document file inventory (one entry per CSV file).
1.2. Document column definitions and types for each file.
1.3. Document natural-key conventions and why IDs are omitted.
1.4. Document the tag semicolon-separator convention.
1.5. Document import processing order and FK resolution rules.
1.6. Provide a minimal worked example showing a valid set of 6 CSVs.

## 2. Export service (`app/services/csv_export.py`)

2.1. Implement `export_to_zip(session: Session) -> bytes`:
  - Query all six tables in dependency order.
  - Build each CSV in memory using `csv.writer` and `io.StringIO`.
  - For `accounts.csv`, load each account's tags via `AccountTag`; emit tag names as
    a semicolon-separated string in the `tags` column (empty string if none).
  - Pack all six CSVs into a `zipfile.ZipFile` (in-memory `io.BytesIO`).
  - Return the ZIP bytes.

## 3. Import service (`app/services/csv_import.py`)

3.1. Define `TableCounts(BaseModel)`: `inserted: int`, `updated: int`.
3.2. Define `ImportResult(BaseModel)`: `imported: dict[str, TableCounts]`.

3.3. Implement `import_from_zip(zip_bytes: bytes, session: Session) -> ImportResult`:
  - Open ZIP; verify all 6 expected filenames are present; raise `HTTPException(422)` listing
    any missing files.
  - Parse each CSV file into a list of dicts using `csv.DictReader`.
  - **Validate all rows before touching the DB** (collect all errors, not just the first):
    - `currencies.csv`: `code` and `name` are non-empty.
    - `tags.csv`: `name` is non-empty.
    - `institutions.csv`: `name` is non-empty.
    - `accounts.csv`: `institution_name` exists in parsed institutions; `currency_code` exists
      in parsed currencies; `side` ∈ `{"asset", "liability"}`; `status` ∈ `{"active", "closed"}`.
    - `balances.csv`: `account_name` exists in parsed accounts; `month` matches `^\d{4}-(0[1-9]|1[0-2])$`;
      `amount` is an integer.
    - `exchange_rates.csv`: `currency_code` exists in parsed currencies; `month` matches the pattern;
      `rate` is numeric.
  - If any validation errors exist, raise `HTTPException(422, detail={"errors": [...]})` listing all
    problems with file name, row number, and description.
  - Within a single transaction, upsert in dependency order:
    1. **Currencies**: upsert by `code`; update `name`.
    2. **Tags**: upsert by `name`; nothing else to update.
    3. **Institutions**: upsert by `name`; nothing else to update.
    4. **Accounts**: upsert by `name`; update `institution_id` (resolved), `currency_code`, `side`,
       `status`; delete existing `AccountTag` rows for this account and insert fresh ones.
    5. **Balances**: upsert by `(account_id, month)`; update `amount`.
    6. **ExchangeRates**: upsert by `(currency_code, month)`; update `rate`.
  - Track insert vs. update counts per table; return `ImportResult`.

## 4. Router (`app/routers/csv_io.py`)

4.1. Create router with `tags=["csv"]`; no prefix (routes are `/export` and `/import`).
4.2. `GET /export`:
  - Inject `session`; call `export_to_zip(session)`.
  - Return `StreamingResponse(iter([zip_bytes]), media_type="application/zip")` with
    `Content-Disposition` header `attachment; filename=nwtracker-YYYY-MM-DD.zip`.
4.3. `POST /import`:
  - Accept `file: UploadFile = File(...)`.
  - Read bytes; call `import_from_zip(bytes, session)`.
  - Return `ImportResult`.

## 5. Register router (`app/main.py`)

5.1. Import `csv_io` router and `app.include_router(csv_io.router)` after the reports router.

## 6. Tests (`backend/tests/test_csv_io.py`)

6.1. **Export shape**: seed one row in each table; `GET /export`; verify 200, `Content-Type: application/zip`,
     ZIP contains all 6 filenames, each file has the correct header row.
6.2. **Round-trip**: seed full data; export; delete all accounts/balances/exchange_rates/institutions/tags
     (keep currencies); import the ZIP; verify all rows are restored including AccountTag rows.
6.3. **Idempotency**: import a ZIP; import the same ZIP again; verify second run returns `inserted: 0`
     and `updated` equals the row count for each table.
6.4. **Upsert updates fields**: build a ZIP with a balance amount different from the DB; import;
     verify the DB row reflects the new amount.
6.5. **Missing file → 422**: upload a ZIP missing `balances.csv`; verify 422 detail names the file.
6.6. **Invalid month format → 422**: `balances.csv` with `month="January 2024"`; verify 422.
6.7. **Invalid side value → 422**: `accounts.csv` with `side="savings"`; verify 422.
6.8. **Unknown institution in accounts → 422**: `accounts.csv` references an institution not in
     `institutions.csv`; verify 422.
6.9. **Unknown account in balances → 422**: `balances.csv` references an account not in `accounts.csv`;
     verify 422.
6.10. **Empty tables**: no seed data; `GET /export`; verify ZIP has header-only CSVs;
      import the empty ZIP → 200, all counts zero.
6.11. **Tag round-trip**: seed an account with two tags; export; delete AccountTag rows; import;
      verify both AccountTag rows are restored.
