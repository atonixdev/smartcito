#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND="${DEBIAN_FRONTEND:-noninteractive}"
GPU_VENDOR="${GPU_VENDOR:-nvidia}"
ENABLE_NVIDIA_DRIVER="${ENABLE_NVIDIA_DRIVER:-false}"
NVIDIA_DRIVER_PACKAGE="${NVIDIA_DRIVER_PACKAGE:-nvidia-driver-550-server}"

apt-get update
apt-get install -y --no-install-recommends \
  dkms \
  linux-headers-generic \
  pciutils \
  ubuntu-drivers-common

install -m 0755 -d /etc/apt/keyrings /etc/smartcito

case "$GPU_VENDOR" in
  nvidia)
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
      gpg --dearmor -o /etc/apt/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
      sed 's#deb https://#deb [signed-by=/etc/apt/keyrings/nvidia-container-toolkit-keyring.gpg] https://#' \
      >/etc/apt/sources.list.d/nvidia-container-toolkit.list

    apt-get update
    apt-get install -y --no-install-recommends nvidia-container-toolkit

    if [[ "$ENABLE_NVIDIA_DRIVER" == "true" ]]; then
      apt-get install -y --no-install-recommends "$NVIDIA_DRIVER_PACKAGE"
    fi

    if command -v nvidia-ctk >/dev/null 2>&1; then
      nvidia-ctk runtime configure --runtime=containerd || true
    fi
    ;;
  none)
    ;;
  *)
    echo "unsupported GPU vendor: $GPU_VENDOR" >&2
    exit 1
    ;;
esac

cat >/etc/smartcito/gpu-profile.env <<EOF
GPU_VENDOR=$GPU_VENDOR
ENABLE_NVIDIA_DRIVER=$ENABLE_NVIDIA_DRIVER
NVIDIA_DRIVER_PACKAGE=$NVIDIA_DRIVER_PACKAGE
EOF

systemctl restart containerd || true