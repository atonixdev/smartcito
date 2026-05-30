output "instance_ids" {
  description = "IDs of the created instances."
  value       = openstack_compute_instance_v2.instance[*].id
}

output "instance_names" {
  description = "Names of the created instances."
  value       = openstack_compute_instance_v2.instance[*].name
}