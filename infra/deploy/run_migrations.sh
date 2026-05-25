#!/usr/bin/env bash

set -euo pipefail

stack_file="${1:-docker-compose.services.yml}"
service_name="${2:-citosmart}"

docker compose -f "$stack_file" run --rm "$service_name" alembic upgrade head