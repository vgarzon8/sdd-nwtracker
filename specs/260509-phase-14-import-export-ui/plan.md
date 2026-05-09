# Phase 14 — Import / Export UI: Plan

## Task Group 1 — API Client

1. Create `frontend/src/api/csv.ts`:
   - `triggerExport()`: `window.location.href = "/api/export"` — triggers the browser download with no fetch call
   - `TableCounts` interface: `{ inserted: number; updated: number }`
   - `ImportResult` interface: `{ imported: Record<string, TableCounts> }`
   - `ImportError` interface: `{ messages: string[] }` — normalised from any 422 detail shape
   - `importCsv(file: File): Promise<ImportResult>` — builds a `FormData`, calls `fetch("/api/import", { method: "POST", body: formData })`, parses JSON on success; on non-2xx, extracts the error detail and throws an `ImportError`-shaped object

2. Run `just frontend-typecheck` — confirm no errors

3. Commit: `feat(phase-14): csv API client — triggerExport and importCsv`

---

## Task Group 2 — ImportExportPage

1. Replace the stub in `frontend/src/pages/ImportExportPage.tsx` with a two-section layout:

   **Export section**
   - Heading: "Export"
   - Brief description: "Download all data as a ZIP of CSV files."
   - "Export" button: calls `triggerExport()` on click; no loading state needed (browser handles it)

   **Import section**
   - Heading: "Import"
   - Brief description: "Upload a ZIP file containing all CSV tables. Existing rows are updated; new rows are inserted."
   - File input (accept `.zip`), controlled via `useState<File | null>`
   - "Import" submit button: disabled when no file selected or import is in progress; shows "Importing…" while pending
   - On success: show import summary table (columns: Table, Inserted, Updated) populated from `ImportResult.imported`
   - On error: show the list of error messages from the caught `ImportError`
   - "Import another file" reset link/button to clear result/errors and re-show the file picker

2. State: `file`, `importing`, `result: ImportResult | null`, `errors: string[]`

3. Run `just frontend-typecheck` and `just frontend-lint` — fix any issues

4. Commit: `feat(phase-14): ImportExportPage — export button and import form with summary`

---

## Task Group 3 — Final Validation & Roadmap Update

1. Run `just test` — confirm all 153 backend tests still pass
2. Run `just frontend-typecheck` and `just frontend-lint` — confirm clean
3. Update `specs/260509-phase-14-import-export-ui/validation.md` — tick all automated checks
4. Update `specs/roadmap.md` — mark Phase 14 `[X]`
5. Commit: `docs(phase-14): validation complete, roadmap updated`
