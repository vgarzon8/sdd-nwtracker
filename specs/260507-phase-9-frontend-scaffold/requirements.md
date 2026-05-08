# Phase 9 — Frontend Scaffold: Requirements

## Scope

### What is included

Initialize a React frontend project under `frontend/` wired to the existing FastAPI backend, with routing, shared layout, and placeholder pages for every section.

**Project setup**

| Item | Choice |
|------|--------|
| Build tool | Vite |
| Language | TypeScript (strict) |
| UI framework | React 19 |
| Routing | React Router v7 |
| Styling | Tailwind CSS |
| Components | shadcn/ui (default theme, no customization) |
| Server state | TanStack Query (QueryClient provider at root) |
| HTTP client | `fetch`-based thin wrapper in `src/api/` |
| Linter | ESLint (ships with Vite `react-ts` template: `typescript-eslint`, `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`) |
| Formatter | Prettier (`prettier` + `eslint-config-prettier`) |

**Routes**

| Path | Page | Notes |
|------|------|-------|
| `/` | — | Redirects to `/dashboard` |
| `/dashboard` | Dashboard | Home/landing placeholder |
| `/currencies` | Currencies | Reference data placeholder |
| `/tags` | Tags | Reference data placeholder |
| `/institutions` | Institutions | Reference data placeholder |
| `/accounts` | Accounts | Placeholder |
| `/balances` | Balances | Placeholder |
| `/reports` | Reports | Placeholder |
| `/import-export` | Import / Export | Placeholder |

**Layout**

- Shared layout wraps all routes: left sidebar navigation + top header
- Sidebar lists sections with links to each route; active link is highlighted
- Header shows the app name (`nwtracker`)
- Layout is functional and minimal — no collapsing, no animations

**API client**

- `frontend/src/api/client.ts` — thin wrapper around `fetch`; base URL is `/api`
- Vite dev proxy forwards `/api/*` → `http://localhost:8000`
- No generated types at this phase

**Placeholder pages**

- Each page renders the section name and a one-line "coming soon" note
- No real data fetching, forms, or interactive elements

### What is NOT included

- Any real component implementations (those belong to phases 10–14)
- Sidebar collapsing, animations, or responsive breakpoints
- Custom Tailwind theme, color tokens, or typography changes beyond defaults
- Frontend tests (no frontend test runner is configured in the stack)
- Docker or Compose setup (covered separately in the stack spec)
- Any AI or chat UI (phases 15–17)

---

## Decisions

**URL structure — flat routes, sidebar handles grouping**
Currencies, Tags, and Institutions live at `/currencies`, `/tags`, `/institutions` (not nested under `/reference/*`). The sidebar can visually group them under a "Reference Data" heading without requiring nested URL paths. Flat URLs are simpler to type, link to, and refactor later.

**Dashboard as the default route**
`/` redirects to `/dashboard`. This gives the app a clear home landing point without over-engineering it now — the dashboard page in this phase is just a placeholder.

**ESLint + Prettier, mirroring backend's ruff lint + format**
The Vite `react-ts` template ships ESLint already configured. Prettier is added for formatting (with `eslint-config-prettier` to disable conflicting ESLint rules). This mirrors the backend pattern: `just frontend-lint` (ESLint) and `just frontend-typecheck` (`tsc --noEmit`) run as part of `just check`; `just frontend-format` auto-fixes formatting. `just check` is updated to run frontend lint + typecheck alongside backend checks.

**`fetch`-based API client, not Axios**
A thin `fetch` wrapper is enough for this phase, keeps the dependency count low, and is easy to extend. If Axios is needed later, the swap is localized to `src/api/client.ts`.

**shadcn/ui default theme, no customization**
No custom color tokens, typography, or theme variables. Phase 9 is infrastructure, not UI polish. Later phases can layer styling on top.

**TanStack Query at root**
`QueryClientProvider` wraps the app in `main.tsx`. Individual pages will use `useQuery` / `useMutation` starting in phase 10.

---

## Context

- **Tone:** Placeholder pages use the section name as an `<h1>` and a short "Coming soon" line. No lorem ipsum, no mock data.
- **Stack pointers:** Follow `specs/tech-stack.md` exactly. Do not introduce additional dependencies without discussion.
- **Conventions from backend:**
  - Month format `YYYY-MM` — not relevant at this phase but keep in mind for later pages
  - All API responses are JSON; no special auth headers needed (single-user, local-only)
- **Existing patterns:** Backend lives in `backend/`; frontend goes in `frontend/` at the same level. Justfile at repo root gains `frontend-dev`, `frontend-lint`, `frontend-typecheck`, `frontend-format` recipes, and `check` is updated to include frontend lint + typecheck.
