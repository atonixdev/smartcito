#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND="${DEBIAN_FRONTEND:-noninteractive}"
NODE_EXPORTER_VERSION="${NODE_EXPORTER_VERSION:-1.8.2}"
FLUENT_BIT_VERSION="${FLUENT_BIT_VERSION:-3.1.9}"

useradd --system --home /var/lib/node_exporter --shell /usr/sbin/nologin node_exporter || true

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

curl -fsSL -o "$tmp_dir/node_exporter.tar.gz" \
  "https://github.com/prometheus/node_exporter/releases/download/v${NODE_EXPORTER_VERSION}/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz"
tar -xzf "$tmp_dir/node_exporter.tar.gz" -C "$tmp_dir"
install -m 0755 "$tmp_dir/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64/node_exporter" /usr/local/bin/node_exporter

cat >/etc/systemd/system/node_exporter.service <<'EOF'
[Unit]
Description=Prometheus Node Exporter
After=network-online.target
Wants=network-online.target

[Service]
User=node_exporter
Group=node_exporter
ExecStart=/usr/local/bin/node_exporter --web.listen-address=:9100
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

curl -fsSL https://packages.fluentbit.io/fluentbit.key | gpg --dearmor -o /etc/apt/keyrings/fluentbit.gpg
echo "deb [signed-by=/etc/apt/keyrings/fluentbit.gpg] https://packages.fluentbit.io/ubuntu/jammy jammy main" >/etc/apt/sources.list.d/fluent-bit.list
apt-get update
apt-get install -y --no-install-recommends fluent-bit libpam-pwquality

cat >/etc/fluent-bit/fluent-bit.conf <<EOF
[SERVICE]
    Flush        1
    Daemon       Off
    Log_Level    info
    Parsers_File parsers.conf

[INPUT]
    Name              systemd
    Tag               host.*
    Systemd_Filter    _SYSTEMD_UNIT=ssh.service
    Systemd_Filter    _SYSTEMD_UNIT=containerd.service
    Read_From_Tail    On

[OUTPUT]
    Name    stdout
    Match   *
EOF

cat >/etc/ssh/sshd_config.d/10-smartcito-hardening.conf <<'EOF'
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
X11Forwarding no
AllowTcpForwarding no
ClientAliveInterval 300
ClientAliveCountMax 2
LoginGraceTime 30
MaxAuthTries 3
EOF

cat >/etc/security/pwquality.conf.d/10-smartcito.conf <<'EOF'
minlen = 14
dcredit = -1
ucredit = -1
lcredit = -1
ocredit = -1
EOF

cat >/etc/sysctl.d/99-smartcito-security.conf <<'EOF'
kernel.kptr_restrict = 2
kernel.dmesg_restrict = 1
kernel.randomize_va_space = 2
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
EOF

ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw --force enable

systemctl daemon-reload
systemctl enable node_exporter
systemctl enable fluent-bit
systemctl enable ssh
systemctl restart ssh
sysctl --system

install -d /opt/smartcito/bin
cat >/opt/smartcito/bin/validate_image.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

systemctl is-enabled qemu-guest-agent >/dev/null
systemctl is-enabled containerd >/dev/null
systemctl is-enabled node_exporter >/dev/null
systemctl is-enabled fluent-bit >/dev/null
command -v cloud-init >/dev/null
command -v kubeadm >/dev/null
command -v kubelet >/dev/null
command -v kubectl >/dev/null
command -v node >/dev/null
command -v python3 >/dev/null
command -v java >/dev/null
echo "SmartCito OS validation passed"
EOF
chmod 0755 /opt/smartcito/bin/validate_image.sh