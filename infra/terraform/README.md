# Terraform Infra

Terraform modules for Orca infrastructure provisioning.

This directory contains a simplified OpenStack stack. The segmented, canonical
OpenStack layout lives in `infra/openstack/`.

## Purpose

Provision OpenStack compute instances, networks, and supporting infrastructure.

## Technologies Used

- Terraform
- OpenStack provider

## How To Run

```bash
cp infra/terraform/terraform.tfvars.example infra/terraform/terraform.tfvars
terraform -chdir=infra/terraform init
terraform -chdir=infra/terraform plan
```

## Example Usage

Set real OpenStack credentials, image name, and key pair in
`infra/terraform/terraform.tfvars` or with `OS_*` environment variables, then
apply the modules to provision controller, compute, and storage nodes.

The example values are placeholders and will not work against a real cloud
until they are replaced.
