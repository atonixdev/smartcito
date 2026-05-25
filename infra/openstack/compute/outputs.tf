output "api_gateway_instance_id" {
  value = openstack_compute_instance_v2.api_gateway.id
}

output "service_node_ids" {
  value = [for node in openstack_compute_instance_v2.service_nodes : node.id]
}

output "database_node_ids" {
  value = [for node in openstack_compute_instance_v2.database_nodes : node.id]
}

output "kubernetes_control_plane_instance_id" {
  value = openstack_compute_instance_v2.kubernetes_control_plane.id
}

output "kubernetes_worker_ids" {
  value = [for node in openstack_compute_instance_v2.kubernetes_workers : node.id]
}

output "kafka_broker_ids" {
  value = [for node in openstack_compute_instance_v2.kafka_brokers : node.id]
}

output "spark_master_instance_id" {
  value = openstack_compute_instance_v2.spark_master.id
}

output "spark_worker_ids" {
  value = [for node in openstack_compute_instance_v2.spark_workers : node.id]
}

output "postgres_primary_instance_id" {
  value = openstack_compute_instance_v2.postgres_primary.id
}

output "postgres_replica_instance_ids" {
  value = [for node in openstack_compute_instance_v2.postgres_replicas : node.id]
}

output "hdfs_namenode_instance_ids" {
  value = [for node in openstack_compute_instance_v2.hdfs_namenodes : node.id]
}

output "hdfs_datanode_instance_ids" {
  value = [for node in openstack_compute_instance_v2.hdfs_datanodes : node.id]
}

output "zookeeper_instance_ids" {
  value = [for node in openstack_compute_instance_v2.zookeeper_nodes : node.id]
}

output "hbase_master_instance_id" {
  value = openstack_compute_instance_v2.hbase_master.id
}

output "hbase_regionserver_instance_ids" {
  value = [for node in openstack_compute_instance_v2.hbase_regionservers : node.id]
}