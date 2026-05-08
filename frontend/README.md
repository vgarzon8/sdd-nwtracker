# nwtracker — Frontend

React + TypeScript + Vite frontend for the nwtracker personal net worth tracker.

## Prerequisites

- Node.js 22+
- Backend running on port 8000 (see `../backend/README.md`)

## Install

```bash
just frontend-install
# or: cd frontend && npm install
```

## Dev server

```bash
just frontend-dev
```

Opens at `http://localhost:5173`. API calls to `/api/*` are proxied to `http://localhost:8000` — start the backend first with `just dev`.

## Code quality

```bash
just frontend-lint        # ESLint
just frontend-typecheck   # TypeScript strict check (tsc --noEmit)
just frontend-format      # Prettier auto-format

cd frontend && npm run format:check   # Prettier check (no writes)
```

Run everything (backend + frontend) at once:

```bash
just check
```

## Build

```bash
cd frontend && npm run build
# Output: frontend/dist/
```
