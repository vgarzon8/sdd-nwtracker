# Phase 16b — Raw Export / Import: Validation

## Automated

- [x] `just test` passes — all existing tests green; new `test_raw_csv_io.py` tests pass
- [x] `just typecheck` passes (mypy strict on backend)
- [x] `just frontend-typecheck` passes (tsc --noEmit strict)
- [x] `just lint` and `just frontend-lint` pass with no new warnings

### Required test assertions

- [x] Round-trip: seed DB → `GET /export?format=raw` → import ZIP into a blank DB via `POST /import?format=raw` → all rows present and values match
- [x] Upsert idempotency: importing the same ZIP twice produces `inserted=0` / `updated=N` on the second pass
- [x] FK violation: a `balances.csv` row referencing an unknown `account_id` is skipped; `skipped.balances >= 1` and `warnings` contains a message referencing that row
- [x] `GET /export?format=raw` returns a ZIP with 7 CSV files: `currencies`, `tags`, `institutions`, `accounts`, `account_tags`, `balances`, `exchange_rates`
- [x] `GET /export` (no param) still returns the user-friendly format unchanged

---

## Manual walkthrough

- [ ] Open Import / Export page — two toggle buttons visible ("User-friendly" / "Raw"); "User-friendly" active by default
- [ ] Subtitle text updates when the toggle changes
- [ ] Click Export with "User-friendly" selected — ZIP named `nwtracker-<date>.zip` downloads; contents match existing format
- [ ] Click Export with "Raw" selected — ZIP named `nwtracker-raw-<date>.zip` downloads; CSVs contain `id` columns and integer FK columns
- [ ] Import the raw ZIP — result table shows Inserted / Updated / Skipped columns; data in the app is unchanged on a clean re-import
- [ ] Introduce a row with a bad FK in the ZIP and import — warnings section appears; valid rows are imported; bad row is skipped

---

## Definition of done

- All automated checks above pass
- Manual walkthrough complete with no regressions on the user-friendly format
- Both export formats produce valid ZIP archives that the import endpoint accepts
