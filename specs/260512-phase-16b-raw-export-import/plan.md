# Phase 16b — Raw Export / Import: Plan

## 1. Backend — Raw Export Service

1.1. Create `backend/app/services/raw_csv_export.py`  
- `export_raw_to_zip(session) -> bytes` — writes one CSV per table using schema-aligned columns (see requirements column table)  
- Reuse the existing `_write_csv` helper (or inline an equivalent); keep implementation parallel to `csv_export.py`

1.2. Add `?format=raw` to `GET /export` in `backend/app/routers/csv_io.py`  
- Accept `format: Literal["friendly", "raw"] = "friendly"` query param  
- Dispatch to `export_raw_to_zip` when `format=raw`; use `nwtracker-raw-<date>.zip` as filename

---

## 2. Backend — Raw Import Service

2.1. Extend `ImportResult` (in `csv_import.py`) with `skipped: dict[str, int]` and `warnings: list[str]` fields  
- `skipped` mirrors the shape of `imported` (per-table count of rows that were dropped)  
- `warnings` is a flat list of human-readable messages ("accounts: row with institution_id=99 skipped — unknown institution")

2.2. Create `backend/app/services/raw_csv_import.py`  
- `import_raw_from_zip(zip_bytes, session) -> ImportResult`  
- For each table: read CSV, validate FK references against in-session data, upsert by `id` (or `code` for currencies), collect skipped rows  
- Import order matters for FK resolution: `currencies` → `tags` → `institutions` → `accounts` → `account_tags` → `balances` → `exchange_rates`

2.3. Add `?format=raw` to `POST /import` in `csv_io.py`  
- Same `format` query param as export; dispatch to `import_raw_from_zip` when `format=raw`

---

## 3. Backend — Tests

3.1. Add `backend/tests/test_raw_csv_io.py`  
- Round-trip test: seed DB → raw export → fresh DB → raw import → assert data matches  
- Upsert idempotency: import same ZIP twice, counts on second pass are all updates, no inserts  
- FK violation: import a `balances.csv` row with unknown `account_id`; assert row is skipped and warning is present  
- `skipped` / `warnings` populated correctly when rows are dropped

---

## 4. Frontend — API client

4.1. Update `frontend/src/api/csv.ts`  
- Add `format` parameter to `triggerExport(format)` and `importCsv(file, format)`  
- Pass `?format=raw` in the URL when format is `"raw"`; default to `"friendly"` (existing behavior unchanged)

---

## 5. Frontend — Import/Export page

5.1. Add format toggle state to `ImportExportPage.tsx`  
- `const [format, setFormat] = useState<"friendly" | "raw">("friendly")`

5.2. Render a segmented toggle above both sections  
- Use two `Button` components with `variant="outline"` / `variant="default"` to indicate active state (shadcn pattern); labels: "User-friendly" / "Raw"  
- Toggling resets any in-progress import result

5.3. Pass `format` to `triggerExport` and `importCsv` calls

5.4. Show a descriptive subtitle for each format  
- User-friendly: "Human-readable names, no IDs. Best for manual editing."  
- Raw: "Schema-aligned with IDs and foreign keys. Best for backup and restore."

5.5. Extend the import result table to show the `skipped` column alongside Inserted / Updated  
- Only render the column when `result.skipped` is non-empty  
- Render `warnings` as a collapsible list below the table (or inline if short)
