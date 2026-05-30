variable "enabled" {
  description = "Create OpenStack compute instances when true."
  type        = bool
  default     = true
}

variable "name_prefix" {
  description = "Prefix for instance names."
  type        = string
}

variable "image_name" {
  description = "OpenStack image name to boot from."
  type        = string
}

variable "flavor_name" {
  description = "OpenStack flavor name for the instances."
  type        = string
}

variable "key_pair" {
  description = "Optional OpenStack key pair."
  type        = string
  default     = ""
}

variable "instance_count" {
  description = "Number of instances to create."
  type        = number
  default     = 1
}

variable "security_groups" {
  description = "Security groups to attach to instances."
  type        = list(string)
  default     = ["default"]
}

variable "metadata" {
  description = "Metadata to attach to instances."
  type        = map(string)
  default     = {}
}

variable "availability_zone" {
  description = "Optional availability zone."
  type        = string
  default     = ""
}

variable "user_data" {
  description = "Optional cloud-init user data."
  type        = string
  default     = ""
}

variable "network_id" {
  description = "Optional OpenStack network UUID."
  type        = string
  default     = ""
}