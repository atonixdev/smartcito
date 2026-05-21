resource "openstack_compute_instance_v2" "instance" {
  count       = var.instance_count
  name        = "${var.name_prefix}-${count.index + 1}"
  image_name  = var.image_name
  flavor_name = var.flavor_name
  key_pair    = var.key_pair

  security_groups = var.security_groups

  network {
    uuid = var.network_id
  }
}
