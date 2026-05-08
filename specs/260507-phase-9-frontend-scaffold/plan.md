# Phase 9 — Frontend Scaffold: Implementation Plan

## 1. Project Initialization

1.1. Scaffold Vite + React + TypeScript project under `frontend/`
```
cd frontend && npm create vite@latest . -- --template react-ts
```
1.2. Install runtime dependencies:
```
npm install react-router-dom @tanstack/react-query
```
1.3. Install and configure Tailwind CSS (follow Vite + Tailwind guide):
```
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```
Update `tailwind.config.ts` content paths to include `./src/**/*.{ts,tsx}`.

1.4. Add Tailwind directives to `src/index.css` (replace file contents).

1.5. Install shadcn/ui CLI and initialize:
```
npx shadcn@latest init
```
Accept defaults (TypeScript, Tailwind, CSS variables). This updates `tailwind.config.ts`, `src/index.css`, and adds `src/lib/utils.ts` and `components.json`.

1.6. Install Prettier and its ESLint integration:
```
npm install -D prettier eslint-config-prettier
```
Create `frontend/.prettierrc` with project defaults:
```json
{
  "semi": true,
  "singleQuote": false,
  "trailingComma": "all",
  "printWidth": 100,
  "tabWidth": 2
}
```
Add `"prettier"` as the last entry in the `extends` array of `eslint.config.js` (or equivalent flat-config setup) so Prettier rules override conflicting ESLint formatting rules.

Add `"format": "prettier --write src/"` and `"format:check": "prettier --check src/"` to `package.json` scripts.

---

## 2. Vite Proxy & API Client

2.1. Configure Vite dev proxy in `vite.config.ts`:
```ts
server: {
  proxy: {
    '/api': 'http://localhost:8000',
  },
}
```

2.2. Create `src/api/client.ts` — thin `fetch` wrapper:
- `get<T>(path: string): Promise<T>`
- `post<T>(path: string, body: unknown): Promise<T>`
- `put<T>(path: string, body: unknown): Promise<T>`
- `del(path: string): Promise<void>`
- Base URL is `/api`; throws on non-2xx responses

---

## 3. TanStack Query Setup

3.1. Create a `QueryClient` instance in `src/main.tsx`.
3.2. Wrap `<App>` with `<QueryClientProvider client={queryClient}>`.

---

## 4. Routing

4.1. Define all routes in `src/App.tsx` using `createBrowserRouter` + `RouterProvider`:

```
/             → <Navigate to="/dashboard" />
/dashboard    → <DashboardPage />
/currencies   → <CurrenciesPage />
/tags         → <TagsPage />
/institutions → <InstitutionsPage />
/accounts     → <AccountsPage />
/balances     → <BalancesPage />
/reports      → <ReportsPage />
/import-export → <ImportExportPage />
```

All routes except `/` share the `<AppLayout>` element as the route parent.

---

## 5. Shared Layout

5.1. Create `src/components/AppLayout.tsx`:
- Outer div: full-height flex row
- Left sidebar (`<Sidebar>`) + main content area (`<Outlet>`)
- Top header bar inside main content area showing "nwtracker"

5.2. Create `src/components/Sidebar.tsx`:
- `<nav>` with `<NavLink>` entries for each section
- Visual grouping under "Reference Data" heading (Currencies, Tags, Institutions)
- Top-level links: Dashboard, Accounts, Balances, Reports, Import / Export
- Active link styled with Tailwind (e.g. `bg-muted font-medium`)

---

## 6. Placeholder Pages

Create one file per route under `src/pages/`:

| File | `<h1>` |
|------|--------|
| `DashboardPage.tsx` | Dashboard |
| `CurrenciesPage.tsx` | Currencies |
| `TagsPage.tsx` | Tags |
| `InstitutionsPage.tsx` | Institutions |
| `AccountsPage.tsx` | Accounts |
| `BalancesPage.tsx` | Balances |
| `ReportsPage.tsx` | Reports |
| `ImportExportPage.tsx` | Import / Export |

Each page renders:
```tsx
<div>
  <h1 className="text-2xl font-semibold">{Section Name}</h1>
  <p className="text-muted-foreground mt-1">Coming soon.</p>
</div>
```

---

## 7. Justfile

7.1. Add frontend recipes to the root `justfile`:
```just
frontend-dev:
    cd frontend && npm run dev

frontend-install:
    cd frontend && npm install

frontend-lint:
    cd frontend && npm run lint

frontend-typecheck:
    cd frontend && npx tsc --noEmit

frontend-format:
    cd frontend && npm run format
```

7.2. Update the `check` recipe to include frontend checks:
```just
check: test lint typecheck frontend-lint frontend-typecheck
```

---

## 8. Documentation

8.1. Create `frontend/README.md` — human-facing quickstart covering:
- Prerequisites (Node version)
- `npm install` to install dependencies
- `just frontend-dev` to start the dev server (requires backend running for API calls)
- `just frontend-lint` / `just frontend-typecheck` / `just frontend-format` for code quality
- Note that `/api/*` is proxied to `http://localhost:8000` in dev

---

## 9. Cleanup

9.1. Remove Vite default boilerplate: `src/assets/react.svg`, `public/vite.svg`, default `App.css` styles.
9.2. Update `index.html` `<title>` to `nwtracker`.
9.3. Verify `frontend/` is not accidentally gitignored (check root `.gitignore`).
