<!--
================================================================================
 File: CONTRIBUTING.md
 Purpose:
   Guide for new and existing contributors. Explains how to set up a dev
   environment, branch naming, commit style, PR review process, and how
   contributions are licensed.
================================================================================
-->

# Contributing to SmartCito

First off — **thank you** for considering contributing. SmartCito is a
community-driven, open project, and every PR, issue, or doc fix matters.

This document explains how to contribute effectively. If anything is unclear,
open a discussion — improving this guide is itself a great first contribution.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Ways to Contribute](#ways-to-contribute)
3. [Development Environment](#development-environment)
4. [Branching & Commit Style](#branching--commit-style)
5. [Pull Request Process](#pull-request-process)
6. [Coding Standards](#coding-standards)
7. [Documentation Standards](#documentation-standards)
8. [Testing](#testing)
9. [Licensing of Contributions](#licensing-of-contributions)

---

## Code of Conduct

By participating, you agree to uphold our [Code of Conduct](CODE_OF_CONDUCT.md).
Be kind, be curious, assume good intent.

---

## Ways to Contribute

- 🐛 **Report bugs** with clear reproduction steps.
- ✨ **Propose features** through GitHub Issues with the `enhancement` label.
- 🧪 **Add tests** — coverage gaps are real contributions.
- 📝 **Improve docs** — typos count!
- 🔌 **Add connectors** — new IoT or city-system integrations.
- 🎨 **Design dashboards** — UX and accessibility welcome.

Look for issues labeled `good first issue` and `help wanted`.

---

## Development Environment

### Citosmart (Python / FastAPI)

```bash
cd citosmart
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Run linters and tests before pushing:

```bash
ruff check .
black --check .
mypy app
pytest
```

### Webapp (React / Vite / TypeScript)

```bash
cd webapp
npm install
npm run dev      # http://localhost:5173
npm run lint
npm run test
npm run build
```

### Full Stack (Docker)

```bash
cp .env.example .env
docker compose up --build
```

---

## Branching & Commit Style

- SmartCito follows GitFlow:
  - `main` stays production-ready.
  - `develop` is the integration branch for active feature work.
  - `feature/<module-name>` branches start from `develop` and merge back into `develop`.
  - `release/<version>` branches start from `develop` and merge into both `main` and `develop`.
  - `hotfix/<name>` branches start from `main` and merge into both `main` and `develop`.
- Pull the latest `develop` before feature work:

```bash
git checkout develop
git pull origin develop
git checkout -b feature/<module-name>
```

- Branch names are enforced in CI for pull requests:
  - `feature/*` can only target `develop`
  - `release/*` can target `main` or `develop`
  - `hotfix/*` can target `main` or `develop`
- Commits follow **[Conventional Commits](https://www.conventionalcommits.org/)**:
  - `feat(api): add traffic ingestion endpoint`
  - `fix(webapp): correct sensor map zoom`
  - `docs: clarify Kafka setup`

Conventional commits power our automated changelog.

---

## Pull Request Process

1. Fork → branch → commit → push → open a PR against the correct GitFlow base branch.
2. Fill out the PR template — describe **what**, **why**, and **how tested**.
3. Ensure CI is green for tests, security, and Kubernetes/container checks.
4. Security checklist sign-off is required on every PR.
5. At least **two maintainer approvals** are required before merge.
6. Squash-merge into `develop`; only release or hotfix flows should land in `main`.

PRs should be **small and focused**. Split large changes into a series.

See [`docs/GITFLOW.md`](docs/GITFLOW.md) for the branch map and release flow.

---

## Coding Standards

### Python

- Target **Python 3.11+**.
- Format with **Black** (line length 100).
- Lint with **Ruff**.
- Type-check with **mypy** (strict where reasonable).
- Prefer **async** where I/O bound (FastAPI, httpx).

### TypeScript / React

- **Strict** TypeScript (`"strict": true`).
- Functional components + hooks only.
- ESLint + Prettier enforced in CI.
- Co-locate component, styles, and tests.

### Enterprise Frontend Checklist

Before merging frontend changes, verify:

- spacing uses only the 8-point scale: 4, 8, 16, 24, 32, 40, 48px,
- typography follows the SmartCito hierarchy,
- cards use the shared 12px radius / 24px padding rule,
- header behavior remains sticky, aligned, and collapsible,
- icons are SVG and use the SmartCito blue accent,
- dark and light modes are both readable,
- pages use `PageTitle`, `SectionContainer`, `Grid`, and `Card` where practical,
- no one-off colors or random spacing values are introduced.

### Enterprise UI Standards

- Use `IBM Plex Sans` for product UI and `IBM Plex Mono` for logs, code, and technical values.
- Follow the 8-point grid: 4, 8, 16, 24, 32, and 48px.
- Buttons should be 44px high, 6px radius, medium weight, and use subtle shadows.
- Cards and panels should use 24px padding, 10px radius, and a low-contrast border.
- Do not introduce random colors, mixed fonts, or one-off spacing values.
- Prefer shared classes in `webapp/src/styles/global.css` before adding new styles.

### General

- No commented-out code in PRs.
- No secrets in commits — use `.env` (which is gitignored).

---

## Documentation Standards

**Every file** in SmartCito starts with a documentation header describing:

- The file's purpose
- Its inputs / outputs / side effects
- Notable design decisions or trade-offs

This makes the codebase teachable and welcoming to newcomers.
See existing files for the pattern.

Public APIs and complex functions require docstrings / JSDoc.

---

## Testing

- Citosmart uses **pytest** with `pytest-asyncio`.
- Webapp uses **Vitest** and **React Testing Library**.
- New features must ship with tests.
- Bug fixes must include a regression test.

---

## Licensing of Contributions

By submitting a contribution, you agree it is licensed under the
[Apache License 2.0](LICENSE), the same license as the project. This is the
standard "inbound = outbound" model. No CLA is required at this time.
