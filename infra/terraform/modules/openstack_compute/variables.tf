variable "name_prefix" {
  type = string
}

variable "image_name" {
  type = string
}

variable "flavor_name" {
  type = string
}

variable "key_pair" {
  type = string
}

variable "network_id" {
  type = string
}

variable "security_groups" {
  type = list(string)
}

variable "instance_count" {
  type = number
}
