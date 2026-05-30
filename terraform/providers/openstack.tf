terraform {
  required_version = ">= 1.5.0"

  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "~> 2.1"
    }

    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.31"
    }
  }
}

provider "openstack" {
  # The provider requires either auth_url or cloud at configuration time.
  # Use a placeholder auth_url only when OpenStack is disabled so init/plan can
  # proceed without real credentials or a live OpenStack endpoint.
  cloud               = var.openstack_cloud != "" ? var.openstack_cloud : null
  auth_url            = var.openstack_auth_url != "" ? var.openstack_auth_url : (var.openstack_enabled ? null : "http://127.0.0.1:5000/v3")
  region              = var.openstack_region != "" ? var.openstack_region : null
  tenant_name         = var.openstack_project_name != "" ? var.openstack_project_name : null
  user_name           = var.openstack_username != "" ? var.openstack_username : null
  password            = var.openstack_password != "" ? var.openstack_password : null
  user_domain_name    = var.openstack_user_domain_name != "" ? var.openstack_user_domain_name : null
  project_domain_name = var.openstack_project_domain_name != "" ? var.openstack_project_domain_name : null
}