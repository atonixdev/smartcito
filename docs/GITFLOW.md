<!--
================================================================================
 File: docs/GITFLOW.md
 Purpose:
   Orca's GitFlow operating model: branch roles, gate checks, and the
   workflow used by contributors and maintainers.
================================================================================
-->

# Orca GitFlow

## Main Branches

- `main`: production-ready code only.
- `develop`: integration branch for completed feature work.

## Supporting Branches

- `feature/<module-name>`: created from `develop`, merged back to `develop`.
- `release/<version>`: created from `develop`, merged to `main` and `develop`.
- `hotfix/<name>`: created from `main`, merged to `main` and `develop`.

## Required Gates

Every pull request must pass these checks:

- Unit and integration validation from the repository test suites.
- Security validation from the security workflow and review checklist.
- Kubernetes and container validation for manifests under `infra/kubernetes/`.
- CODEOWNERS review coverage.

Repository protection for `main` and `develop` is expected to require:

- 2 approving reviews
- successful status checks
- resolved review conversations
- no force pushes or branch deletions

## Daily Developer Workflow

```bash
git checkout develop
git pull origin develop
git checkout -b feature/<module-name>
```

Implement the assigned service or folder, validate locally, then open a PR into
`develop`.

## Release Workflow

```bash
git checkout develop
git pull origin develop
git checkout -b release/v1.0
```

Stabilize the release branch, then merge it into `main` and back into `develop`.

## Hotfix Workflow

```bash
git checkout main
git pull origin main
git checkout -b hotfix/<name>
```

Ship the urgent fix to `main`, then back-merge it into `develop`.

## Automation Included In This Repository

- `.github/workflows/gitflow.yml` enforces branch naming and target rules.
- `.github/workflows/ci.yml` runs tests on GitFlow branches.
- `.github/workflows/security.yml` enforces security sign-off and container or manifest checks.
- `.github/CODEOWNERS` defines review ownership.
- `scripts/gitflow/bootstrap.sh` can create `develop` and apply GitHub branch protection through the GitHub CLI.
