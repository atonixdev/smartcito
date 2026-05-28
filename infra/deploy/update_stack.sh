#!/usr/bin/env bash

set -euo pipefail

: "${DEPLOY_PATH:?DEPLOY_PATH is required}"
: "${IMAGE_REGISTRY:=atonixdev}"
: "${IMAGE_TAG:=1.0.0}"

deploy_strategy="${DEPLOY_STRATEGY:-blue-green-api}"
compose_file="docker-compose.services.yml"
runtime_dir="infra/deploy/runtime"
api_upstream_runtime_file="$runtime_dir/api-upstream.conf"
active_api_slot_file="$runtime_dir/active_api_slot"
keep_previous_api_slot="${BLUE_GREEN_KEEP_OLD_SLOT:-false}"
legacy_api_container_name="orca-citosmart"

cd "$DEPLOY_PATH"

cat > .env <<EOF
APP_ENV=${APP_ENV:-staging}
DB_HOST=${DB_HOST:-postgres}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-orca}
DB_PASSWORD=${DB_PASSWORD:-change-me}
DB_NAME=${DB_NAME:-orca}
MEMCACHED_SERVERS=${MEMCACHED_SERVERS:-memcached-1:11211,memcached-2:11211,memcached-3:11211}
MEMCACHED_DEFAULT_TTL_SECONDS=${MEMCACHED_DEFAULT_TTL_SECONDS:-60}
MEMCACHED_API_TTL_SECONDS=${MEMCACHED_API_TTL_SECONDS:-60}
MEMCACHED_DASHBOARD_TTL_SECONDS=${MEMCACHED_DASHBOARD_TTL_SECONDS:-45}
MEMCACHED_DEVICE_METADATA_TTL_SECONDS=${MEMCACHED_DEVICE_METADATA_TTL_SECONDS:-300}
MEMCACHED_AI_TTL_SECONDS=${MEMCACHED_AI_TTL_SECONDS:-1800}
MEMCACHED_SESSION_TTL_SECONDS=${MEMCACHED_SESSION_TTL_SECONDS:-3600}
KAFKA_BROKER_URL=${KAFKA_BROKER_URL:-kafka:9092}
MESSAGE_BUS_URL=${MESSAGE_BUS_URL:-${KAFKA_BROKER_URL:-kafka:9092}}
OBJECT_STORAGE_ENDPOINT=${OBJECT_STORAGE_ENDPOINT:-file:///srv/orca/object_storage}
OBJECT_STORAGE_BUCKET=${OBJECT_STORAGE_BUCKET:-orca-artifacts}
AUTH_JWT_SECRET=${AUTH_JWT_SECRET:-change-me}
AUTH_ISSUER=${AUTH_ISSUER:-orca.local}
AUTH_AUDIENCE=${AUTH_AUDIENCE:-orca-clients}
SECRET_KEY=${AUTH_JWT_SECRET:-change-me}
POSTGRES_HOST=${DB_HOST:-postgres}
POSTGRES_PORT=${DB_PORT:-5432}
POSTGRES_USER=${DB_USER:-orca}
POSTGRES_PASSWORD=${DB_PASSWORD:-change-me}
POSTGRES_DB=${DB_NAME:-orca}
KAFKA_BOOTSTRAP_SERVERS=${KAFKA_BROKER_URL:-kafka:9092}
CITOSMART_IMAGE=${IMAGE_REGISTRY}/api-gateway:${IMAGE_TAG}
WEBAPP_IMAGE=${IMAGE_REGISTRY}/webapp:${IMAGE_TAG}
CAMERA_IMAGE=${IMAGE_REGISTRY}/camera-service:${IMAGE_TAG}
GPS_IMAGE=${IMAGE_REGISTRY}/gps-service:${IMAGE_TAG}
AI_IMAGE=${IMAGE_REGISTRY}/ai-service:${IMAGE_TAG}
SECURITY_IMAGE=${IMAGE_REGISTRY}/security-service:${IMAGE_TAG}
HARDWARE_IMAGE=${IMAGE_REGISTRY}/hardware-agent:${IMAGE_TAG}
INGESTION_KAFKA_PRODUCER_IMAGE=${IMAGE_REGISTRY}/ingestion-kafka-producer:${IMAGE_TAG}
INGESTION_SPARK_IMAGE=${IMAGE_REGISTRY}/ingestion-spark:${IMAGE_TAG}
EOF

compose=(docker compose -f "$compose_file")
base_services=(postgres redis memcached-1 memcached-2 memcached-3 mqtt kafka)
rolling_services=(
	event-consumer-raw
	event-consumer-clean
	event-consumer-alerts
	ingestion-kafka-producer
	ingestion-spark
	camera-service
	gps-service
	ai-service
	security-service
	hardware-agent
	webapp
)
rolling_partition_services=(citosmart-blue "${rolling_services[@]}")

ensure_blue_green_runtime() {
	mkdir -p "$runtime_dir"

	if [[ ! -f "$active_api_slot_file" ]]; then
		echo blue > "$active_api_slot_file"
	fi

	if [[ ! -f "$api_upstream_runtime_file" ]]; then
		cp "infra/deploy/nginx/upstreams/api-$(current_active_api_slot).conf" "$api_upstream_runtime_file"
	fi
}

api_slot_service() {
	local slot="$1"
	echo "citosmart-$slot"
}

current_active_api_slot() {
	local current_slot
	current_slot="$(tr -d '[:space:]' < "$active_api_slot_file")"
	case "$current_slot" in
		blue|green)
			echo "$current_slot"
			;;
		*)
			echo blue
			;;
	esac
}

inactive_api_slot() {
	local active_slot="$1"
	if [[ "$active_slot" == "blue" ]]; then
		echo green
	else
		echo blue
	fi
}

reload_api_router() {
	local router_container_id
	router_container_id="$(${compose[@]} ps -q api-router)"
	if [[ -z "$router_container_id" ]]; then
		echo "api-router container is not running" >&2
		return 1
	fi

	docker exec "$router_container_id" nginx -s reload >/dev/null
}

service_running() {
	local service_name="$1"
	local container_id

	container_id="$(${compose[@]} ps -q "$service_name")"
	if [[ -z "$container_id" ]]; then
		return 1
	fi

	[[ "$(docker inspect --format '{{.State.Running}}' "$container_id")" == "true" ]]
}

legacy_api_container_exists() {
	docker ps -a --format '{{.Names}}' | grep -qx "$legacy_api_container_name"
}

remove_legacy_api_container() {
	if legacy_api_container_exists; then
		docker rm -f "$legacy_api_container_name" >/dev/null 2>&1 || true
	fi
}

validate_router_traffic() {
	local expected_slot="$1"
	local expected_service
	expected_service="$(api_slot_service "$expected_slot")"

	for _ in $(seq 1 30); do
		local router_container_id
		router_container_id="$(${compose[@]} ps -q api-router)"
		if [[ -n "$router_container_id" ]] \
			&& docker exec "$router_container_id" wget -qO- http://127.0.0.1:8000/api/v1/health/ready | grep -q '"status":"ready"' \
			&& grep -q "$expected_service" "$api_upstream_runtime_file"; then
			return 0
		fi
		sleep 2
	done

	echo "Blue/green router validation failed for slot $expected_slot" >&2
	return 1
}

switch_api_traffic() {
	local target_slot="$1"
	local previous_slot="$2"

	cp "infra/deploy/nginx/upstreams/api-${target_slot}.conf" "$api_upstream_runtime_file"
	echo "$target_slot" > "$active_api_slot_file"

	if ! reload_api_router || ! validate_router_traffic "$target_slot"; then
		cp "infra/deploy/nginx/upstreams/api-${previous_slot}.conf" "$api_upstream_runtime_file"
		echo "$previous_slot" > "$active_api_slot_file"
		reload_api_router || true
		return 1
	fi
}

service_exists() {
	local service_name="$1"
	"${compose[@]}" config --services | grep -qx "$service_name"
}

wait_for_service() {
	local service_name="$1"
	local container_id
	local status

	for _ in $(seq 1 60); do
		container_id="$("${compose[@]}" ps -q "$service_name")"
		if [[ -z "$container_id" ]]; then
			sleep 2
			continue
		fi

		status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_id")"
		case "$status" in
			healthy|running)
				return 0
				;;
			unhealthy|exited|dead)
				echo "Service $service_name failed with status $status" >&2
				docker logs "$container_id" >&2 || true
				return 1
				;;
		esac

		sleep 2
	done

	echo "Timed out waiting for service $service_name" >&2
	return 1
}

roll_service() {
	local service_name="$1"

	if ! service_exists "$service_name"; then
		return 0
	fi

	"${compose[@]}" up -d --no-deps "$service_name"
	wait_for_service "$service_name"
}

ensure_blue_green_runtime
"${compose[@]}" pull

case "$deploy_strategy" in
	blue-green-api)
		"${compose[@]}" up -d "${base_services[@]}"
		for service_name in "${base_services[@]}"; do
			wait_for_service "$service_name"
		done

		bootstrap_from_legacy=false
		active_slot="$(current_active_api_slot)"
		if ! service_running citosmart-blue && ! service_running citosmart-green && legacy_api_container_exists; then
			bootstrap_from_legacy=true
			target_slot="blue"
			active_slot="blue"
		else
			"${compose[@]}" up -d api-router
			wait_for_service api-router
			target_slot="$(inactive_api_slot "$active_slot")"
		fi

		target_service="$(api_slot_service "$target_slot")"
		previous_service="$(api_slot_service "$active_slot")"

		bash infra/deploy/run_migrations.sh "$compose_file" "$target_service"

		roll_service "$target_service"

		if [[ "$bootstrap_from_legacy" == "true" ]]; then
			cp "infra/deploy/nginx/upstreams/api-${target_slot}.conf" "$api_upstream_runtime_file"
			echo "$target_slot" > "$active_api_slot_file"
			remove_legacy_api_container
			"${compose[@]}" up -d api-router
			wait_for_service api-router
		fi

		switch_api_traffic "$target_slot" "$active_slot"

		if [[ "$bootstrap_from_legacy" != "true" ]] && [[ "$keep_previous_api_slot" != "true" ]] && service_exists "$previous_service"; then
			"${compose[@]}" stop "$previous_service" >/dev/null 2>&1 || true
		fi

		for service_name in "${rolling_services[@]}"; do
			roll_service "$service_name"
		done
		;;
	rolling-partitions)
		"${compose[@]}" up -d "${base_services[@]}" api-router
		for service_name in "${base_services[@]}" api-router; do
			wait_for_service "$service_name"
		done

		bash infra/deploy/run_migrations.sh "$compose_file" citosmart-blue
		roll_service citosmart-blue
		switch_api_traffic blue "$(current_active_api_slot)"

		for service_name in "${rolling_services[@]}"; do
			roll_service "$service_name"
		done
		;;
	full-stack)
		bash infra/deploy/run_migrations.sh "$compose_file" citosmart-blue
		"${compose[@]}" up -d --remove-orphans --wait
		;;
	*)
		echo "Unsupported DEPLOY_STRATEGY: $deploy_strategy" >&2
		exit 1
		;;
esac