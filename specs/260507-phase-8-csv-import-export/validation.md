# Validation — Phase 8: CSV Import & Export

## Automated

- [x] `just check` passes (tests, lint, typecheck all green)
- [x] `GET /export` returns 200 with `Content-Type: application/zip`
- [x] Exported ZIP contains exactly: `currencies.csv`, `tags.csv`, `institutions.csv`, `accounts.csv`, `balances.csv`, `exchange_rates.csv`
- [x] Each exported CSV has the correct header row per `specs/csv-format.md`
- [x] Full export → wipe → import round-trip restores all rows in all tables
- [x] Tag associations are preserved in the round-trip (multi-tag account restores all `account_tag` rows)
- [x] Importing the same ZIP twice is idempotent: second run returns `inserted: 0` for all tables
- [x] Importing a ZIP with a changed balance amount upserts the row with the new amount
- [x] Missing CSV file in ZIP → 422 listing the missing filename
- [x] Invalid `month` format in `balances.csv` → 422
- [x] Invalid `side` value in `accounts.csv` → 422
- [x] Account references unknown `institution_name` → 422
- [x] Balance references unknown `account_name` → 422
- [x] Import with header-only CSVs (no data rows) → 200, all counts zero
- [x] mypy reports no errors on `app/services/csv_export.py`, `app/services/csv_import.py`, `app/routers/csv_io.py`

## Manual walkthrough

1. Run `just db-seed` to load sample data.
2. `GET /export` — save the ZIP to disk; open it and verify all 6 CSVs are present with headers and data rows.
3. Inspect `accounts.csv` — verify `institution_name` and `currency_code` are human-readable (not IDs); verify `tags` column contains semicolon-separated names or empty string.
4. Inspect `balances.csv` — verify `account_name` column (not `account_id`); verify `month` is `YYYY-MM`; verify `amount` is an integer.
5. `POST /import` with the exported ZIP on the same seeded DB — verify 200 response with per-table `inserted`/`updated` counts.
6. Modify one balance amount in `balances.csv` inside the ZIP and re-import — verify the DB row reflects the new amount.
7. Delete `balances.csv` from the ZIP and try to import — verify 422 response naming `balances.csv`.
8. Add a row to `accounts.csv` that references an institution not in `institutions.csv` and import — verify 422 naming the unknown institution.
9. Check `/docs` — verify both endpoints appear with correct request/response schemas.

## Edge cases

- Account with no tags: `tags` column is empty string `""`; import treats this as zero tag associations.
- All accounts USD: `exchange_rates.csv` exports with headers only (no data rows); import succeeds with `exchange_rates: {inserted: 0, updated: 0}`.
- Institution name containing a comma: `csv.writer` auto-quotes the field; `csv.DictReader` reads it correctly.
- Tag names containing a semicolon: disallowed per spec (semicolon is the tag separator).

## Definition of done

- All automated checks above pass.
- Manual walkthrough completed without errors.
- `specs/csv-format.md` exists and matches the actual export format.
- `specs/roadmap.md` Phase 8 checkbox updated to `[X]`.
