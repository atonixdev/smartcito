<!--
================================================================================
 File: infra/openstack/orca-os/README.md
 Purpose:
   Official implementation guide and build surface for the Orca base OS
   image used by OpenStack virtual machines and Kubernetes nodes.
================================================================================
-->

# Orca OS

Orca OS is the official base image for the Orca platform.

It is the operating system every Orca node should boot from before any
application-specific deployment happens. That includes OpenStack service VMs,
Kubernetes control plane nodes, Kubernetes workers, ingestion nodes, AI/ML
nodes, and simulation or hardware-support nodes.

## Outcome

This build surface standardizes:

- consistent package baselines
- cloud-init and OpenStack boot behavior
- Kubernetes node prerequisites
- runtime dependencies for Python, Node.js, and Java workloads
- observability agents for Prometheus and log shipping
- security hardening for SSH, firewalling, auditing, and kernel posture
- repeatable image versioning and Glance upload flow

## Layout

- `orca-os.pkr.hcl`: Packer build definition for the official image.
- `orca-os-gpu.pkr.hcl`: GPU-capable Orca OS variant for AI nodes.
- `orca-os.auto.pkrvars.hcl.example`: example build variables.
- `orca-os-gpu.auto.pkrvars.hcl.example`: example build variables for the GPU variant.
- `http/user-data`: cloud-init seed used during image baking.
- `scripts/10-base-os.sh`: base OS, OpenStack, and cloud-init packages.
- `scripts/20-runtime-and-k8s.sh`: runtimes plus Kubernetes prerequisites.
- `scripts/25-gpu-runtime.sh`: optional GPU runtime and NVIDIA container toolkit layering.
- `scripts/30-observability-and-hardening.sh`: node exporter, Fluent Bit, SSH, audit, firewall, and sysctl hardening.
- `scripts/90-cleanup.sh`: image cleanup and optimization.
- `scripts/boot_validation_vm.sh`: launches an OpenStack validation VM, waits for SSH, and runs the guest validation helper.
- `scripts/validate_image.sh`: guest-side validation checks after boot.
- `scripts/upload_to_glance.sh`: qcow2 upload helper for OpenStack Glance.

## Recommended Baseline

- Base distribution: Ubuntu 22.04 LTS
- Image role: `orca-os`
- Intended consumers:
  - OpenStack VM instances
  - Kubernetes control-plane nodes
  - Kubernetes worker nodes
  - Orca service hosts
  - ingestion and AI/ML nodes

## Prerequisites

- OpenStack project credentials with permission to create images and build VMs.
- A temporary OpenStack network and security group for the image bake.
- Packer 1.10 or newer.
- Ubuntu 22.04 cloud image already available in Glance, for example `ubuntu-22.04`.
- Access to the public Internet or an internal mirror for apt repositories.

## Build Flow

1. Copy the example variables.
2. Fill in OpenStack credentials, network IDs, image naming, and visibility.
3. Run `packer init` and `packer build`.
4. Boot a VM from the resulting image and run the validation script.
5. Promote the validated image name into Terraform and deployment runbooks.

Example:

```bash
cp infra/openstack/orca-os/orca-os.auto.pkrvars.hcl.example \
  infra/openstack/orca-os/orca-os.auto.pkrvars.hcl

packer init infra/openstack/orca-os/orca-os.pkr.hcl
packer build \
  -var-file=infra/openstack/orca-os/orca-os.auto.pkrvars.hcl \
  infra/openstack/orca-os/orca-os.pkr.hcl
```

## What The Image Includes

### Operating System Layer

- Ubuntu 22.04 LTS cloud image baseline
- cloud-init with OpenStack datasource preference
- UEFI-capable boot packages
- qemu guest tools and VirtIO-friendly virtualization support
- SSH server and basic networking tools

### Orca Runtime Dependencies

- Python 3, pip, venv, build-essential
- Node.js 20 and npm
- OpenJDK 17 runtime
- common AI runtime libraries such as OpenBLAS, image, and GL dependencies
- compression and archive tooling

### Kubernetes Compatibility

- containerd runtime
- kubelet, kubeadm, kubectl
- overlay and `br_netfilter` kernel modules
- systemd and sysctl settings required by kubeadm-based clusters

### OpenStack Compatibility

- cloud-init
- qemu-guest-agent
- UEFI support packages
- metadata and config-drive support

### Monitoring and Logging

- node exporter service
- Fluent Bit service with systemd-journald ingestion
- auditd and rsyslog

### Security Hardening

- root SSH login disabled
- password SSH authentication disabled by default
- UFW default deny incoming, allow outgoing
- audit logging enabled
- password quality requirements enabled
- kernel hardening sysctls applied

## Validation

After building and booting the image on OpenStack, run:

```bash
sudo /opt/orca/bin/validate_image.sh
```

The validation checks:

- cloud-init completion
- qemu guest agent state
- containerd availability
- node exporter and Fluent Bit services
- kubelet binary presence
- firewall and audit services

For a full OpenStack boot-and-validate flow from your operator workstation:

```bash
export OS_AUTH_URL="https://openstack.example.com:5000/v3"
export OS_USERNAME="orca-admin"
export OS_PASSWORD="..."
export OS_PROJECT_NAME="orca"
export OS_USER_DOMAIN_NAME="Default"
export OS_PROJECT_DOMAIN_NAME="Default"
export OS_REGION_NAME="RegionOne"

infra/openstack/orca-os/scripts/boot_validation_vm.sh \
  orca-os-ubuntu-22.04-2026.05 \
  orca-services-net \
  orca-keypair \
  orca-validation \
  ~/.ssh/orca.pem \
  public \
  m1.large \
  ubuntu
```

The helper creates one VM, attaches a floating IP, waits for SSH and cloud-init,
runs `/opt/orca/bin/validate_image.sh`, then deletes the validation VM by
default. Set `KEEP_VALIDATION_VM=true` to retain it for inspection.

## Glance Upload

If you build or export a qcow2 artifact separately, upload it with:

```bash
infra/openstack/orca-os/scripts/upload_to_glance.sh \
  /path/to/orca-os-2026.05.qcow2 \
  orca-os-ubuntu-22.04-2026.05
```

## Promotion Into Terraform

Once validated, set the image in [infra/openstack/terraform.tfvars.example](../terraform.tfvars.example) and real environment tfvars to the promoted Orca OS image name.

This repository also includes an auto-loaded Terraform image override in [infra/openstack/zz-orca-os.auto.tfvars](../zz-orca-os.auto.tfvars) so the promoted image name is selected by default without copying secrets into version control.

Recommended pattern:

```hcl
image_name = "orca-os-ubuntu-22.04-2026.05"
```

## GPU Variant

Use the GPU variant for AI and model-serving nodes that need NVIDIA container
runtime support or driver layering.

Build flow:

```bash
cp infra/openstack/orca-os/orca-os-gpu.auto.pkrvars.hcl.example \
  infra/openstack/orca-os/orca-os-gpu.auto.pkrvars.hcl

packer init infra/openstack/orca-os/orca-os-gpu.pkr.hcl
packer build \
  -var-file=infra/openstack/orca-os/orca-os-gpu.auto.pkrvars.hcl \
  infra/openstack/orca-os/orca-os-gpu.pkr.hcl
```

Recommended GPU image naming pattern:

```hcl
image_name = "orca-os-gpu-ubuntu-22.04-2026.05"
```

The GPU variant installs `nvidia-container-toolkit` and can optionally install
the NVIDIA kernel driver package selected in the Packer variables.

## Operational Guidance

- Treat Orca OS as the default image for the whole platform.
- Version images monthly or per security release.
- Rebuild on kernel, OpenSSL, containerd, Kubernetes, or cloud-init updates.
- Do not hand-configure production VMs after boot; push changes back into this image or cloud-init.

## Team Responsibilities

- Infrastructure: image build, versioning, Glance promotion.
- DevOps: Kubernetes and OpenStack validation, observability verification.
- Backend and data teams: runtime library verification.
- AI/ML: CPU and optional GPU runtime verification.

## Notes

- GPU driver enablement is intentionally optional and should be layered through a specialized variant image if GPU nodes are required.
- This base image is the foundation only. It should not contain Orca service code or environment-specific secrets.