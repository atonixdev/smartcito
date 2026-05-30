#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <rootfs-dir>" >&2
  exit 1
fi

ROOTFS_DIR="$1"
MANIFEST_FILE="$ROOTFS_DIR/usr/share/orca/rootfs.manifest"

rm -rf "$ROOTFS_DIR"

mkdir -p \
  "$ROOTFS_DIR/bin" \
  "$ROOTFS_DIR/boot" \
  "$ROOTFS_DIR/dev" \
  "$ROOTFS_DIR/etc/orca/ai/models" \
  "$ROOTFS_DIR/etc/orca/ai/runtime" \
  "$ROOTFS_DIR/etc/orca/ai/pipelines" \
  "$ROOTFS_DIR/etc/orca/kernel" \
  "$ROOTFS_DIR/etc/orca/network/interfaces.d" \
  "$ROOTFS_DIR/etc/orca/network/firewall" \
  "$ROOTFS_DIR/etc/orca/network/vpn" \
  "$ROOTFS_DIR/etc/orca/security/policies" \
  "$ROOTFS_DIR/etc/orca/security/apparmor" \
  "$ROOTFS_DIR/etc/orca/security/selinux" \
  "$ROOTFS_DIR/etc/orca/security/keys" \
  "$ROOTFS_DIR/etc/orca/hardware/sensors" \
  "$ROOTFS_DIR/etc/orca/hardware/gpu" \
  "$ROOTFS_DIR/etc/orca/hardware/drivers" \
  "$ROOTFS_DIR/etc/orca/services" \
  "$ROOTFS_DIR/etc/orca/storage/disks" \
  "$ROOTFS_DIR/etc/orca/storage/partitions" \
  "$ROOTFS_DIR/etc/orca/logging/telemetry" \
  "$ROOTFS_DIR/etc/orca/system/init" \
  "$ROOTFS_DIR/etc/orca/system/power" \
  "$ROOTFS_DIR/etc/orca/system/scheduler" \
  "$ROOTFS_DIR/etc/orca/system/watchdog" \
  "$ROOTFS_DIR/etc/orca/updater/channels" \
  "$ROOTFS_DIR/etc/orca/updater/signatures" \
  "$ROOTFS_DIR/etc/systemd" \
  "$ROOTFS_DIR/etc/init.d" \
  "$ROOTFS_DIR/etc/network" \
  "$ROOTFS_DIR/etc/ssh" \
  "$ROOTFS_DIR/home" \
  "$ROOTFS_DIR/lib" \
  "$ROOTFS_DIR/media" \
  "$ROOTFS_DIR/mnt" \
  "$ROOTFS_DIR/opt/orca-ai/engine" \
  "$ROOTFS_DIR/opt/orca-ai/models" \
  "$ROOTFS_DIR/opt/orca-ai/tokenizer" \
  "$ROOTFS_DIR/opt/orca-ai/runtime" \
  "$ROOTFS_DIR/opt/orca-ai/gpu" \
  "$ROOTFS_DIR/opt/orca-ai/config" \
  "$ROOTFS_DIR/opt/orca-net/drivers" \
  "$ROOTFS_DIR/opt/orca-net/protocols" \
  "$ROOTFS_DIR/opt/orca-net/satellite" \
  "$ROOTFS_DIR/opt/orca-net/mesh" \
  "$ROOTFS_DIR/opt/orca-net/config" \
  "$ROOTFS_DIR/proc" \
  "$ROOTFS_DIR/root" \
  "$ROOTFS_DIR/run/orca/pids" \
  "$ROOTFS_DIR/run/orca/sockets" \
  "$ROOTFS_DIR/run/orca/cache" \
  "$ROOTFS_DIR/run/orca/state" \
  "$ROOTFS_DIR/sbin" \
  "$ROOTFS_DIR/srv" \
  "$ROOTFS_DIR/sys" \
  "$ROOTFS_DIR/tmp" \
  "$ROOTFS_DIR/usr/bin" \
  "$ROOTFS_DIR/usr/sbin" \
  "$ROOTFS_DIR/usr/lib/orca/core" \
  "$ROOTFS_DIR/usr/lib/orca/ai" \
  "$ROOTFS_DIR/usr/lib/orca/net" \
  "$ROOTFS_DIR/usr/lib/orca/vision" \
  "$ROOTFS_DIR/usr/lib/orca/sensors" \
  "$ROOTFS_DIR/usr/lib/orca/updater" \
  "$ROOTFS_DIR/usr/lib/orca/cli" \
  "$ROOTFS_DIR/usr/lib" \
  "$ROOTFS_DIR/usr/share/orca" \
  "$ROOTFS_DIR/usr/share" \
  "$ROOTFS_DIR/usr/local" \
  "$ROOTFS_DIR/var/log" \
  "$ROOTFS_DIR/var/cache" \
  "$ROOTFS_DIR/var/lib" \
  "$ROOTFS_DIR/var/run" \
  "$ROOTFS_DIR/var/spool" \
  "$ROOTFS_DIR/var/orca/logs" \
  "$ROOTFS_DIR/var/orca/db" \
  "$ROOTFS_DIR/var/orca/cache" \
  "$ROOTFS_DIR/var/orca/updates"

cat > "$ROOTFS_DIR/etc/fstab" <<'EOF'
# ORCA OS filesystem table
proc  /proc proc  defaults 0 0
sysfs /sys  sysfs defaults 0 0
tmpfs /run  tmpfs defaults 0 0
tmpfs /tmp  tmpfs defaults 0 0
EOF

cat > "$ROOTFS_DIR/etc/hostname" <<'EOF'
orca-os
EOF

cat > "$ROOTFS_DIR/etc/hosts" <<'EOF'
127.0.0.1 localhost
127.0.1.1 orca-os
EOF

cat > "$ROOTFS_DIR/etc/orca/ai/config.yaml" <<'EOF'
engine:
  models_dir: /opt/orca-ai/models
  runtime_dir: /opt/orca-ai/runtime
  tokenizer_dir: /opt/orca-ai/tokenizer
  gpu_runtime_dir: /opt/orca-ai/gpu
pipelines:
  config_dir: /etc/orca/ai/pipelines
  default_pipeline: edge-triage
runtime:
  provider: local
  preload_models: false
  health_socket: /run/orca/sockets/orca-ai.sock
telemetry:
  metrics_dir: /var/orca/logs/ai
EOF

cat > "$ROOTFS_DIR/etc/orca/kernel/sysctl.conf" <<'EOF'
# ORCA kernel sysctl defaults
kernel.watchdog = 1
vm.swappiness = 10
EOF

cat > "$ROOTFS_DIR/etc/orca/kernel/modules.conf" <<'EOF'
# ORCA kernel module policy
load=orca_net
load=orca_vision
load=orca_security
EOF

cat > "$ROOTFS_DIR/etc/orca/kernel/scheduler.conf" <<'EOF'
policy=balanced
quantum_ms=10
EOF

cat > "$ROOTFS_DIR/etc/orca/network/orca-net.conf" <<'EOF'
network:
  mode: hybrid
  mesh_enabled: true
  satellite_enabled: false
  vpn_enabled: true
  control_socket: /run/orca/sockets/orca-net.sock
uplinks:
  preferred:
    - wifi
    - lte
    - mesh
  failover:
    - satellite
firewall:
  policy_dir: /etc/orca/network/firewall
  default_policy: deny-ingress-allow-egress
EOF

cat > "$ROOTFS_DIR/etc/orca/network/interfaces.d/edge0.conf" <<'EOF'
[interface]
name=edge0
dhcp=true
role=primary-uplink
metric=100
EOF

cat > "$ROOTFS_DIR/etc/orca/network/firewall/default.rules" <<'EOF'
# ORCA-Net default firewall rules
default_input=deny
default_output=allow
allow_service=orca-net
allow_service=orca-security
EOF

cat > "$ROOTFS_DIR/etc/orca/network/vpn/default.conf" <<'EOF'
provider=wireguard
peer_mode=hub-and-spoke
key_dir=/etc/orca/security/keys
EOF

cat > "$ROOTFS_DIR/etc/orca/security/policies/platform-policy.yaml" <<'EOF'
policy:
  secure_boot_required: true
  signed_updates_only: true
  root_login: disabled
  telemetry_redaction: strict
EOF

cat > "$ROOTFS_DIR/etc/orca/security/apparmor/orca-core.profile" <<'EOF'
# ORCA Core AppArmor placeholder profile
/usr/lib/orca/core/orca-core {
  capability net_bind_service,
  /var/orca/** rw,
  /run/orca/** rw,
}
EOF

cat > "$ROOTFS_DIR/etc/orca/security/selinux/orca.te" <<'EOF'
# ORCA SELinux placeholder policy
policy_module(orca, 1.0)
EOF

cat > "$ROOTFS_DIR/etc/orca/security/keys/README" <<'EOF'
Store ORCA platform keys and trust anchors here.
EOF

cat > "$ROOTFS_DIR/etc/orca/hardware/hal.conf" <<'EOF'
hardware:
  discover_sensors: true
  hotplug_usb: true
  gpu_runtime: /opt/orca-ai/gpu
  sensor_inventory: /etc/orca/hardware/sensors
drivers:
  config_dir: /etc/orca/hardware/drivers
EOF

cat > "$ROOTFS_DIR/etc/orca/hardware/drivers/storage.conf" <<'EOF'
driver=orca-storage
mode=nvme-preferred
state_dir=/var/orca/db/storage
EOF

cat > "$ROOTFS_DIR/etc/orca/storage/fs.conf" <<'EOF'
storage:
  rootfs_mode: read-only
  state_overlay: /var/orca
  update_staging: /var/orca/updates/staging
  manifest: /usr/share/orca/rootfs.manifest
EOF

cat > "$ROOTFS_DIR/etc/orca/storage/disks/default.disk" <<'EOF'
name=system-disk
role=rootfs
filesystem=ext4
EOF

cat > "$ROOTFS_DIR/etc/orca/storage/partitions/layout.conf" <<'EOF'
boot=/boot
root=/
state=/var/orca
EOF

cat > "$ROOTFS_DIR/etc/orca/logging/orca.log.conf" <<'EOF'
logging:
  level: info
  output: /var/orca/logs/orca.log
  journal_forward: true
  telemetry_dir: /etc/orca/logging/telemetry
EOF

cat > "$ROOTFS_DIR/etc/orca/logging/telemetry/pipeline.conf" <<'EOF'
exporter=local-file
path=/var/orca/logs/telemetry.jsonl
redaction=enabled
EOF

cat > "$ROOTFS_DIR/etc/orca/system/init/profile.conf" <<'EOF'
default_target=orca-core.target
retry_deferred_services=true
service_graph_retries=2
enabled_services=net,vision,core,security,update
EOF

cat > "$ROOTFS_DIR/etc/orca/system/power/profile.conf" <<'EOF'
governor=balanced
thermal_protection=enabled
EOF

cat > "$ROOTFS_DIR/etc/orca/system/scheduler/profile.conf" <<'EOF'
service_graph_retries=4
latency_budget_ms=25
EOF

cat > "$ROOTFS_DIR/etc/orca/system/watchdog/profile.conf" <<'EOF'
enabled=true
interval_seconds=15
EOF

cat > "$ROOTFS_DIR/etc/orca/updater/ota.conf" <<'EOF'
updater:
  channel: stable
  signatures_dir: /etc/orca/updater/signatures
  channels_dir: /etc/orca/updater/channels
  staging_dir: /var/orca/updates/staging
  rollout_policy: canary
EOF

cat > "$ROOTFS_DIR/etc/orca/updater/channels/stable.conf" <<'EOF'
name=stable
auto_rollout=true
verification=signed
EOF

cat > "$ROOTFS_DIR/etc/orca/updater/signatures/README" <<'EOF'
Store release signatures and trusted update metadata here.
EOF

cat > "$ROOTFS_DIR/etc/network/interfaces" <<'EOF'
auto lo
iface lo inet loopback

auto edge0
iface edge0 inet dhcp
EOF

cat > "$ROOTFS_DIR/etc/ssh/sshd_config" <<'EOF'
Port 22
PermitRootLogin no
PasswordAuthentication no
ChallengeResponseAuthentication no
UsePAM yes
Subsystem sftp /usr/lib/openssh/sftp-server
EOF

cat > "$ROOTFS_DIR/etc/orca/services/orca-core.service" <<'EOF'
[Unit]
Description=ORCA Core Service
After=orca-net.service orca-ai.service

[Service]
ExecStart=/usr/lib/orca/core/orca-core
EOF

cat > "$ROOTFS_DIR/etc/orca/services/orca-ai.service" <<'EOF'
[Unit]
Description=ORCA AI Service
After=orca-net.service

[Service]
ExecStart=/usr/lib/orca/ai/orca-ai
EOF

cat > "$ROOTFS_DIR/etc/orca/services/orca-net.service" <<'EOF'
[Unit]
Description=ORCA Net Service

[Service]
ExecStart=/usr/lib/orca/net/orca-net
EOF

cat > "$ROOTFS_DIR/etc/orca/services/orca-update.service" <<'EOF'
[Unit]
Description=ORCA Update Service
After=orca-net.service
Requires=orca-net.service

[Service]
ExecStart=/usr/lib/orca/updater/orca-update
EOF

cat > "$ROOTFS_DIR/init" <<'EOF'
#!/bin/sh
set -eu
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t tmpfs tmpfs /run
mkdir -p /run/orca/pids /run/orca/sockets /run/orca/cache /run/orca/state /var/orca/logs
echo "ORCA initramfs bootstrap"
exec /usr/lib/orca/orca-supervise boot
EOF
chmod +x "$ROOTFS_DIR/init"

cat > "$ROOTFS_DIR/usr/lib/orca/orca-supervise" <<'EOF'
#!/bin/sh
set -eu

STATE_DIR=/run/orca/state
PID_DIR=/run/orca/pids
SOCKET_DIR=/run/orca/sockets
CACHE_DIR=/run/orca/cache
LOG_DIR=/var/orca/logs
HEARTBEAT_INTERVAL=30
SERVICES="orca-net orca-ai orca-core orca-update"

mkdir -p "$STATE_DIR" "$PID_DIR" "$SOCKET_DIR" "$CACHE_DIR" "$LOG_DIR"

service_log() {
  service_name="$1"
  shift
  printf '%s %s\n' "[$service_name]" "$*"
}

start_service() {
  service_name="$1"
  launcher="$2"
  log_file="$LOG_DIR/$service_name.log"

  service_log supervisor "starting $service_name via $launcher" >> "$LOG_DIR/bootstrap.log"
  "$launcher" >> "$log_file" 2>&1 &
  pid="$!"
  echo "$pid" > "$PID_DIR/$service_name.pid"
  echo "starting" > "$STATE_DIR/$service_name.state"
}

run_service() {
  service_name="$1"
  profile_path="$2"
  detail_line_one="$3"
  detail_line_two="$4"

  echo "running" > "$STATE_DIR/$service_name.state"
  service_log "$service_name" "profile=$profile_path"
  service_log "$service_name" "$detail_line_one"
  service_log "$service_name" "$detail_line_two"

  while :; do
    date -u +%Y-%m-%dT%H:%M:%SZ > "$STATE_DIR/$service_name.heartbeat"
    sleep "$HEARTBEAT_INTERVAL"
  done
}

monitor_services() {
  while :; do
    for service_name in $SERVICES; do
      pid_file="$PID_DIR/$service_name.pid"
      state_file="$STATE_DIR/$service_name.state"

      if [[ ! -f "$pid_file" ]]; then
        continue
      fi

      pid="$(cat "$pid_file")"
      if kill -0 "$pid" 2>/dev/null; then
        echo "running" > "$state_file"
      else
        echo "failed" > "$state_file"
        service_log supervisor "$service_name exited; restarting" >> "$LOG_DIR/bootstrap.log"
        rm -f "$pid_file"
        case "$service_name" in
          orca-net)
            start_service "$service_name" /usr/lib/orca/net/orca-net
            ;;
          orca-ai)
            start_service "$service_name" /usr/lib/orca/ai/orca-ai
            ;;
          orca-core)
            start_service "$service_name" /usr/lib/orca/core/orca-core
            ;;
          orca-update)
            start_service "$service_name" /usr/lib/orca/updater/orca-update
            ;;
        esac
      fi
    done

    sleep 5
  done
}

print_status() {
  for service_name in $SERVICES; do
    state_file="$STATE_DIR/$service_name.state"
    heartbeat_file="$STATE_DIR/$service_name.heartbeat"
    state="unknown"
    heartbeat="none"
    if [[ -f "$state_file" ]]; then
      state="$(cat "$state_file")"
    fi
    if [[ -f "$heartbeat_file" ]]; then
      heartbeat="$(cat "$heartbeat_file")"
    fi
    printf '%s state=%s heartbeat=%s\n' "$service_name" "$state" "$heartbeat"
  done
}

command="${1:-boot}"
case "$command" in
  boot)
    : > "$LOG_DIR/bootstrap.log"
    service_log supervisor "boot sequence started" >> "$LOG_DIR/bootstrap.log"
    start_service orca-net /usr/lib/orca/net/orca-net
    start_service orca-ai /usr/lib/orca/ai/orca-ai
    start_service orca-core /usr/lib/orca/core/orca-core
    start_service orca-update /usr/lib/orca/updater/orca-update
    monitor_services
    ;;
  run-service)
    run_service "$2" "$3" "$4" "$5"
    ;;
  status)
    print_status
    ;;
  *)
    echo "usage: orca-supervise [boot|run-service|status]" >&2
    exit 1
    ;;
esac
EOF
chmod +x "$ROOTFS_DIR/usr/lib/orca/orca-supervise"

cat > "$ROOTFS_DIR/usr/lib/orca/cli/orca" <<'EOF'
#!/bin/sh
set -eu

COMMAND="${1:-status}"
case "$COMMAND" in
  status)
    echo "ORCA CLI"
    echo "hostname=$(cat /etc/hostname 2>/dev/null || echo unknown)"
    echo "config=/etc/orca"
    echo "state=/run/orca"
    echo "data=/var/orca"
    /usr/lib/orca/orca-supervise status
    ;;
  manifest)
    cat /usr/share/orca/rootfs.manifest
    ;;
  *)
    echo "usage: orca [status|manifest]" >&2
    exit 1
    ;;
esac
EOF
chmod +x "$ROOTFS_DIR/usr/lib/orca/cli/orca"

cat > "$ROOTFS_DIR/usr/lib/orca/core/orca-core" <<'EOF'
#!/bin/sh
set -eu

mkdir -p /run/orca/state /var/orca/logs
exec /usr/lib/orca/orca-supervise run-service \
  orca-core \
  /etc/orca/system/init/profile.conf \
  "scheduler=/etc/orca/system/scheduler/profile.conf" \
  "runtime=ready"
EOF
chmod +x "$ROOTFS_DIR/usr/lib/orca/core/orca-core"

cat > "$ROOTFS_DIR/usr/lib/orca/ai/orca-ai" <<'EOF'
#!/bin/sh
set -eu

mkdir -p /run/orca/sockets /var/orca/logs/ai
exec /usr/lib/orca/orca-supervise run-service \
  orca-ai \
  /etc/orca/ai/config.yaml \
  "runtime=/opt/orca-ai/runtime" \
  "models=/opt/orca-ai/models"
EOF
chmod +x "$ROOTFS_DIR/usr/lib/orca/ai/orca-ai"

cat > "$ROOTFS_DIR/usr/lib/orca/net/orca-net" <<'EOF'
#!/bin/sh
set -eu

mkdir -p /run/orca/sockets /var/orca/logs
exec /usr/lib/orca/orca-supervise run-service \
  orca-net \
  /etc/orca/network/orca-net.conf \
  "firewall=/etc/orca/network/firewall/default.rules" \
  "vpn=/etc/orca/network/vpn/default.conf"
EOF
chmod +x "$ROOTFS_DIR/usr/lib/orca/net/orca-net"

cat > "$ROOTFS_DIR/usr/lib/orca/updater/orca-update" <<'EOF'
#!/bin/sh
set -eu

mkdir -p /var/orca/updates/staging /run/orca/state
exec /usr/lib/orca/orca-supervise run-service \
  orca-update \
  /etc/orca/updater/ota.conf \
  "manifest=/usr/share/orca/rootfs.manifest" \
  "staging=/var/orca/updates/staging"
EOF
chmod +x "$ROOTFS_DIR/usr/lib/orca/updater/orca-update"

cat > "$ROOTFS_DIR/opt/orca-ai/config/runtime.conf" <<'EOF'
runtime=local
models_dir=/opt/orca-ai/models
tokenizer_dir=/opt/orca-ai/tokenizer
engine_dir=/opt/orca-ai/engine
EOF

cat > "$ROOTFS_DIR/opt/orca-net/config/orca-net.conf" <<'EOF'
transport=wifi,lte,mesh
protocol=orca-net
EOF

cat > "$ROOTFS_DIR/README.rootfs" <<'EOF'
This image contains the ORCA OS root filesystem skeleton.
Configuration lives under /etc/orca.
Runtime state lives under /run/orca.
Persistent ORCA data lives under /var/orca.
EOF

{
  echo "# ORCA OS rootfs manifest"
  echo "# generated by scripts/generate-rootfs.sh"
  (cd "$ROOTFS_DIR" && find . -mindepth 1 | LC_ALL=C sort)
} > "$MANIFEST_FILE"