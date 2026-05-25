#!/usr/bin/env bash
set -euo pipefail

ssh_target="${1:-}"

if [[ -z "$ssh_target" ]]; then
  echo "usage: $0 <user@host> [ssh options...]" >&2
  exit 1
fi

shift || true

ssh "$@" "$ssh_target" sudo /opt/smartcito/bin/validate_image.sh