output "network_id" {
  description = "ID of the OpenStack network."
  value       = var.enabled ? openstack_networking_network_v2.network[0].id : null
}

output "subnet_id" {
  description = "ID of the OpenStack subnet."
  value       = var.enabled ? openstack_networking_subnet_v2.subnet[0].id : null
}

output "network_name" {
  description = "Name of the OpenStack network."
  value       = var.network_name
}