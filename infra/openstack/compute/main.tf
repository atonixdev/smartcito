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
  cloud            = var.cloud_name
  auth_url         = var.auth_url
  tenant_id        = var.project_id
  tenant_name      = var.project_name
  user_name        = var.username
  password         = var.password
  region           = var.region
  user_domain_name = var.user_domain_name
}

locals {
  cloud_init = <<-EOF
              #cloud-config
              package_update: true
              packages:
                - docker.io
                - containerd
              runcmd:
                - systemctl enable docker
                - systemctl start docker
              EOF

  kubernetes_cloud_init = <<-EOF
              #cloud-config
              package_update: true
              packages:
                - containerd
                - curl
              runcmd:
                - systemctl enable containerd
                - systemctl start containerd
              EOF
}

resource "openstack_compute_instance_v2" "api_gateway" {
  name            = "orca-api-gateway"
  image_name      = var.image_name
  flavor_name     = var.api_flavor_name
  key_pair        = var.key_pair
  security_groups = var.public_security_groups
  user_data       = local.cloud_init

  network {
    uuid = var.public_network_id
  }

  network {
    uuid = var.services_network_id
  }
}

resource "openstack_compute_instance_v2" "service_nodes" {
  count           = var.service_node_count
  name            = "orca-service-${count.index + 1}"
  image_name      = var.image_name
  flavor_name     = var.service_flavor_name
  key_pair        = var.key_pair
  security_groups = var.internal_security_groups
  user_data       = local.cloud_init

  network {
    uuid = var.services_network_id
  }
}

resource "openstack_compute_instance_v2" "database_nodes" {
  count           = var.database_node_count
  name            = "orca-database-${count.index + 1}"
  image_name      = var.image_name
  flavor_name     = var.database_flavor_name
  key_pair        = var.key_pair
  security_groups = var.database_security_groups
  user_data       = local.cloud_init

  network {
    uuid = var.database_network_id
  }
}

resource "openstack_compute_instance_v2" "kubernetes_control_plane" {
  name            = "orca-k8s-control-plane"
  image_name      = var.image_name
  flavor_name     = var.kubernetes_control_plane_flavor_name
  key_pair        = var.key_pair
  security_groups = var.kubernetes_security_groups
  user_data       = local.kubernetes_cloud_init

  network {
    uuid = var.public_network_id
  }

  network {
    uuid = var.services_network_id
  }
}

resource "openstack_compute_instance_v2" "kubernetes_workers" {
  count           = var.kubernetes_worker_count
  name            = "orca-k8s-worker-${count.index + 1}"
  image_name      = var.image_name
  flavor_name     = var.kubernetes_worker_flavor_name
  key_pair        = var.key_pair
  security_groups = var.kubernetes_security_groups
  user_data       = local.kubernetes_cloud_init

  network {
    uuid = var.services_network_id
  }
}

resource "openstack_compute_instance_v2" "kafka_brokers" {
  count           = var.kafka_broker_count
  name            = "orca-kafka-${count.index + 1}"
  image_name      = var.image_name
  flavor_name     = var.kafka_broker_flavor_name
  key_pair        = var.key_pair
  security_groups = var.data_platform_security_groups
  user_data       = local.cloud_init

  network {
    uuid = var.services_network_id
  }
}

resource "openstack_compute_instance_v2" "spark_master" {
  name            = "orca-spark-master"
  image_name      = var.image_name
  flavor_name     = var.spark_master_flavor_name
  key_pair        = var.key_pair
  security_groups = var.data_platform_security_groups
  user_data       = local.cloud_init

  network {
    uuid = var.services_network_id
  }
}

resource "openstack_compute_instance_v2" "spark_workers" {
  count           = var.spark_worker_count
  name            = "orca-spark-worker-${count.index + 1}"
  image_name      = var.image_name
  flavor_name     = var.spark_worker_flavor_name
  key_pair        = var.key_pair
  security_groups = var.data_platform_security_groups
  user_data       = local.cloud_init

  network {
    uuid = var.services_network_id
  }
}

resource "openstack_compute_instance_v2" "postgres_primary" {
  name            = "orca-postgres-primary"
  image_name      = var.image_name
  flavor_name     = var.postgres_primary_flavor_name
  key_pair        = var.key_pair
  security_groups = var.database_security_groups
  user_data       = local.cloud_init

  network {
    uuid = var.database_network_id
  }
}

resource "openstack_compute_instance_v2" "postgres_replicas" {
  count           = var.postgres_replica_count
  name            = "orca-postgres-replica-${count.index + 1}"
  image_name      = var.image_name
  flavor_name     = var.postgres_replica_flavor_name
  key_pair        = var.key_pair
  security_groups = var.database_security_groups
  user_data       = local.cloud_init

  network {
    uuid = var.database_network_id
  }
}

resource "openstack_compute_instance_v2" "hdfs_namenodes" {
  count           = var.hdfs_namenode_count
  name            = "orca-hdfs-namenode-${count.index + 1}"
  image_name      = var.image_name
  flavor_name     = var.hdfs_namenode_flavor_name
  key_pair        = var.key_pair
  security_groups = var.data_platform_security_groups
  user_data       = local.cloud_init

  network {
    uuid = var.services_network_id
  }
}

resource "openstack_compute_instance_v2" "hdfs_datanodes" {
  count           = var.hdfs_datanode_count
  name            = "orca-hdfs-datanode-${count.index + 1}"
  image_name      = var.image_name
  flavor_name     = var.hdfs_datanode_flavor_name
  key_pair        = var.key_pair
  security_groups = var.data_platform_security_groups
  user_data       = local.cloud_init

  network {
    uuid = var.services_network_id
  }
}

resource "openstack_compute_instance_v2" "zookeeper_nodes" {
  count           = var.zookeeper_node_count
  name            = "orca-zookeeper-${count.index + 1}"
  image_name      = var.image_name
  flavor_name     = var.zookeeper_flavor_name
  key_pair        = var.key_pair
  security_groups = var.data_platform_security_groups
  user_data       = local.cloud_init

  network {
    uuid = var.services_network_id
  }
}

resource "openstack_compute_instance_v2" "hbase_master" {
  name            = "orca-hbase-master"
  image_name      = var.image_name
  flavor_name     = var.hbase_master_flavor_name
  key_pair        = var.key_pair
  security_groups = var.data_platform_security_groups
  user_data       = local.cloud_init

  network {
    uuid = var.services_network_id
  }
}

resource "openstack_compute_instance_v2" "hbase_regionservers" {
  count           = var.hbase_regionserver_count
  name            = "orca-hbase-regionserver-${count.index + 1}"
  image_name      = var.image_name
  flavor_name     = var.hbase_regionserver_flavor_name
  key_pair        = var.key_pair
  security_groups = var.data_platform_security_groups
  user_data       = local.cloud_init

  network {
    uuid = var.services_network_id
  }
}