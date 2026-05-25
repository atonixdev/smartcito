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

variable "external_network_id" {
  type = string
}

variable "image_name" {
  type = string
}

variable "key_pair" {
  type = string
}

variable "public_subnet_cidr" {
  type    = string
  default = "172.20.10.0/24"
}

variable "services_subnet_cidr" {
  type    = string
  default = "172.20.20.0/24"
}

variable "database_subnet_cidr" {
  type    = string
  default = "172.20.30.0/24"
}

variable "public_gateway_ip" {
  type    = string
  default = "172.20.10.1"
}

variable "services_gateway_ip" {
  type    = string
  default = "172.20.20.1"
}

variable "database_gateway_ip" {
  type    = string
  default = "172.20.30.1"
}

variable "dns_nameservers" {
  type    = list(string)
  default = ["1.1.1.1", "8.8.8.8"]
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

variable "postgres_data_volume_size_gb" {
  type    = number
  default = 200
}

variable "postgres_wal_volume_size_gb" {
  type    = number
  default = 100
}

variable "postgres_replica_volume_size_gb" {
  type    = number
  default = 150
}

variable "hdfs_namenode_volume_size_gb" {
  type    = number
  default = 200
}

variable "hdfs_datanode_volume_size_gb" {
  type    = number
  default = 500
}