locals {
  enabled_openstack_compute = {
    for name, config in var.openstack_compute : name => config
    if var.openstack_enabled && config.enabled
  }

  namespace_set = distinct(concat(var.namespaces, [var.orca_namespace]))
}

module "openstack_network" {
  source = "../modules/openstack-network"

  providers = {
    openstack = openstack
  }

  enabled      = var.openstack_enabled && var.openstack_network.enabled
  network_name = var.openstack_network.network_name
  subnet_name  = var.openstack_network.subnet_name
  subnet_cidr  = var.openstack_network.subnet_cidr
}

module "openstack_compute" {
  for_each = local.enabled_openstack_compute
  source   = "../modules/openstack-compute"

  providers = {
    openstack = openstack
  }

  enabled           = true
  name_prefix       = each.value.name_prefix
  image_name        = each.value.image_name
  flavor_name       = each.value.flavor_name
  key_pair          = each.value.key_pair
  instance_count    = each.value.instance_count
  security_groups   = each.value.security_groups
  metadata          = merge(each.value.metadata, { group = each.key })
  availability_zone = each.value.availability_zone
  user_data         = each.value.user_data
  network_id        = each.value.network_id != "" ? each.value.network_id : module.openstack_network.network_id
}

module "k8s_namespaces" {
  source = "../modules/k8s-namespaces"

  providers = {
    kubernetes = kubernetes
  }

  enabled    = var.kubernetes_enabled
  namespaces = local.namespace_set
}

module "k8s_services" {
  source = "../modules/k8s-services"

  providers = {
    kubernetes = kubernetes
  }

  enabled   = var.kubernetes_enabled
  namespace = var.orca_namespace
  workloads = var.orca_workloads

  depends_on = [module.k8s_namespaces]
}