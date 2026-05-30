variable "openstack_enabled" {
  type = bool
}

variable "openstack_cloud" {
  type = string
}

variable "openstack_auth_url" {
  type      = string
  sensitive = true
}

variable "openstack_region" {
  type = string
}

variable "openstack_project_name" {
  type = string
}

variable "openstack_username" {
  type = string
}

variable "openstack_password" {
  type      = string
  sensitive = true
}

variable "openstack_user_domain_name" {
  type = string
}

variable "openstack_project_domain_name" {
  type = string
}

variable "openstack_network" {
  type = object({
    enabled      = bool
    network_name = string
    subnet_name  = string
    subnet_cidr  = string
  })
}

variable "openstack_compute" {
  type = map(object({
    enabled           = bool
    name_prefix       = string
    image_name        = string
    flavor_name       = string
    key_pair          = string
    instance_count    = number
    security_groups   = list(string)
    metadata          = map(string)
    availability_zone = string
    user_data         = string
    network_id        = string
  }))
}

variable "kubernetes_enabled" {
  type = bool
}

variable "kubeconfig_path" {
  type = string
}

variable "kubeconfig_context" {
  type = string
}

variable "kubernetes_host" {
  type = string
}

variable "kubernetes_token" {
  type      = string
  sensitive = true
}

variable "kubernetes_cluster_ca_certificate" {
  type      = string
  sensitive = true
}

variable "namespaces" {
  type = list(string)
}

variable "orca_namespace" {
  type = string
}

variable "orca_workloads" {
  type = map(object({
    model_name     = string
    image          = string
    replicas       = number
    service_port   = number
    container_port = number
    service_type   = string
    env            = map(string)
    labels         = map(string)
  }))
}