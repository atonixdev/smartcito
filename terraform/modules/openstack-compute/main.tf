terraform {
  required_providers {
    openstack = {
      source = "terraform-provider-openstack/openstack"
    }
  }
}

resource "openstack_compute_instance_v2" "instance" {
  count = var.enabled ? var.instance_count : 0

  name              = "${var.name_prefix}-${count.index + 1}"
  image_name        = var.image_name
  flavor_name       = var.flavor_name
  key_pair          = var.key_pair != "" ? var.key_pair : null
  security_groups   = var.security_groups
  metadata          = var.metadata
  availability_zone = var.availability_zone != "" ? var.availability_zone : null
  user_data         = var.user_data != "" ? var.user_data : null

  dynamic "network" {
    for_each = var.network_id != "" ? [var.network_id] : []
    content {
      uuid = network.value
    }
  }
}