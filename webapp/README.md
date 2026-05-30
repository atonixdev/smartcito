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

## GitHub Pages Deployment

The production deployment target for this site is GitHub Pages:

- Repository URL: `https://github.com/AtonixCorp/Orca`
- Pages URL: `https://atonixcorp.github.io/Orca/`
- Workflow: `.github/workflows/deploy-github-pages.yml`

Deployment behavior:

- Pushes to `main` run the Pages workflow automatically.
- The workflow builds the Vite app with `GITHUB_PAGES=true`, so the correct
  base path is generated for the repository slug.
- The workflow copies `index.html` to `404.html` so deep links continue to work
  on GitHub Pages.

Repository setting required once:

- In GitHub, open **Settings > Pages** and set **Source** to **GitHub Actions**.

Local validation command:

```bash
GITHUB_PAGES=true GITHUB_REPOSITORY=AtonixCorp/Orca npm run build
```

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
