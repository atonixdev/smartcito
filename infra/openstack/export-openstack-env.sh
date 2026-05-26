#!/usr/bin/env bash

set -euo pipefail

env_file="${1:-.env}"

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

: "${OPENSTACK_AUTH_URL:?OPENSTACK_AUTH_URL is required}"
: "${OPENSTACK_USER:?OPENSTACK_USER is required}"
: "${OPENSTACK_PASSWORD:?OPENSTACK_PASSWORD is required}"

if [[ -z "${OPENSTACK_PROJECT:-}" && -z "${OPENSTACK_PROJECT_ID:-}" ]]; then
  echo "Either OPENSTACK_PROJECT or OPENSTACK_PROJECT_ID is required" >&2
  exit 1
fi

export TF_VAR_auth_url="$OPENSTACK_AUTH_URL"
export TF_VAR_username="$OPENSTACK_USER"
export TF_VAR_password="$OPENSTACK_PASSWORD"
export TF_VAR_region="${OPENSTACK_REGION:-RegionOne}"

export OS_AUTH_URL="$OPENSTACK_AUTH_URL"
export OS_USERNAME="$OPENSTACK_USER"
export OS_PASSWORD="$OPENSTACK_PASSWORD"
export OS_REGION_NAME="${OPENSTACK_REGION:-RegionOne}"

if [[ -n "${OPENSTACK_PROJECT_ID:-}" ]]; then
  export TF_VAR_project_id="$OPENSTACK_PROJECT_ID"
  export OS_PROJECT_ID="$OPENSTACK_PROJECT_ID"
else
  export TF_VAR_project_name="$OPENSTACK_PROJECT"
  export OS_PROJECT_NAME="$OPENSTACK_PROJECT"
fi

if [[ -n "${OPENSTACK_USER_DOMAIN_NAME:-}" ]]; then
  export TF_VAR_user_domain_name="$OPENSTACK_USER_DOMAIN_NAME"
  export OS_USER_DOMAIN_NAME="$OPENSTACK_USER_DOMAIN_NAME"
fi

if [[ $# -gt 1 ]]; then
  shift
  exec "$@"
fi

cat <<EOF
Exported OpenStack variables from $env_file
TF_VAR_auth_url=$TF_VAR_auth_url
TF_VAR_region=$TF_VAR_region
TF_VAR_username=$TF_VAR_username
TF_VAR_project_id=${TF_VAR_project_id:-}
TF_VAR_project_name=${TF_VAR_project_name:-}
TF_VAR_user_domain_name=${TF_VAR_user_domain_name:-}
EOF