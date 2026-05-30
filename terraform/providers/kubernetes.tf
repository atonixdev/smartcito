provider "kubernetes" {
  config_path    = var.kubeconfig_path != "" ? pathexpand(var.kubeconfig_path) : null
  config_context = var.kubeconfig_context != "" ? var.kubeconfig_context : null

  host                   = var.kubernetes_host != "" ? var.kubernetes_host : null
  token                  = var.kubernetes_token != "" ? var.kubernetes_token : null
  cluster_ca_certificate = var.kubernetes_cluster_ca_certificate != "" ? base64decode(var.kubernetes_cluster_ca_certificate) : null
}