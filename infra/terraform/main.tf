terraform {
  required_version = ">= 1.6.0"

  backend "local" {
    path = "terraform.tfstate"
  }

  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "~> 2.1"
    }
  }
}

provider "openstack" {
  auth_url    = var.auth_url
  tenant_name = var.project_name
  user_name   = var.username
  password    = var.password
  region      = var.region
}

module "network" {
  source       = "./modules/openstack_network"
  network_name = var.network_name
  subnet_cidr  = var.subnet_cidr
}

module "controller" {
  source          = "./modules/openstack_compute"
  name_prefix     = "controller"
  image_name      = var.image_name
  flavor_name     = var.controller_flavor
  key_pair        = var.key_pair
  network_id      = module.network.network_id
  security_groups = ["default"]
  instance_count  = var.controller_count
}

module "compute" {
  source          = "./modules/openstack_compute"
  name_prefix     = "compute"
  image_name      = var.image_name
  flavor_name     = var.compute_flavor
  key_pair        = var.key_pair
  network_id      = module.network.network_id
  security_groups = ["default"]
  instance_count  = var.compute_count
}

module "storage" {
  source          = "./modules/openstack_compute"
  name_prefix     = "storage"
  image_name      = var.image_name
  flavor_name     = var.storage_flavor
  key_pair        = var.key_pair
  network_id      = module.network.network_id
  security_groups = ["default"]
  instance_count  = var.storage_count
}
