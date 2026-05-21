# Terraform Infra

Terraform modules for SmartCito infrastructure provisioning.

## Purpose

Provision OpenStack compute instances, networks, and supporting infrastructure.

## Technologies Used

- Terraform
- OpenStack provider

## How To Run

```bash
terraform -chdir=infra/terraform init
terraform -chdir=infra/terraform plan
```

## Example Usage

Set OpenStack credentials in variables or environment and apply the modules to
provision controller, compute, and storage nodes.
