# Phase 4 — Accounts API: Requirements

## Scope

Full CRUD REST endpoints for the `Account` entity, including tag association via the `AccountTag` junction table. Accounts depend on `Currency`, `Tag`, and `Institution` from Phase 3.

## Out of Scope

- Balance endpoints (Phase 5)
- Exchange rate endpoints (Phase 6)
- Frontend
- Pagination or search on list endpoints

---

## Fields

| Field | Type | Notes |
|-------|------|-------|
| `id` | `int` | Auto-incremented PK |
| `name` | `str` | Unique across all accounts; enforced at DB level |
| `institution_id` | `int` | FK → `institution.id` |
| `currency_code` | `str` | FK → `currency.code` |
| `side` | `"asset" \| "liability"` | Enum; `AccountSide` |
| `status` | `"active" \| "closed"` | Enum; `AccountStatus`; defaults to `"active"` on create |
| `tag_ids` | `list[int]` | Tag associations; stored in `account_tag` junction table; not a column on `Account` |

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/accounts` | List all accounts; optional filter by `status` and/or `tag` |
| `POST` | `/accounts` | Create an account |
| `GET` | `/accounts/{id}` | Get a single account |
| `PUT` | `/accounts/{id}` | Update an account (partial — only provided fields change) |
| `DELETE` | `/accounts/{id}` | Cascade-delete account and its balances |

### GET /accounts — Filtering

Accepts optional query parameters:

- `status=active|closed` — filter by account status
- `tag=<tag_id>` — filter to accounts that have this tag
- Both params can be combined (AND logic: accounts matching both conditions)

### Account Delete — Two Modes

Matching the institution cascade-delete pattern from Phase 3:

- **Dry-run** (`DELETE /accounts/{id}` — no `confirm` param): returns `200` with `{"balances_to_delete": N}`. No data modified. Returns `404` if account missing.
- **Destructive** (`DELETE /accounts/{id}?confirm=true`): deletes all `Balance` rows for the account, then all `AccountTag` rows, then the `Account` row. Returns `204 No Content`. Returns `404` if account missing.

---

## Request / Response Shapes

```
AccountCreate  {
    name: str,
    institution_id: int,
    currency_code: str,
    side: "asset" | "liability",
    status: "active" | "closed" = "active",
    tag_ids: list[int] = []
}

AccountRead  {
    id: int,
    name: str,
    institution_id: int,
    currency_code: str,
    side: "asset" | "liability",
    status: "active" | "closed",
    tag_ids: list[int]
}

AccountUpdate  {
    name: str | None = None,
    institution_id: int | None = None,
    currency_code: str | None = None,
    side: "asset" | "liability" | None = None,
    status: "active" | "closed" | None = None,
    tag_ids: list[int] | None = None
}
# Only provided (non-None) fields are updated.
# tag_ids: if provided, replaces all current tags; if None, tags are unchanged.

AccountDeletePreview  { balances_to_delete: int }
```

---

## FK Validation

Unlike Phase 3 entities (which only have a `name`), accounts reference other tables. Validate explicitly before inserting or updating:

- `institution_id`: must reference an existing `Institution`; return `404` if not found
- `currency_code`: must reference an existing `Currency`; return `404` if not found
- Each id in `tag_ids`: must reference an existing `Tag`; return `404` if any are not found

---

## Status Codes

| Situation | Code |
|-----------|------|
| Successful create | `201 Created` |
| Successful read / list / dry-run | `200 OK` |
| Successful destructive delete | `204 No Content` |
| Resource not found | `404 Not Found` |
| Referenced FK (institution, currency, tag) not found | `404 Not Found` |
| Unique constraint violated (duplicate name) | `409 Conflict` |

---

## Key Decisions

- **Separate read/create/update models from table models.** Same as Phase 3: `AccountCreate`, `AccountRead`, `AccountUpdate`, and `AccountDeletePreview` Pydantic models defined in the router file. No SQLModel table class used as a request body.
- **Partial update (`PUT`).** Unlike Phase 3 entities that only have a `name`, accounts have five user-editable fields. All fields in `AccountUpdate` are optional; only non-`None` values are applied. This follows the same intent (PUT replaces what you send) without forcing the caller to re-send unchanged fields.
- **`tag_ids` replace-on-update semantics.** When `tag_ids` is present in a PUT body, it fully replaces existing tag associations (delete all `AccountTag` rows for the account, insert new ones). When `tag_ids` is `None`, tags are left untouched.
- **Explicit FK validation.** Rather than catching `IntegrityError` from SQLite, check for missing institution/currency/tags before writing. This produces clean 404 responses with clear detail messages.
- **List returns all rows.** No pagination. Small record counts expected.
- **Router file: `backend/app/routers/accounts.py`.** Registered in `main.py` with no prefix, matching all Phase 3 routers.
- **Error format: FastAPI default.** All errors use `HTTPException` returning `{"detail": "..."}`, same as Phase 3.
