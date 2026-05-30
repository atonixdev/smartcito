output "openstack_network" {
  description = "OpenStack network details created by this stack."
  value       = module.platform.openstack_network
}

output "openstack_compute" {
  description = "OpenStack compute groups created by this stack."
  value       = module.platform.openstack_compute
}

output "kubernetes_namespaces" {
  description = "Namespaces managed by this stack."
  value       = module.platform.kubernetes_namespaces
}

output "orca_workloads" {
  description = "ORCA workloads exposed by the Kubernetes module."
  value       = module.platform.orca_workloads
}