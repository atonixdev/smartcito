# Puppet Infra

Puppet manifests for SmartCito node configuration.

## Purpose

Apply consistent configuration to controller, compute, and storage nodes.

## Technologies Used

- Puppet DSL
- Linux package and service management

## How To Run

```bash
puppet apply infra/puppet/manifests/site.pp
```

## Example Usage

Use the role manifests under `infra/puppet/manifests/roles/` for controller,
compute, and storage nodes.
