<!--
================================================================================
 File: frontend/README.md
 Purpose: Dev quickstart for the SmartCito React dashboard.
================================================================================
-->

# SmartCito Frontend (React + Vite)

The operator dashboard for the Urban Data Backbone.

## Quickstart

```bash
npm install
npm run dev          # http://localhost:5173
```

The dev server proxies `/api` to `http://localhost:8000`, so start the
backend with `uvicorn app.main:app --reload` in another shell (or use
`docker compose up` from the repo root).

## Project Layout

```
frontend/
├── index.html                 # Vite entry HTML
├── vite.config.ts             # Vite + Vitest config
├── tsconfig.json              # Strict TypeScript options
├── package.json
└── src/
    ├── main.tsx               # React + providers entrypoint
    ├── App.tsx                # Shell + routes
    ├── pages/                 # One file per route
    ├── components/            # Reusable UI building blocks
    ├── api/                   # Typed API client + React Query hooks
    ├── styles/global.css      # Minimal design system
    └── test/setup.ts          # Vitest setup
```

## Conventions

- **Every file** opens with a documentation header (see existing files).
- All HTTP calls go through `src/api/client.ts` so auth and error handling
  stay centralized.
- Data fetching uses **TanStack Query** — never useEffect for server data.
- TypeScript is strict; do not silence errors with `any`.

## Scripts

| Command          | Purpose                                  |
|------------------|------------------------------------------|
| `npm run dev`    | Vite dev server with HMR                 |
| `npm run build`  | Type-check + production build to `dist/` |
| `npm run preview`| Serve the production build locally       |
| `npm run lint`   | ESLint (zero warnings tolerated)         |
| `npm run test`   | Vitest in CI mode                        |
