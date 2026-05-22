<!--
================================================================================
 File: webapp/README.md
 Purpose: Dev quickstart for the SmartCito React dashboard.
================================================================================
-->

# SmartCito Webapp (React + Vite)

The operator dashboard for the Urban Data Backbone.

## Quickstart

```bash
npm install
npm run dev          # http://localhost:5173
```

By default, the webapp runs in offline demo mode. Dashboard log calls such as
`/api/location/dashboard/logs` are handled locally by Vite so a stopped map
service does not produce `ECONNREFUSED` proxy noise.

Only enable backend proxying when the backend services are running:

```bash
VITE_ENABLE_BACKEND=true npm run dev
```

Then start the services in separate terminals:

```bash
cd ../citosmart
uvicorn app.main:app --reload --port 8000
```

```bash
cd ../map
npm start
```

The dev server proxies `/api` to `http://localhost:8000`, so start the
citosmart with `uvicorn app.main:app --reload` in another shell (or use
`docker compose up` from the repo root).

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

To enable the real WebGL 3D world map, provide a Mapbox token:

```bash
VITE_MAPBOX_TOKEN=pk_your_mapbox_token npm run dev
```

Without `VITE_MAPBOX_TOKEN`, the dashboard does **not** render a fake map. It
shows a configuration message until the real Mapbox GL map can load.

The 3D map supports:

- country click and fly-to zoom,
- reverse-geocoded location popups,
- 2D / 3D toggle,
- terrain and 3D building extrusion,
- verified device markers,
- GPS trails,
- camera overlays,
- weather, traffic, and threat layer toggles.

## Enterprise UI System

The webapp uses IBM Plex as the primary UI typeface:

- `IBM Plex Sans` for all interface text
- `IBM Plex Mono` for code, logs, tables, and technical values

Layout follows an 8-point spacing grid:

| Token | Value | Use |
|---|---:|---|
| `--space-1` | 4px | micro spacing |
| `--space-2` | 8px | base spacing |
| `--space-4` | 16px | section spacing |
| `--space-6` | 24px | card padding |
| `--space-8` | 32px | layout gutters |
| `--space-12` | 48px | page spacing |

Use existing `.panel`, `.feature-card`, `.page-title-row`, `.content-grid-12`,
`.btn`, and dashboard tab styles before adding new component-specific spacing.
