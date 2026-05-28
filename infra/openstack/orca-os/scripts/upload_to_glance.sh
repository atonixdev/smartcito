#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <qcow2-path> <image-name> [visibility]" >&2
  exit 1
fi

qcow2_path="$1"
image_name="$2"
visibility="${3:-shared}"

if [[ ! -f "$qcow2_path" ]]; then
  echo "qcow2 artifact not found: $qcow2_path" >&2
  exit 1
fi

openstack image create "$image_name" \
  --file "$qcow2_path" \
  --disk-format qcow2 \
  --container-format bare \
  --property orca_image=true \
  --property orca_role=base-os \
  --property os_distro=ubuntu \
  --property os_version=22.04 \
  --property hw_firmware_type=uefi \
  --property kube_compatible=true \
  --property openstack_compatible=true \
  --"$visibility"