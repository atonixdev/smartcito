resource "openstack_networking_network_v2" "network" {
  name = var.network_name
}

resource "openstack_networking_subnet_v2" "subnet" {
  name       = "${var.network_name}-subnet"
  network_id = openstack_networking_network_v2.network.id
  cidr       = var.subnet_cidr
  ip_version = 4
}
