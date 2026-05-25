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

variable "image_name" {
  type = string
}

variable "key_pair" {
  type = string
}

variable "public_network_id" {
  type = string
}

variable "services_network_id" {
  type = string
}

variable "database_network_id" {
  type = string
}

variable "public_security_groups" {
  type = list(string)
}

variable "internal_security_groups" {
  type = list(string)
}

variable "database_security_groups" {
  type = list(string)
}

variable "kubernetes_security_groups" {
  type = list(string)
}

variable "data_platform_security_groups" {
  type = list(string)
}

variable "api_flavor_name" {
  type    = string
  default = "m1.medium"
}

variable "service_flavor_name" {
  type    = string
  default = "m1.large"
}

variable "database_flavor_name" {
  type    = string
  default = "m1.xlarge"
}

variable "kubernetes_control_plane_flavor_name" {
  type    = string
  default = "m1.large"
}

variable "kubernetes_worker_flavor_name" {
  type    = string
  default = "m1.large"
}

variable "kafka_broker_flavor_name" {
  type    = string
  default = "m1.large"
}

variable "spark_master_flavor_name" {
  type    = string
  default = "m1.large"
}

variable "spark_worker_flavor_name" {
  type    = string
  default = "m1.xlarge"
}

variable "postgres_primary_flavor_name" {
  type    = string
  default = "m1.xlarge"
}

variable "postgres_replica_flavor_name" {
  type    = string
  default = "m1.large"
}

variable "hdfs_namenode_flavor_name" {
  type    = string
  default = "m1.large"
}

variable "hdfs_datanode_flavor_name" {
  type    = string
  default = "m1.xlarge"
}

variable "hbase_master_flavor_name" {
  type    = string
  default = "m1.large"
}

variable "hbase_regionserver_flavor_name" {
  type    = string
  default = "m1.xlarge"
}

variable "zookeeper_flavor_name" {
  type    = string
  default = "m1.medium"
}

variable "service_node_count" {
  type    = number
  default = 2
}

variable "database_node_count" {
  type    = number
  default = 1
}

variable "kubernetes_worker_count" {
  type    = number
  default = 3
}

variable "kafka_broker_count" {
  type    = number
  default = 3
}

variable "spark_worker_count" {
  type    = number
  default = 2
}

variable "postgres_replica_count" {
  type    = number
  default = 1
}

variable "hdfs_namenode_count" {
  type    = number
  default = 2
}

variable "hdfs_datanode_count" {
  type    = number
  default = 3
}

variable "hbase_regionserver_count" {
  type    = number
  default = 3
}

variable "zookeeper_node_count" {
  type    = number
  default = 3
}