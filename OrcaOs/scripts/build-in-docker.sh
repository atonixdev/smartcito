#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_TAG="orcos-toolchain:latest"
CONTAINER_RUNTIME="${CONTAINER_RUNTIME:-}"

detect_runtime() {
	if [[ -n "$CONTAINER_RUNTIME" ]]; then
		if command -v "$CONTAINER_RUNTIME" >/dev/null 2>&1; then
			echo "$CONTAINER_RUNTIME"
			return 0
		fi
		echo "Configured CONTAINER_RUNTIME '$CONTAINER_RUNTIME' was not found in PATH." >&2
		exit 1
	fi

	if command -v docker >/dev/null 2>&1; then
		echo docker
		return 0
	fi

	if command -v podman >/dev/null 2>&1; then
		echo podman
		return 0
	fi

	echo "No container runtime found. Install docker or podman, or set CONTAINER_RUNTIME." >&2
	exit 1
}

RUNTIME="$(detect_runtime)"

cd "$ROOT_DIR"

"$RUNTIME" build -t "$IMAGE_TAG" -f Dockerfile.toolchain .
"$RUNTIME" run --rm -v "$ROOT_DIR":/workspace -w /workspace "$IMAGE_TAG" make all
