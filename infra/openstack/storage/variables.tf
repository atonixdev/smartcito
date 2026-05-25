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
  type = string
}

variable "database_volume_size_gb" {
  type    = number
  default = 100
}

variable "object_storage_volume_size_gb" {
  type    = number
  default = 250
}

variable "logs_volume_size_gb" {
  type    = number
  default = 150
}

variable "kafka_log_volume_size_gb" {
  type    = number
  default = 250
}

variable "spark_checkpoint_volume_size_gb" {
  type    = number
  default = 150
}

variable "kafka_broker_count" {
  type    = number
  default = 3
}