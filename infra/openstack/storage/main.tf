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

resource "openstack_blockstorage_volume_v3" "database_volume" {
  name        = "smartcito-db-volume"
  size        = var.database_volume_size_gb
  description = "Primary persistent volume for SmartCito databases."
}

resource "openstack_blockstorage_volume_v3" "object_storage_volume" {
  name        = "smartcito-object-volume"
  size        = var.object_storage_volume_size_gb
  description = "Persistent volume for object storage workloads."
}

resource "openstack_blockstorage_volume_v3" "logs_volume" {
  name        = "smartcito-logs-volume"
  size        = var.logs_volume_size_gb
  description = "Persistent volume for aggregated platform logs."
}

resource "openstack_blockstorage_volume_v3" "kafka_log_volumes" {
  count       = var.kafka_broker_count
  name        = "smartcito-kafka-log-${count.index + 1}"
  size        = var.kafka_log_volume_size_gb
  description = "Persistent Kafka broker log volume."
}

resource "openstack_blockstorage_volume_v3" "spark_checkpoint_volume" {
  name        = "smartcito-spark-checkpoints"
  size        = var.spark_checkpoint_volume_size_gb
  description = "Persistent Spark Streaming checkpoint volume."
}

resource "openstack_blockstorage_volume_v3" "postgres_data_volume" {
  name        = "smartcito-postgres-data"
  size        = var.postgres_data_volume_size_gb
  description = "Primary PostgreSQL data volume for business data."
}

resource "openstack_blockstorage_volume_v3" "postgres_wal_volume" {
  name        = "smartcito-postgres-wal"
  size        = var.postgres_wal_volume_size_gb
  description = "Dedicated PostgreSQL WAL volume for primary replication durability."
}

resource "openstack_blockstorage_volume_v3" "postgres_replica_volumes" {
  count       = var.postgres_replica_count
  name        = "smartcito-postgres-replica-${count.index + 1}"
  size        = var.postgres_replica_volume_size_gb
  description = "Replica PostgreSQL data volume."
}

resource "openstack_blockstorage_volume_v3" "hdfs_namenode_volumes" {
  count       = var.hdfs_namenode_count
  name        = "smartcito-hdfs-namenode-${count.index + 1}"
  size        = var.hdfs_namenode_volume_size_gb
  description = "Dedicated HDFS NameNode metadata volume."
}

resource "openstack_blockstorage_volume_v3" "hdfs_datanode_volumes" {
  count       = var.hdfs_datanode_count
  name        = "smartcito-hdfs-datanode-${count.index + 1}"
  size        = var.hdfs_datanode_volume_size_gb
  description = "Dedicated HDFS DataNode data volume."
}