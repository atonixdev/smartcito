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