# Contrib

External and experimental contributions to Orca.

Use this folder to propose new modules, dashboards, connectors, or AI models
that are **not yet ready** to live in the core tree. Promoted contributions
graduate into the appropriate top-level module (`ingestion/`, `ai_models/`,
`camera_module/`, etc.) once they meet the project's quality and security
bar.

## Layout

```
contrib/
├── <your-feature>/
│   ├── README.md
│   ├── src/
│   └── tests/
└── README.md
```

## Rules for Contrib

1. **One folder per contribution.** Name it clearly (kebab-case).
2. **Every folder ships a `README.md`** explaining purpose, status, owner,
   and how to run/test it.
3. **No core dependencies on contrib.** Code in `citosmart/` and `webapp/`
   must never import from `contrib/`.
4. **Tests are required**, even for experiments — add them under
   `contrib/<your-feature>/tests/` or [`../tests/`](../tests/).
5. **Security still applies.** Secrets handling, TLS, RBAC, and audit
   requirements (see [`../security/`](../security/)) are non-negotiable.

## Promotion Path

1. Open an issue describing the contribution.
2. Land it under `contrib/<your-feature>/`.
3. Iterate with maintainers.
4. Once stable + reviewed, move into the appropriate top-level module and
   remove the `contrib/` copy in the same PR.

See [`../CONTRIBUTING.md`](../CONTRIBUTING.md) for the full workflow.
