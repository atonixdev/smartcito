#!/usr/bin/env bash

set -euo pipefail

env_file="${1:-.env}"
namespace="${2:-backend}"

load_env_file() {
  local line
  local key
  local value

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"

    if [[ -z "${line//[[:space:]]/}" || "$line" =~ ^[[:space:]]*# ]]; then
      continue
    fi

    key="${line%%=*}"
    value="${line#*=}"

    key="${key#"${key%%[![:space:]]*}"}"
    key="${key%"${key##*[![:space:]]}"}"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"

    if [[ "$value" == \"*\" && "$value" == *\" ]]; then
      value="${value:1:${#value}-2}"
    elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
      value="${value:1:${#value}-2}"
    else
      value="${value%%[[:space:]]#*}"
      value="${value%"${value##*[![:space:]]}"}"
    fi

    export "$key=$value"
  done < "$env_file"
}

if [[ ! -f "$env_file" ]]; then
  echo "Environment file not found: $env_file" >&2
  exit 1
fi

load_env_file

: "${DB_PASSWORD:?DB_PASSWORD is required}"
: "${AUTH_JWT_SECRET:?AUTH_JWT_SECRET is required}"
: "${OPENSTACK_AUTH_URL:?OPENSTACK_AUTH_URL is required}"
: "${OPENSTACK_PROJECT:?OPENSTACK_PROJECT is required}"
: "${OPENSTACK_USER:?OPENSTACK_USER is required}"
: "${OPENSTACK_PASSWORD:?OPENSTACK_PASSWORD is required}"

secret_args=(
  create secret generic smartcito-platform-secrets
  --namespace "$namespace"
  --dry-run=client
  -o yaml
  --from-literal=DB_PASSWORD="$DB_PASSWORD"
  --from-literal=AUTH_JWT_SECRET="$AUTH_JWT_SECRET"
  --from-literal=KAFKA_KRAFT_CLUSTER_ID="${KAFKA_KRAFT_CLUSTER_ID:-change-me-kraft-cluster-id}"
  --from-literal=OPENSTACK_AUTH_URL="$OPENSTACK_AUTH_URL"
  --from-literal=OPENSTACK_PROJECT="$OPENSTACK_PROJECT"
  --from-literal=OPENSTACK_USER="$OPENSTACK_USER"
  --from-literal=OPENSTACK_PASSWORD="$OPENSTACK_PASSWORD"
  --from-literal=OPENSTACK_REGION="${OPENSTACK_REGION:-RegionOne}"
  --from-literal=OS_AUTH_URL="$OPENSTACK_AUTH_URL"
  --from-literal=OS_PROJECT_NAME="$OPENSTACK_PROJECT"
  --from-literal=OS_USERNAME="$OPENSTACK_USER"
  --from-literal=OS_PASSWORD="$OPENSTACK_PASSWORD"
  --from-literal=OS_REGION_NAME="${OPENSTACK_REGION:-RegionOne}"
)

if [[ -n "${OPENSTACK_PROJECT_ID:-}" ]]; then
  secret_args+=(--from-literal=OPENSTACK_PROJECT_ID="$OPENSTACK_PROJECT_ID")
  secret_args+=(--from-literal=OS_PROJECT_ID="$OPENSTACK_PROJECT_ID")
fi

if [[ -n "${OPENSTACK_USER_DOMAIN_NAME:-}" ]]; then
  secret_args+=(--from-literal=OPENSTACK_USER_DOMAIN_NAME="$OPENSTACK_USER_DOMAIN_NAME")
  secret_args+=(--from-literal=OS_USER_DOMAIN_NAME="$OPENSTACK_USER_DOMAIN_NAME")
fi

kubectl "${secret_args[@]}" | kubectl apply -f -