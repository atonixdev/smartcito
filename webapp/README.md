<!--
================================================================================
 File: webapp/README.md
 Purpose: Dev quickstart for the Orca React docs and downloads site.
================================================================================
-->

# Orca Webapp (React + Vite)

The local-first documentation and downloads site for ORCA.

## Container Image

- Build file: `webapp/Dockerfile`
- What the image does: builds the React docs site with Vite and serves the production bundle from nginx on port `80`.
- What ships in the runtime image: compiled static assets, nginx config, and a copy of this README at `/usr/share/nginx/html/README.md`.

## Quickstart

```bash
npm install
npm run dev          # http://localhost:5173
```

The dev server proxies `/api` to `http://localhost:8000`, so start the
backend API with `uvicorn app.main:app --reload` from [`../orcaapi/`](../orcaapi/)
in another shell, or use `docker compose up` from the repo root.

## Project Layout

```
webapp/
├── index.html                 # Vite entry HTML
├── vite.config.ts             # Vite + Vitest config
├── tsconfig.json              # Strict TypeScript options
├── package.json
└── src/
    ├── main.tsx               # React + providers entrypoint
    ├── App.tsx                # Shell + routes
    ├── pages/                 # One file per route
    ├── pages/                 # Documentation and download routes
    ├── styles/global.css      # Minimal design system
    └── test/setup.ts          # Vitest setup
```

## Conventions

- **Every file** opens with a documentation header (see existing files).
- The webapp is now static-content oriented; avoid reintroducing dashboard-only
  API clients or browser authentication flows.
- TypeScript is strict; do not silence errors with `any`.

## Scripts

| Command          | Purpose                                  |
|------------------|------------------------------------------|
| `npm run dev`    | Vite dev server with HMR                 |
| `npm run build`  | Type-check + production build to `dist/` |
| `npm run preview`| Serve the production build locally       |
| `npm run lint`   | ESLint (zero warnings tolerated)         |
| `npm run test`   | Vitest in CI mode                        |
