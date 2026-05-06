# Phase 3 — Reference Data API: Requirements

## Scope

Full CRUD REST endpoints for the three reference-data entities: `Currency`, `Tag`, and `Institution`. These are the foundational lookup tables that accounts depend on. No account or balance routes in this phase.

## Out of Scope

- Account endpoints (Phase 4)
- Balance endpoints (Phase 5)
- Exchange rate endpoints (Phase 6)
- Filtering, search, or pagination on list endpoints
- Frontend

---

## Endpoints

### Currencies

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/currencies` | List all currencies |
| `POST` | `/currencies` | Create a currency |
| `GET` | `/currencies/{code}` | Get a single currency by code |
| `DELETE` | `/currencies/{code}` | Delete a currency (blocked if in use) |

Currency codes are the natural PK (`"USD"`, `"CNY"`, etc.) — no numeric id.

**DELETE constraint:** If any `Account` or `ExchangeRate` row references the currency code, return `409 Conflict`. No cascade; the caller must remove dependent records first.

### Tags

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/tags` | List all tags |
| `POST` | `/tags` | Create a tag |
| `GET` | `/tags/{id}` | Get a single tag |
| `PUT` | `/tags/{id}` | Rename a tag |
| `DELETE` | `/tags/{id}` | Delete tag and its account associations |

Tags are used for reporting only. Deleting a tag removes the tag row and all rows in `account_tag` for that tag. **Accounts are not deleted.** No `confirm` parameter required — this is always a safe operation.

### Institutions

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/institutions` | List all institutions |
| `POST` | `/institutions` | Create an institution |
| `GET` | `/institutions/{id}` | Get a single institution |
| `PUT` | `/institutions/{id}` | Rename an institution |
| `DELETE` | `/institutions/{id}` | Cascade-delete institution and its accounts |

**Institution delete has two modes:**

- **Dry-run** (`DELETE /institutions/{id}` — no query param): returns `200` with `{"accounts_to_delete": N, "balances_to_delete": N}`. No data is changed. If `N == 0` for both, the caller may proceed knowing it's a clean delete.
- **Destructive** (`DELETE /institutions/{id}?confirm=true`): deletes all balance rows for affected accounts, then all account_tag rows, then all accounts, then the institution. Returns `204 No Content`.

In both modes, if the institution does not exist return `404`.

---

## Request / Response Shapes

### Currency

```
CurrencyCreate  { code: str, name: str }
CurrencyRead    { code: str, name: str }
```

`code` must be a non-empty string of 1–10 characters (no format enforcement beyond that — the spec does not mandate ISO 4217 only).

### Tag

```
TagCreate  { name: str }
TagRead    { id: int, name: str }
TagUpdate  { name: str }
```

### Institution

```
InstitutionCreate  { name: str }
InstitutionRead    { id: int, name: str }
InstitutionUpdate  { name: str }
```

### Institution Delete Dry-Run Response

```
InstitutionDeletePreview  { accounts_to_delete: int, balances_to_delete: int }
```

---

## Status Codes

| Situation | Code |
|-----------|------|
| Successful create | `201 Created` |
| Successful read / list / dry-run | `200 OK` |
| Successful destructive delete | `204 No Content` |
| Resource not found | `404 Not Found` |
| Unique constraint violated (duplicate name/code) | `409 Conflict` |
| Currency in use (accounts or exchange rates) | `409 Conflict` |

---

## Key Decisions

- **Separate read/create models from table models.** SQLModel table classes are not used directly as request/response bodies. Each router defines its own `*Create`, `*Read`, and `*Update` Pydantic models. This avoids leaking internal fields and keeps the OpenAPI schema clean.
- **Error format: FastAPI default.** All error responses use FastAPI's built-in `HTTPException` which returns `{"detail": "..."}`. No custom error model is introduced in this phase.
- **Tag delete is unconditional.** Because tags are reporting metadata, removing a tag never deletes accounts. The cascade to `account_tag` is always safe and requires no confirmation.
- **Institution dry-run returns 200 (not 4xx).** The absence of `?confirm=true` is a deliberate "preview" request, not an error. Returning 200 with counts makes it easy to script and display in a future UI.
- **Balances included in institution cascade preview.** Even though balances are a Phase 5 concern, they are FK'd to accounts. The dry-run must report `balances_to_delete` so the caller has full impact visibility. The destructive path must delete balances before accounts to avoid FK violations.
- **Currency delete blocked, not cascaded.** Currencies are low-churn reference data. A currency should not be deletable while accounts hold it — the caller is expected to reassign or close accounts first. This is simpler than cascading and avoids silent data loss.
- **List endpoints return all rows.** Record counts for these entities will be small. No pagination or filtering in this phase.
- **Router-per-domain file layout.** Each entity gets its own file under `backend/app/routers/`: `currencies.py`, `tags.py`, `institutions.py`. Routers are registered in `main.py` with no prefix (paths are already fully qualified).
- **`check` recipe in justfile.** A `just check` recipe is added that runs lint + typecheck + test in sequence, making it easy to verify the full suite before committing.
