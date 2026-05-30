#!/usr/bin/env bash
# ============================================================================
# File: scripts/gitflow/bootstrap.sh
# Purpose:
#   Bootstrap Orca GitFlow branches and branch-protection rules using the
#   GitHub CLI. Requires an authenticated `gh` session with repo admin rights.
# ============================================================================

set -euo pipefail

repo="${1:-AtonixCorp/Orca}"
remote="${2:-origin}"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required" >&2
  exit 1
fi

if ! git remote get-url "$remote" >/dev/null 2>&1; then
  echo "git remote '$remote' does not exist" >&2
  exit 1
fi

current_branch=$(git rev-parse --abbrev-ref HEAD)

if ! git show-ref --verify --quiet refs/heads/develop; then
  git branch develop main
fi

git push "$remote" develop

gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "/repos/${repo}/branches/main/protection" \
  -f required_status_checks.strict=true \
  -f required_status_checks.contexts[]="GitFlow / GitFlow branch policy" \
  -f required_status_checks.contexts[]="CI / Unit Tests and Quality (orcaapi)" \
  -f required_status_checks.contexts[]="CI / Unit Tests and Quality (webapp)" \
  -f required_status_checks.contexts[]="Security / Security checklist sign-off" \
  -f required_status_checks.contexts[]="Security / Security checks (backend)" \
  -f required_status_checks.contexts[]="Security / Security checks (webapp)" \
  -f required_status_checks.contexts[]="Security / Secret scanning" \
  -f required_status_checks.contexts[]="Security / Container build and manifest checks" \
  -F enforce_admins=true \
  -f required_pull_request_reviews.dismiss_stale_reviews=true \
  -f required_pull_request_reviews.require_code_owner_reviews=true \
  -F required_pull_request_reviews.required_approving_review_count=2 \
  -F restrictions= \
  -F allow_force_pushes=false \
  -F allow_deletions=false \
  -F required_conversation_resolution=true

gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "/repos/${repo}/branches/develop/protection" \
  -f required_status_checks.strict=true \
  -f required_status_checks.contexts[]="GitFlow / GitFlow branch policy" \
  -f required_status_checks.contexts[]="CI / Unit Tests and Quality (orcaapi)" \
  -f required_status_checks.contexts[]="CI / Unit Tests and Quality (webapp)" \
  -f required_status_checks.contexts[]="Security / Security checklist sign-off" \
  -f required_status_checks.contexts[]="Security / Security checks (backend)" \
  -f required_status_checks.contexts[]="Security / Security checks (webapp)" \
  -f required_status_checks.contexts[]="Security / Secret scanning" \
  -f required_status_checks.contexts[]="Security / Container build and manifest checks" \
  -F enforce_admins=true \
  -f required_pull_request_reviews.dismiss_stale_reviews=true \
  -f required_pull_request_reviews.require_code_owner_reviews=true \
  -F required_pull_request_reviews.required_approving_review_count=2 \
  -F restrictions= \
  -F allow_force_pushes=false \
  -F allow_deletions=false \
  -F required_conversation_resolution=true

git checkout "$current_branch"
echo "GitFlow bootstrap applied for ${repo}"
