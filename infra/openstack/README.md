<!--
================================================================================
 File: infra/openstack/README.md
 Purpose:
   Index for SmartCito OpenStack infrastructure definitions.
================================================================================
-->

# SmartCito OpenStack Infrastructure

This folder contains the OpenStack-specific infrastructure layer for running
SmartCito on virtual machines that host Kubernetes, Kafka, Spark, and the
supporting service tier.

The root Terraform module in this directory composes the child modules under
`networking/`, `compute/`, and `storage/` into one apply flow.

## Layout

- `networking/` defines `smartcito-public-net`, `smartcito-services-net`, and
  `smartcito-database-net`, plus router and security groups for public,
  Kubernetes, data-platform, and database traffic.
- `compute/` defines API gateway, service nodes, Kubernetes control-plane and
  worker nodes, Kafka brokers, Spark master/workers, and database nodes.
- `storage/` defines persistent volumes for databases, Kafka logs, Spark
  checkpoints, object storage, and logs.
- `smartcito-os/` defines the official SmartCito base image build surface for
  OpenStack and Kubernetes nodes.

## SmartCito OS

Use the official SmartCito OS image as the `image_name` for compute nodes.
The build instructions, Packer template, validation helper, and Glance upload
workflow live in [infra/openstack/smartcito-os/README.md](/home/atonixdev/smartcito/infra/openstack/smartcito-os/README.md).
The promoted default image is auto-loaded from [infra/openstack/zz-smartcito-os.auto.tfvars](/home/atonixdev/smartcito/infra/openstack/zz-smartcito-os.auto.tfvars).

## Apply Flow

```bash
cp infra/openstack/terraform.tfvars.example infra/openstack/terraform.tfvars
terraform -chdir=infra/openstack init
terraform -chdir=infra/openstack plan
terraform -chdir=infra/openstack apply
```

Recommended image setting after promotion:

```hcl
image_name = "smartcito-os-ubuntu-22.04-2026.05"
```