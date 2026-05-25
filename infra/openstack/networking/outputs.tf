output "public_network_id" {
  value = openstack_networking_network_v2.public_net.id
}

output "services_network_id" {
  value = openstack_networking_network_v2.services_net.id
}

output "database_network_id" {
  value = openstack_networking_network_v2.database_net.id
}

output "public_security_group_id" {
  value = openstack_networking_secgroup_v2.public_ingress.id
}

output "database_security_group_id" {
  value = openstack_networking_secgroup_v2.database_internal.id
}

output "kubernetes_security_group_id" {
  value = openstack_networking_secgroup_v2.kubernetes_internal.id
}

output "data_platform_security_group_id" {
  value = openstack_networking_secgroup_v2.data_platform_internal.id
}