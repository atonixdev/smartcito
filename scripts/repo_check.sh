#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root_dir"

required_dirs=(
  "ai"
  "gpuops"
  "gpuops/intelligence"
  "gpuops/intelligence/physics"
  "gpuops/intelligence/robotics"
  "gpuops/intelligence/mapping"
  "gpuops/intelligence/distance"
  "gpuops/intelligence/camera"
  "gpuops/intelligence/solvers"
  "gpuops/intelligence/optimization"
  "gpuops/intelligence/utils"
  "robot"
  "robot/physics"
  "robot/perception"
  "robot/sensors"
  "robot/navigation"
  "robot/ai"
  "robot/cloud"
  "robot/ros2_ws"
  "orcaapi"
  "services"
  "webapp"
  "docs"
  "scripts"
)

failures=0

for d in "${required_dirs[@]}"; do
  if [[ ! -d "$d" ]]; then
    echo "[FAIL] Missing required directory: $d"
    failures=$((failures + 1))
  fi
done

if [[ -d "ai/keras_stack" ]]; then
  echo "[FAIL] Deprecated path detected: ai/keras_stack (use ai/model_stack)"
  failures=$((failures + 1))
fi

if [[ ! -f "docs/REPOSITORY_STRUCTURE.md" ]]; then
  echo "[FAIL] Missing docs/REPOSITORY_STRUCTURE.md"
  failures=$((failures + 1))
fi

if [[ ! -f "docs/WORKSPACE_ORGANIZATION.md" ]]; then
  echo "[FAIL] Missing docs/WORKSPACE_ORGANIZATION.md"
  failures=$((failures + 1))
fi

if [[ "$failures" -gt 0 ]]; then
  echo "\nRepository structure check failed with $failures issue(s)."
  exit 1
fi

echo "Repository structure check passed."
