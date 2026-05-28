#!/usr/bin/env bash

set -euo pipefail

environment_name="${1:-${DEPLOY_ENVIRONMENT:-staging}}"

: "${DEPLOY_HOST:?DEPLOY_HOST is required}"
: "${DEPLOY_USER:?DEPLOY_USER is required}"
: "${DEPLOY_PATH:?DEPLOY_PATH is required}"
: "${IMAGE_REGISTRY:?IMAGE_REGISTRY is required}"
: "${IMAGE_TAG:?IMAGE_TAG is required}"

ssh_opts=(
  -o BatchMode=yes
  -o StrictHostKeyChecking=accept-new
)

ssh "${ssh_opts[@]}" "${DEPLOY_USER}@${DEPLOY_HOST}" \
  "DEPLOY_ENVIRONMENT='${environment_name}' DEPLOY_PATH='${DEPLOY_PATH}' IMAGE_REGISTRY='${IMAGE_REGISTRY}' IMAGE_TAG='${IMAGE_TAG}' DEPLOY_STRATEGY='${DEPLOY_STRATEGY:-blue-green-api}' APP_ENV='${APP_ENV:-$environment_name}' DB_HOST='${DB_HOST:-postgres}' DB_PORT='${DB_PORT:-5432}' DB_USER='${DB_USER:-orca}' DB_PASSWORD='${DB_PASSWORD:-change-me}' DB_NAME='${DB_NAME:-orca}' KAFKA_BROKER_URL='${KAFKA_BROKER_URL:-${MESSAGE_BUS_URL:-kafka:9092}}' MESSAGE_BUS_URL='${MESSAGE_BUS_URL:-${KAFKA_BROKER_URL:-kafka:9092}}' OBJECT_STORAGE_ENDPOINT='${OBJECT_STORAGE_ENDPOINT:-file:///srv/orca/object_storage}' OBJECT_STORAGE_BUCKET='${OBJECT_STORAGE_BUCKET:-orca-artifacts}' AUTH_JWT_SECRET='${AUTH_JWT_SECRET:-change-me}' AUTH_ISSUER='${AUTH_ISSUER:-orca.local}' AUTH_AUDIENCE='${AUTH_AUDIENCE:-orca-clients}' bash -s" < infra/deploy/update_stack.sh