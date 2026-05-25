#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND="${DEBIAN_FRONTEND:-noninteractive}"

apt-get autoremove -y
apt-get clean
rm -rf /var/lib/apt/lists/*
rm -rf /tmp/* /var/tmp/*
cloud-init clean --logs --seed || true
truncate -s 0 /etc/machine-id
truncate -s 0 /var/log/wtmp || true
truncate -s 0 /var/log/btmp || true
find /var/log -type f -name '*.log' -exec truncate -s 0 {} \;
fstrim -av || true