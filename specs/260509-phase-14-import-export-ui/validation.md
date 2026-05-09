# Phase 14 — Import / Export UI: Validation

## Automated

- [x] `just test` passes (153 passed — all backend tests green, no regressions)
- [x] `just frontend-typecheck` passes with no errors
- [x] `just frontend-lint` passes with no errors

---

## Manual Walkthrough

### Setup

- [ ] Dev servers running: `just dev` and `just frontend-dev`
- [ ] A valid export ZIP available for re-import testing (export first, then use that file)

### Export

- [ ] Navigate to `/import-export`
- [ ] Clicking **Export** triggers a browser download of a `.zip` file named `nwtracker-YYYY-MM-DD.zip`
- [ ] The downloaded ZIP contains all expected CSV files (currencies, tags, institutions, accounts, balances, exchange_rates)

### Import — Success Path

- [ ] Select the previously exported ZIP via the file picker
- [ ] **Import** button is enabled once a file is selected
- [ ] Clicking **Import** shows "Importing…" while in progress
- [ ] On success, the import summary table appears with columns: Table, Inserted, Updated
- [ ] Counts for each table are visible (all rows show 0 inserted / N updated for a round-trip re-import)
- [ ] An "Import another file" option allows resetting to upload a new file

### Import — Error Path

- [ ] Selecting a non-ZIP file and submitting shows an error message (invalid ZIP)
- [ ] Uploading a ZIP missing required CSV files shows a message listing the missing files
- [ ] Uploading a ZIP with invalid row data shows the per-row validation error messages inline

### Edge Cases

- [ ] Submitting without a file selected is not possible (Import button disabled)
- [ ] Uploading the same file twice succeeds both times (idempotent — updated counts increase on second run)

---

## Definition of Done

- Export button triggers a browser download of the full data ZIP with no errors
- Import form accepts a ZIP file, shows per-table summary on success, and shows validation errors inline on failure
- Import is idempotent: re-uploading the same file produces 0 inserted / all updated on second run
- All automated checks pass
- No regressions to any other page
