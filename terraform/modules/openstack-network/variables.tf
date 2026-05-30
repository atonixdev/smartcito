variable "enabled" {
  description = "Create OpenStack networking resources when true."
  type        = bool
  default     = true
}

variable "network_name" {
  description = "Name of the OpenStack network to create."
  type        = string
}

variable "subnet_name" {
  description = "Name of the OpenStack subnet to create."
  type        = string
}

variable "subnet_cidr" {
  description = "CIDR for the OpenStack subnet."
  type        = string
}