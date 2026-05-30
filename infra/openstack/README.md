<!--
================================================================================
 File: infra/openstack/README.md
 Purpose:
   Index for Orca OpenStack infrastructure definitions.
================================================================================
-->

# Orca OpenStack Infrastructure

This folder contains the OpenStack-specific infrastructure layer for running
Orca on virtual machines that host Kubernetes, Kafka, Spark, and the
supporting service tier.

The root Terraform module in this directory composes the child modules under
`networking/`, `compute/`, and `storage/` into one apply flow.

## Layout

- `networking/` defines `orca-public-net`, `orca-services-net`, and
  `orca-database-net`, plus router and security groups for public,
  Kubernetes, data-platform, and database traffic.
- `compute/` defines API gateway, service nodes, Kubernetes control-plane and
  worker nodes, Kafka brokers, Spark master/workers, and database nodes.
- `storage/` defines persistent volumes for databases, Kafka logs, Spark
  checkpoints, object storage, and logs.
- `orca-os/` defines the official Orca base image build surface for
  OpenStack and Kubernetes nodes.

## Orca OS

Use the official Orca OS image as the `image_name` for compute nodes.
The build instructions, Packer template, validation helper, and Glance upload
workflow live in [infra/openstack/orca-os/README.md](orca-os/README.md).
The promoted default image is auto-loaded from [infra/openstack/zz-orca-os.auto.tfvars](zz-orca-os.auto.tfvars).

## Apply Flow

Terraform can authenticate to OpenStack in either of these ways:

- Preferred: use a named profile from `clouds.yaml` with `cloud_name`.
- Legacy: set `auth_url`, `project_name` or `project_id`, `username`, `password`, and optional `user_domain_name` directly in `terraform.tfvars`.

```bash
cp infra/openstack/terraform.tfvars.example infra/openstack/terraform.tfvars
export OS_CLIENT_CONFIG_FILE="$HOME/.config/openstack/clouds.yaml"
terraform -chdir=infra/openstack init
terraform -chdir=infra/openstack plan
terraform -chdir=infra/openstack apply
```

If you want Terraform to consume the same `.env` contract used by the rest of
the repo, load it first:

```bash
bash infra/openstack/export-openstack-env.sh .env terraform -chdir=infra/openstack plan
bash infra/openstack/export-openstack-env.sh .env terraform -chdir=infra/openstack apply
```

Example `clouds.yaml` profile for this stack:

```yaml
clouds:
  openstack:
    auth:
      auth_url: http://172.27.112.36/identity
      username: admin
      password: YOUR_PASSWORD
      project_id: b4e15aaf3bcd41c69934f585febaa845
      project_name: demo
      user_domain_name: Default
    region_name: RegionOne
    interface: public
    identity_api_version: 3
```

Then point Terraform at that profile in `infra/openstack/terraform.tfvars`:

```hcl
cloud_name          = "openstack"
region              = "RegionOne"
external_network_id = "public-network-id"
image_name          = "orca-os-ubuntu-22.04-2026.05"
key_pair            = "orca-keypair"
```

If Keystone requires a versioned endpoint in your environment, prefer
`http://172.27.112.36/identity/v3` for `auth_url` in `clouds.yaml`.

Recommended image setting after promotion:

```hcl
image_name = "orca-os-ubuntu-22.04-2026.05"
```