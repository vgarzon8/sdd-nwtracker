# Phase 9 — Frontend Scaffold: Validation Checklist

## Automated

- [x] `just frontend-typecheck` exits 0 (`tsc --noEmit`, strict mode)
- [x] `just frontend-lint` exits 0 (no ESLint errors or warnings)
- [x] `cd frontend && npm run format:check` exits 0 (Prettier reports no formatting issues)
- [x] `cd frontend && npm run build` exits 0 (production build succeeds)
- [x] `just check` exits 0 (backend + frontend lint and typecheck all pass)

## Manual Walkthrough

### Dev server starts

- [ ] `just frontend-dev` starts the Vite dev server on port 5173 (or configured port)
- [ ] Browser opens `http://localhost:5173` without console errors
- [ ] `http://localhost:5173/` redirects to `http://localhost:5173/dashboard`

### Routes

- [ ] `/dashboard` — renders "Dashboard" heading and "Coming soon." text
- [ ] `/currencies` — renders "Currencies" heading
- [ ] `/tags` — renders "Tags" heading
- [ ] `/institutions` — renders "Institutions" heading
- [ ] `/accounts` — renders "Accounts" heading
- [ ] `/balances` — renders "Balances" heading
- [ ] `/reports` — renders "Reports" heading
- [ ] `/import-export` — renders "Import / Export" heading
- [ ] Navigating to an unknown path (e.g. `/foo`) does not crash; falls back gracefully

### Layout

- [ ] Sidebar is visible on all routes (except redirect)
- [ ] Header displays "nwtracker"
- [ ] Clicking each sidebar link navigates to the correct route without a full page reload
- [ ] Active link in sidebar is visually distinct from inactive links

### API proxy (requires backend running)

- [ ] With `just dev` running, `fetch('/api/health')` from the browser console returns 200
- [ ] No CORS errors in the browser console

### Cleanup

- [ ] No default Vite boilerplate visible in the browser (no spinning React logo, no "Vite + React" heading)
- [ ] `<title>` in the browser tab reads "nwtracker"

## Definition of Done

- All checklist items above are checked
- `npm run build` produces a clean production build under `frontend/dist/`
- `frontend/README.md` exists and covers install, dev, and code quality commands
- No placeholder or TODO comments left in the committed source files
- The `frontend/` directory is committed and tracked by git
