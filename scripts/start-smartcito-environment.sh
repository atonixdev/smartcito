#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$ROOT_DIR/docker-compose.yml}"

log() {
  printf '[smartcito-docker] %s\n' "$*"
}

fail() {
  printf '[smartcito-docker] %s\n' "$*" >&2
  exit 1
}

compose() {
  docker compose -f "$COMPOSE_FILE" "$@"
}

require_file() {
  local path="$1"
  [[ -e "$path" ]] || fail "Missing required file: $path"
}

require_dir() {
  local path="$1"
  [[ -d "$path" ]] || fail "Missing required directory: $path"
}

check_environment() {
  require_file "$ROOT_DIR/.env"
  require_file "$COMPOSE_FILE"
  require_dir "$ROOT_DIR/data"
  require_dir "$ROOT_DIR/data/object_storage"
  require_dir "$ROOT_DIR/database/init"
  require_dir "$ROOT_DIR/infra/deploy/nginx"
  require_dir "$ROOT_DIR/infra/mosquitto"

  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a

  : "${DB_PASSWORD:?DB_PASSWORD must be set in .env}"
  : "${AUTH_JWT_SECRET:?AUTH_JWT_SECRET must be set in .env}"
}

verify_core_images() {
  local images=(
    atonixdev/orca-api-gateway:1.0.0
    atonixdev/orca-webapp:1.0.0
    atonixdev/orca-ai-service:1.0.0
    atonixdev/orca-gps-service:1.0.0
    atonixdev/orca-camera-service:1.0.0
    atonixdev/orca-drone-camera-ingestion:1.0.0
    atonixdev/orca-mapping-geospatial:1.0.0
    atonixdev/orca-mission-control:1.0.0
  )

  for image in "${images[@]}"; do
    docker image inspect "$image" >/dev/null 2>&1 || log "Image not cached locally yet: $image"
  done
}

restart_failed_services() {
  local services=()
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    services+=("${line%%$'\t'*}")
  done < <(compose ps --format '{{.Service}}\t{{.State}}\t{{.Status}}' | awk '$2 != "running" {print}')

  if [[ ${#services[@]} -eq 0 ]]; then
    return
  fi

  log "Restarting failing services: ${services[*]}"
  for service in "${services[@]}"; do
    compose restart "$service"
  done
}

show_service_logs() {
  local services=(
    ai-service
    gps-service
    camera-service
    drone-camera-ingestion
    mapping-geospatial
    mission-control
  )

  for service in "${services[@]}"; do
    log "Recent logs for ${service}"
    compose logs --tail=20 "$service"
  done
}

verify_running_state() {
  local status_output
  status_output="$(compose ps --format '{{.Service}}\t{{.State}}\t{{.Status}}')"
  printf '%s\n' "$status_output"

  if printf '%s\n' "$status_output" | awk '$2 != "running" {exit 1}'; then
    return
  fi

  fail "One or more compose services are not running"
}

verify_core_services() {
  local required=(
    ai-service
    gps-service
    camera-service
    drone-camera-ingestion
    mapping-geospatial
    mission-control
  )

  local status_output
  status_output="$(compose ps --format '{{.Service}}\t{{.State}}')"

  for service in "${required[@]}"; do
    if ! printf '%s\n' "$status_output" | awk -v svc="$service" '$1 == svc && $2 == "running" {found=1} END {exit found ? 0 : 1}'; then
      fail "Required core service is not running: $service"
    fi
  done
}

main() {
  command -v docker >/dev/null 2>&1 || fail "docker is required"

  log "Checking environment prerequisites"
  check_environment

  log "Pulling compose images"
  compose pull

  log "Starting SmartCito compose stack"
  compose up -d

  log "Verifying core image tags"
  verify_core_images

  log "Checking running container state"
  restart_failed_services
  verify_running_state

  log "Checking AI, GPS, camera, map, and fusion services"
  verify_core_services

  log "Showing recent logs for core modules"
  show_service_logs
}

main "$@"
