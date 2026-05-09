# Phase 14 — Import / Export UI: Requirements

## Scope

### Included

- **Export button**: single click triggers a browser download of `GET /export` — a ZIP file containing all tables as CSV files, named `nwtracker-YYYY-MM-DD.zip`
- **Import file upload**: file picker (accept `.zip`), submit button, and inline result display
- **Import summary**: after a successful import, show a table with inserted + updated counts per table (currencies, tags, institutions, accounts, balances, exchange_rates)
- **Import error display**: on a 422 response, show the validation error messages inline without navigating away
- New `src/api/csv.ts` with `triggerExport()` and `importCsv(file)` functions
- Both features on the existing `/import-export` route (`ImportExportPage.tsx`)

### Not included

- Dry-run / preview step before committing import
- Selecting individual tables to export
- Progress bar or streaming feedback during upload (file is expected to be small)
- Drag-and-drop file upload
- Ability to download individual CSVs rather than the ZIP

---

## Decisions

| Decision | Choice | Reason |
|---|---|---|
| Export mechanism | `window.location.href = "/api/export"` | Backend sets `Content-Disposition: attachment`, triggering a browser download; no `fetch` call or response handling needed in JS |
| Import HTTP client | Custom `fetch` with `FormData` (not the shared `client.ts` wrapper) | `client.ts` only handles JSON bodies and reads errors as raw text; for multipart upload + structured 422 parsing, a dedicated function is cleaner |
| Import state management | Local component state (`useState`) — no TanStack Query mutation | One-shot form interaction; no cache to invalidate; no background refetch needed |
| 422 error parsing | Parse the `detail` field from the JSON error body | Backend returns `{"detail": {"errors": [...]}}` for row errors, `{"detail": {"message": "...", "missing": [...]}}` for missing files, and `{"detail": "Invalid ZIP file"}` for a bad ZIP |
| Import idempotency | No warning shown to user | Backend import is fully idempotent (upsert-based); safe to re-run without side effects |
| Page layout | Two stacked sections: Export (top), Import (below) | Natural read order; export is simpler and more common |
| Summary table row labels | Use raw table key from response (`currencies`, `accounts`, etc.) | Matches the backend key names; no need to map to display labels |

---

## Context

- **Stack**: TypeScript, React 19, shadcn/ui, Tailwind CSS v4 (no TanStack Query for the import form)
- **Backend endpoints** (both fully implemented and tested):
  - `GET /export` → `application/zip` response with `Content-Disposition: attachment; filename=nwtracker-YYYY-MM-DD.zip`
  - `POST /import` — multipart `file` field → `ImportResult` (`{ imported: { [table]: { inserted, updated } } }`) on success; 422 on failure
- **Existing page stub**: `src/pages/ImportExportPage.tsx` (replace entirely)
- **No TanStack Query needed**: import is a one-shot form action, not a server-state query
- **No copy-style constraints**: labels should be plain and functional
- **ImportResult shape** (from `backend/app/services/csv_import.py`):
  ```
  ImportResult.imported: dict[tableName, TableCounts]
  TableCounts: { inserted: int, updated: int }
  Table keys: currencies, tags, institutions, accounts, balances, exchange_rates
  ```
- **422 detail shapes**:
  - String: `"Invalid ZIP file"` (bad archive)
  - Object with `message` + `missing` array: missing required CSV files
  - Object with `errors` array: per-row validation errors
