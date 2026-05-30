terraform {
  required_providers {
    openstack = {
      source = "terraform-provider-openstack/openstack"
    }
  }
}

resource "openstack_networking_network_v2" "network" {
  count = var.enabled ? 1 : 0
  name  = var.network_name
}

resource "openstack_networking_subnet_v2" "subnet" {
  count      = var.enabled ? 1 : 0
  name       = var.subnet_name
  network_id = openstack_networking_network_v2.network[0].id
  cidr       = var.subnet_cidr
  ip_version = 4
}