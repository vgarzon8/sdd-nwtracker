# Phase 16b — Raw Export / Import: Requirements

## Scope

### Included

- A **raw CSV format** that mirrors the database schema: every exported CSV includes the `id` primary key column and uses integer foreign key IDs instead of human-readable names.
- All seven tables are exported: `currencies`, `tags`, `institutions`, `accounts`, `account_tags`, `balances`, `exchange_rates`.
- Raw export delivered as a ZIP archive (same container as the user-friendly format); the ZIP is named `nwtracker-raw-<date>.zip`.
- Raw import performs an **upsert by `id`**: rows with a matching `id` are updated; rows with an unrecognised `id` are inserted.
- Rows with referential integrity violations (unknown FK) are **skipped with a warning** rather than aborting the whole import; the response reports how many rows were skipped per table and why.
- A **format toggle** (User-friendly / Raw) is added to the existing Import/Export page; it controls both the Export button and the Import flow with a single selector.
- The toggle is wired to a `?format=raw` query parameter on the existing `/export` and `/import` endpoints — no new URL paths.

### Not included

- Full-restore / destructive import (overwrite-all behavior) — the import is always additive/upsert.
- Any changes to the existing user-friendly format or its endpoints.
- New sidebar entries or pages.

---

## CSV column definitions (raw format)

| Table | Columns |
|---|---|
| `currencies` | `code`, `name` |
| `tags` | `id`, `name` |
| `institutions` | `id`, `name` |
| `accounts` | `id`, `name`, `institution_id`, `currency_code`, `side`, `status` |
| `account_tags` | `account_id`, `tag_id` |
| `balances` | `id`, `account_id`, `month`, `amount` |
| `exchange_rates` | `id`, `currency_code`, `month`, `rate` |

`currencies` has no surrogate `id`; `code` is the primary key (same as today).

---

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| API surface | `?format=raw` param on existing `/export` and `/import` | Avoids duplicating URL paths; keeps the router thin |
| Import collision strategy | Upsert by `id` | Preserves existing rows not in the uploaded file; idempotent on re-upload |
| FK violation handling | Skip row, collect warning, continue | Safer than a hard abort; import result already returns per-table counts |
| UI toggle placement | Single selector above Export and Import sections | Keeps the page layout unchanged; one toggle controls both actions |
| ZIP filenames | `nwtracker-raw-<date>.zip` vs `nwtracker-<date>.zip` | Different names prevent confusion when both formats are used |

---

## Context

- Follow the existing patterns in `backend/app/services/csv_export.py` and `csv_import.py`; add sibling files `raw_csv_export.py` and `raw_csv_import.py`.
- The import result response model (`ImportResult`) already carries per-table `inserted`/`updated` counts; extend it with a `skipped` count and a `warnings` list.
- Frontend toggle: use a `ToggleGroup` or two `Button` components styled as a segmented control (shadcn/ui pattern); store state locally in the page component.
- No new dependencies required.
