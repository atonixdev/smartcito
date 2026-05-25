packer {
  required_version = ">= 1.10.0"

  required_plugins {
    openstack = {
      source  = "github.com/hashicorp/openstack"
      version = ">= 1.1.2"
    }
  }
}

variable "auth_url" {
  type = string
}

variable "project_name" {
  type = string
}

variable "username" {
  type = string
}

variable "password" {
  type      = string
  sensitive = true
}

variable "region" {
  type    = string
  default = "RegionOne"
}

variable "source_image_name" {
  type    = string
  default = "ubuntu-22.04"
}

variable "image_name" {
  type    = string
  default = "smartcito-os-ubuntu-22.04"
}

variable "image_visibility" {
  type    = string
  default = "private"
}

variable "build_flavor" {
  type    = string
  default = "m1.large"
}

variable "build_network_id" {
  type = string
}

variable "build_security_group" {
  type = string
}

variable "ssh_username" {
  type    = string
  default = "ubuntu"
}

variable "use_floating_ip" {
  type    = bool
  default = true
}

variable "node_exporter_version" {
  type    = string
  default = "1.8.2"
}

variable "fluent_bit_version" {
  type    = string
  default = "3.1.9"
}

variable "kubernetes_version" {
  type    = string
  default = "1.30"
}

source "openstack" "smartcito_os" {
  auth_url          = var.auth_url
  tenant_name       = var.project_name
  user_name         = var.username
  password          = var.password
  region            = var.region
  source_image_name = var.source_image_name
  image_name        = var.image_name
  image_visibility  = var.image_visibility
  flavor            = var.build_flavor
  ssh_username      = var.ssh_username
  use_floating_ip   = var.use_floating_ip
  networks          = [var.build_network_id]
  security_groups   = [var.build_security_group]
  user_data_file    = "${path.root}/http/user-data"

  metadata = {
    smartcito_image      = "true"
    smartcito_role       = "base-os"
    smartcito_os         = "ubuntu-22.04"
    kubernetes_ready     = "true"
    openstack_ready      = "true"
    monitoring_embedded  = "true"
    hardened_by_default  = "true"
  }
}

build {
  name    = "smartcito-os"
  sources = ["source.openstack.smartcito_os"]

  provisioner "shell" {
    environment_vars = [
      "DEBIAN_FRONTEND=noninteractive",
      "NODE_EXPORTER_VERSION=${var.node_exporter_version}",
      "FLUENT_BIT_VERSION=${var.fluent_bit_version}",
      "KUBERNETES_VERSION=${var.kubernetes_version}",
    ]
    scripts = [
      "${path.root}/scripts/10-base-os.sh",
      "${path.root}/scripts/20-runtime-and-k8s.sh",
      "${path.root}/scripts/30-observability-and-hardening.sh",
      "${path.root}/scripts/90-cleanup.sh",
    ]
  }

  post-processor "manifest" {
    output = "${path.root}/manifest.json"
  }
}