module "platform" {
  source = "./providers"

  openstack_enabled             = var.openstack_enabled
  openstack_cloud               = var.openstack_cloud
  openstack_auth_url            = var.openstack_auth_url
  openstack_region              = var.openstack_region
  openstack_project_name        = var.openstack_project_name
  openstack_username            = var.openstack_username
  openstack_password            = var.openstack_password
  openstack_user_domain_name    = var.openstack_user_domain_name
  openstack_project_domain_name = var.openstack_project_domain_name
  openstack_network             = var.openstack_network
  openstack_compute             = var.openstack_compute

  kubernetes_enabled                = var.kubernetes_enabled
  kubeconfig_path                   = var.kubeconfig_path
  kubeconfig_context                = var.kubeconfig_context
  kubernetes_host                   = var.kubernetes_host
  kubernetes_token                  = var.kubernetes_token
  kubernetes_cluster_ca_certificate = var.kubernetes_cluster_ca_certificate
  namespaces                        = var.namespaces
  orca_namespace                    = var.orca_namespace
  orca_workloads                    = var.orca_workloads
}