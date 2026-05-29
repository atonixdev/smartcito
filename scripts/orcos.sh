#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ORCOS_DIR="$ROOT_DIR/OrcaOs"

usage() {
  cat <<EOF
Usage: scripts/orcos.sh <command>

Commands:
  build            Build OrcOS ISO using host toolchain
  run              Run OrcOS in QEMU (requires host toolchain + qemu)
  docker-build     Build OrcOS ISO in a container toolchain (docker/podman)
  container-build  Alias of docker-build
  clean            Remove OrcOS build artifacts
EOF
}

cmd="${1:-}"
if [[ -z "$cmd" ]]; then
  usage
  exit 1
fi

case "$cmd" in
  build)
    make -C "$ORCOS_DIR" all
    ;;
  run)
    make -C "$ORCOS_DIR" run
    ;;
  docker-build|container-build)
    (cd "$ORCOS_DIR" && bash scripts/build-in-docker.sh)
    ;;
  clean)
    make -C "$ORCOS_DIR" clean
    ;;
  *)
    usage
    exit 1
    ;;
esac
