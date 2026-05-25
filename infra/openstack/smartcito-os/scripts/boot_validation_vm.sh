#!/usr/bin/env bash
set -euo pipefail

image_name="${1:-}"
network_id="${2:-}"
key_pair="${3:-}"
security_group="${4:-}"
ssh_private_key="${5:-}"
floating_network="${6:-}"
flavor="${7:-m1.large}"
ssh_username="${8:-ubuntu}"
server_name="${9:-smartcito-os-validation-$(date +%Y%m%d%H%M%S)}"

if [[ -z "$image_name" || -z "$network_id" || -z "$key_pair" || -z "$security_group" || -z "$ssh_private_key" || -z "$floating_network" ]]; then
  echo "usage: $0 <image-name> <network-id> <key-pair> <security-group> <ssh-private-key> <floating-network> [flavor] [ssh-user] [server-name]" >&2
  exit 1
fi

if ! command -v openstack >/dev/null 2>&1; then
  echo "openstack CLI is required" >&2
  exit 1
fi

if ! command -v ssh >/dev/null 2>&1; then
  echo "ssh is required" >&2
  exit 1
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
server_id=""
floating_ip=""
keep_vm="${KEEP_VALIDATION_VM:-false}"
keep_floating_ip="${KEEP_VALIDATION_FLOATING_IP:-false}"

cleanup() {
  if [[ -n "$server_id" && "$keep_vm" != "true" ]]; then
    openstack server delete "$server_id" >/dev/null 2>&1 || true
  fi

  if [[ -n "$floating_ip" && "$keep_floating_ip" != "true" ]]; then
    openstack floating ip delete "$floating_ip" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT

server_id="$(openstack server create \
  --image "$image_name" \
  --flavor "$flavor" \
  --network "$network_id" \
  --security-group "$security_group" \
  --key-name "$key_pair" \
  --property smartcito_validation=true \
  --property smartcito_role=validation \
  "$server_name" \
  -f value -c id)"

openstack server wait --active "$server_id"

floating_ip="$(openstack floating ip create "$floating_network" -f value -c floating_ip_address)"
openstack server add floating ip "$server_id" "$floating_ip"

ssh_options=(
  -i "$ssh_private_key"
  -o StrictHostKeyChecking=no
  -o UserKnownHostsFile=/dev/null
  -o ConnectTimeout=10
)

for attempt in $(seq 1 30); do
  if ssh "${ssh_options[@]}" "$ssh_username@$floating_ip" true >/dev/null 2>&1; then
    break
  fi

  if [[ "$attempt" == "30" ]]; then
    echo "validation instance did not become reachable over SSH" >&2
    exit 1
  fi
done

ssh "${ssh_options[@]}" "$ssh_username@$floating_ip" sudo cloud-init status --wait >/dev/null
"$script_dir/validate_image.sh" "$ssh_username@$floating_ip" "${ssh_options[@]}"

if [[ "$keep_vm" == "true" ]]; then
  echo "validation VM retained: $server_name ($server_id) at $floating_ip"
fi