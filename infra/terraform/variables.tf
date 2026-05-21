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

variable "network_name" {
  type    = string
  default = "smartcito-net"
}

variable "subnet_cidr" {
  type    = string
  default = "10.42.0.0/24"
}

variable "image_name" {
  type = string
}

variable "key_pair" {
  type = string
}

variable "controller_flavor" {
  type    = string
  default = "m1.large"
}

variable "compute_flavor" {
  type    = string
  default = "g1.xlarge"
}

variable "storage_flavor" {
  type    = string
  default = "m1.xlarge"
}

variable "controller_count" {
  type    = number
  default = 1
}

variable "compute_count" {
  type    = number
  default = 2
}

variable "storage_count" {
  type    = number
  default = 1
}
