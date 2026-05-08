# Requirements — Phase 8: CSV Import & Export

## Scope

### In scope

- `GET /export` — export all tables to a single ZIP archive containing one CSV per table
- `POST /import` — accept a ZIP archive (same format as export), validate, and upsert all rows
- `specs/csv-format.md` — document the CSV format and natural-key conventions
- Integration tests covering export shape, round-trip, idempotency, upsert, and validation errors

### Not in scope

- Per-table export endpoints
- JSON import/export format
- Import dry-run / validate-only mode (no commit)
- Streaming for large files
- UI (Phase 14)

### Tables exported / imported

All six tables exported in dependency order:

| File | Table(s) | Natural key |
|------|----------|-------------|
| `currencies.csv` | `currency` | `code` |
| `tags.csv` | `tag` | `name` |
| `institutions.csv` | `institution` | `name` |
| `accounts.csv` | `account` + `account_tag` | `name` |
| `balances.csv` | `balance` | `(account_name, month)` |
| `exchange_rates.csv` | `exchange_rate` | `(currency_code, month)` |

`accounts.csv` embeds tag associations in a `tags` column (semicolon-separated tag names; empty string if none). The `account_tag` join table is not a separate file.

## Decisions

### Upsert by natural key (IDs not in CSVs)

Exported CSVs do **not** include synthetic integer IDs. All cross-file references use natural keys (e.g., `institution_name` instead of `institution_id` in `accounts.csv`). On import, each row is matched to an existing DB row by natural key; if found, non-key fields are overwritten; if not found, a new row is inserted.

**Why:** User chose upsert semantics. Omitting IDs makes the CSV portable across fresh installs where auto-increment IDs would differ.

### All files required on import

Import requires all six CSV files to be present in the ZIP. Missing files → 422 listing which files are absent.

**Why:** Partial imports can create orphaned FK references (e.g., a balance referencing an account that was not imported). A complete snapshot is the safe default for a single-user local tool.

### Atomic import

The entire import runs inside a single DB transaction. Any validation error or DB error triggers a rollback; the DB is left unchanged.

**Why:** A partially applied import is harder to recover from than a clean failure.

### Tag separator: semicolon

Tags in `accounts.csv` use `;` as the separator, not `,`, to avoid ambiguity with the CSV column delimiter. Tag names must not contain semicolons.

**Why:** Tag names are user-defined strings that could contain commas.

### Export file naming

`GET /export` returns a ZIP with `Content-Disposition: attachment; filename=nwtracker-YYYY-MM-DD.zip` using today's UTC date.

**Why:** Makes backup files easy to identify by date without requiring a client-provided name.

## Context

- Follow the existing service layer pattern in `app/services/` (see `reports.py`)
- Router follows the pattern of existing routers; register in `main.py`
- Use Python `csv` and `zipfile` stdlib only — no new dependencies
- `POST /import` accepts `UploadFile` via FastAPI multipart upload
- `GET /export` returns `fastapi.responses.StreamingResponse` with `media_type="application/zip"`
- Validation errors follow the existing pattern: `HTTPException(status_code=422, detail={...})`
- Month format: `YYYY-MM`; amounts: integer; rates: `Decimal` with up to 4 decimal places
