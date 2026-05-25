output "database_volume_id" {
  value = openstack_blockstorage_volume_v3.database_volume.id
}

output "object_storage_volume_id" {
  value = openstack_blockstorage_volume_v3.object_storage_volume.id
}

output "logs_volume_id" {
  value = openstack_blockstorage_volume_v3.logs_volume.id
}

output "kafka_log_volume_ids" {
  value = [for volume in openstack_blockstorage_volume_v3.kafka_log_volumes : volume.id]
}

output "spark_checkpoint_volume_id" {
  value = openstack_blockstorage_volume_v3.spark_checkpoint_volume.id
}

output "postgres_data_volume_id" {
  value = openstack_blockstorage_volume_v3.postgres_data_volume.id
}

output "postgres_wal_volume_id" {
  value = openstack_blockstorage_volume_v3.postgres_wal_volume.id
}

output "postgres_replica_volume_ids" {
  value = [for volume in openstack_blockstorage_volume_v3.postgres_replica_volumes : volume.id]
}

output "hdfs_namenode_volume_ids" {
  value = [for volume in openstack_blockstorage_volume_v3.hdfs_namenode_volumes : volume.id]
}

output "hdfs_datanode_volume_ids" {
  value = [for volume in openstack_blockstorage_volume_v3.hdfs_datanode_volumes : volume.id]
}