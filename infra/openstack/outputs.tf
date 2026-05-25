output "public_network_id" {
  value = module.networking.public_network_id
}

output "services_network_id" {
  value = module.networking.services_network_id
}

output "database_network_id" {
  value = module.networking.database_network_id
}

output "api_gateway_instance_id" {
  value = module.compute.api_gateway_instance_id
}

output "service_node_ids" {
  value = module.compute.service_node_ids
}

output "database_node_ids" {
  value = module.compute.database_node_ids
}

output "kubernetes_control_plane_instance_id" {
  value = module.compute.kubernetes_control_plane_instance_id
}

output "kubernetes_worker_ids" {
  value = module.compute.kubernetes_worker_ids
}

output "kafka_broker_ids" {
  value = module.compute.kafka_broker_ids
}

output "spark_master_instance_id" {
  value = module.compute.spark_master_instance_id
}

output "spark_worker_ids" {
  value = module.compute.spark_worker_ids
}

output "postgres_primary_instance_id" {
  value = module.compute.postgres_primary_instance_id
}

output "postgres_replica_instance_ids" {
  value = module.compute.postgres_replica_instance_ids
}

output "hdfs_namenode_instance_ids" {
  value = module.compute.hdfs_namenode_instance_ids
}

output "hdfs_datanode_instance_ids" {
  value = module.compute.hdfs_datanode_instance_ids
}

output "zookeeper_instance_ids" {
  value = module.compute.zookeeper_instance_ids
}

output "hbase_master_instance_id" {
  value = module.compute.hbase_master_instance_id
}

output "hbase_regionserver_instance_ids" {
  value = module.compute.hbase_regionserver_instance_ids
}

output "database_volume_id" {
  value = module.storage.database_volume_id
}

output "object_storage_volume_id" {
  value = module.storage.object_storage_volume_id
}

output "logs_volume_id" {
  value = module.storage.logs_volume_id
}

output "kafka_log_volume_ids" {
  value = module.storage.kafka_log_volume_ids
}

output "spark_checkpoint_volume_id" {
  value = module.storage.spark_checkpoint_volume_id
}

output "postgres_data_volume_id" {
  value = module.storage.postgres_data_volume_id
}

output "postgres_wal_volume_id" {
  value = module.storage.postgres_wal_volume_id
}

output "postgres_replica_volume_ids" {
  value = module.storage.postgres_replica_volume_ids
}

output "hdfs_namenode_volume_ids" {
  value = module.storage.hdfs_namenode_volume_ids
}

output "hdfs_datanode_volume_ids" {
  value = module.storage.hdfs_datanode_volume_ids
}