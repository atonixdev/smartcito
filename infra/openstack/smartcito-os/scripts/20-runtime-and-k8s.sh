#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND="${DEBIAN_FRONTEND:-noninteractive}"
KUBERNETES_VERSION="${KUBERNETES_VERSION:-1.30}"

apt-get update
apt-get install -y --no-install-recommends \
  build-essential \
  conntrack \
  containerd \
  cri-tools \
  ebtables \
  ethtool \
  iproute2 \
  iptables \
  java-common \
  libffi-dev \
  libgl1 \
  libglib2.0-0 \
  libgomp1 \
  libjpeg-turbo8 \
  liblapack3 \
  libopenblas0 \
  libpq-dev \
  libssl-dev \
  libxml2 \
  libxslt1.1 \
  nfs-common \
  openjdk-17-jre-headless \
  python3 \
  python3-pip \
  python3-venv \
  socat \
  zlib1g

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" >/etc/apt/sources.list.d/nodesource.list

curl -fsSL https://pkgs.k8s.io/core:/stable:/v${KUBERNETES_VERSION}/deb/Release.key | \
  gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v${KUBERNETES_VERSION}/deb/ /" > /etc/apt/sources.list.d/kubernetes.list

apt-get update
apt-get install -y --no-install-recommends nodejs kubeadm kubelet kubectl
apt-mark hold kubeadm kubelet kubectl

containerd config default >/etc/containerd/config.toml
sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml

cat >/etc/modules-load.d/smartcito-k8s.conf <<'EOF'
overlay
br_netfilter
EOF

modprobe overlay
modprobe br_netfilter

cat >/etc/sysctl.d/99-smartcito-k8s.conf <<'EOF'
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
EOF

sysctl --system
systemctl enable containerd