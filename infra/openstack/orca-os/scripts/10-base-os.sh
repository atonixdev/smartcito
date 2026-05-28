#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND="${DEBIAN_FRONTEND:-noninteractive}"

apt-get update
apt-get install -y --no-install-recommends \
  apt-transport-https \
  auditd \
  audispd-plugins \
  ca-certificates \
  chrony \
  cloud-init \
  curl \
  fail2ban \
  gnupg \
  grub-efi-amd64 \
  grub-efi-amd64-signed \
  gzip \
  jq \
  locales \
  lsb-release \
  net-tools \
  openssh-server \
  qemu-guest-agent \
  rsyslog \
  shim-signed \
  software-properties-common \
  sudo \
  tcpdump \
  traceroute \
  ufw \
  unattended-upgrades \
  unzip \
  vim \
  wget \
  xfsprogs \
  zip

locale-gen en_US.UTF-8
update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8

cat >/etc/cloud/cloud.cfg.d/99-orca-datasource.cfg <<'EOF'
datasource_list: [ OpenStack, ConfigDrive, NoCloud ]
EOF

systemctl enable qemu-guest-agent
systemctl enable chrony
systemctl enable auditd
systemctl enable rsyslog