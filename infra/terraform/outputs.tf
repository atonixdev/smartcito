output "network_id" {
  value = module.network.network_id
}

output "controller_ids" {
  value = module.controller.instance_ids
}

output "compute_ids" {
  value = module.compute.instance_ids
}

output "storage_ids" {
  value = module.storage.instance_ids
}
