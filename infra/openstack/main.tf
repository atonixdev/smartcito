terraform {
  required_version = ">= 1.6.0"

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

module "networking" {
  source = "./networking"

  auth_url            = var.auth_url
  project_name        = var.project_name
  username            = var.username
  password            = var.password
  region              = var.region
  external_network_id = var.external_network_id

  public_subnet_cidr   = var.public_subnet_cidr
  services_subnet_cidr = var.services_subnet_cidr
  database_subnet_cidr = var.database_subnet_cidr
  public_gateway_ip    = var.public_gateway_ip
  services_gateway_ip  = var.services_gateway_ip
  database_gateway_ip  = var.database_gateway_ip
  dns_nameservers      = var.dns_nameservers
}

module "compute" {
  source = "./compute"

  auth_url   = var.auth_url
  project_name = var.project_name
  username   = var.username
  password   = var.password
  region     = var.region

  image_name            = var.image_name
  key_pair              = var.key_pair
  public_network_id     = module.networking.public_network_id
  services_network_id   = module.networking.services_network_id
  database_network_id   = module.networking.database_network_id
  public_security_groups   = [module.networking.public_security_group_id]
  internal_security_groups = [module.networking.data_platform_security_group_id]
  database_security_groups = [module.networking.database_security_group_id]
  kubernetes_security_groups = [module.networking.kubernetes_security_group_id]
  data_platform_security_groups = [module.networking.data_platform_security_group_id]

  api_flavor_name      = var.api_flavor_name
  service_flavor_name  = var.service_flavor_name
  database_flavor_name = var.database_flavor_name
  kubernetes_control_plane_flavor_name = var.kubernetes_control_plane_flavor_name
  kubernetes_worker_flavor_name = var.kubernetes_worker_flavor_name
  kafka_broker_flavor_name = var.kafka_broker_flavor_name
  spark_master_flavor_name = var.spark_master_flavor_name
  spark_worker_flavor_name = var.spark_worker_flavor_name
  service_node_count   = var.service_node_count
  database_node_count  = var.database_node_count
  kubernetes_worker_count = var.kubernetes_worker_count
  kafka_broker_count = var.kafka_broker_count
  spark_worker_count = var.spark_worker_count
}

module "storage" {
  source = "./storage"

  auth_url     = var.auth_url
  project_name = var.project_name
  username     = var.username
  password     = var.password
  region       = var.region

  database_volume_size_gb      = var.database_volume_size_gb
  object_storage_volume_size_gb = var.object_storage_volume_size_gb
  logs_volume_size_gb          = var.logs_volume_size_gb
  kafka_log_volume_size_gb     = var.kafka_log_volume_size_gb
  spark_checkpoint_volume_size_gb = var.spark_checkpoint_volume_size_gb
  kafka_broker_count           = var.kafka_broker_count
}

resource "openstack_compute_volume_attach_v2" "database_volume_attachment" {
  instance_id = module.compute.database_node_ids[0]
  volume_id   = module.storage.database_volume_id
}

resource "openstack_compute_volume_attach_v2" "kafka_log_volume_attachments" {
  count       = min(length(module.compute.kafka_broker_ids), length(module.storage.kafka_log_volume_ids))
  instance_id = module.compute.kafka_broker_ids[count.index]
  volume_id   = module.storage.kafka_log_volume_ids[count.index]
}

resource "openstack_compute_volume_attach_v2" "spark_checkpoint_attachment" {
  instance_id = module.compute.spark_master_instance_id
  volume_id   = module.storage.spark_checkpoint_volume_id
}