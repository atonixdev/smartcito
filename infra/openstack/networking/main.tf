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

resource "openstack_networking_network_v2" "public_net" {
  name           = "smartcito-public-net"
  admin_state_up = true
}

resource "openstack_networking_subnet_v2" "public_subnet" {
  name       = "smartcito-public-subnet"
  network_id = openstack_networking_network_v2.public_net.id
  cidr       = var.public_subnet_cidr
  ip_version = 4
  gateway_ip = var.public_gateway_ip
  dns_nameservers = var.dns_nameservers
}

resource "openstack_networking_network_v2" "services_net" {
  name           = "smartcito-services-net"
  admin_state_up = true
}

resource "openstack_networking_subnet_v2" "services_subnet" {
  name       = "smartcito-services-subnet"
  network_id = openstack_networking_network_v2.services_net.id
  cidr       = var.services_subnet_cidr
  ip_version = 4
  gateway_ip = var.services_gateway_ip
  dns_nameservers = var.dns_nameservers
}

resource "openstack_networking_network_v2" "database_net" {
  name           = "smartcito-database-net"
  admin_state_up = true
}

resource "openstack_networking_subnet_v2" "database_subnet" {
  name       = "smartcito-database-subnet"
  network_id = openstack_networking_network_v2.database_net.id
  cidr       = var.database_subnet_cidr
  ip_version = 4
  gateway_ip = var.database_gateway_ip
  dns_nameservers = var.dns_nameservers
}

resource "openstack_networking_router_v2" "smartcito_router" {
  name                = "smartcito-edge-router"
  admin_state_up      = true
  external_network_id = var.external_network_id
}

resource "openstack_networking_router_interface_v2" "public_interface" {
  router_id = openstack_networking_router_v2.smartcito_router.id
  subnet_id = openstack_networking_subnet_v2.public_subnet.id
}

resource "openstack_networking_router_interface_v2" "services_interface" {
  router_id = openstack_networking_router_v2.smartcito_router.id
  subnet_id = openstack_networking_subnet_v2.services_subnet.id
}

resource "openstack_networking_router_interface_v2" "database_interface" {
  router_id = openstack_networking_router_v2.smartcito_router.id
  subnet_id = openstack_networking_subnet_v2.database_subnet.id
}

resource "openstack_networking_secgroup_v2" "public_ingress" {
  name        = "smartcito-public-ingress"
  description = "Allow HTTP/HTTPS access to API gateway and webapp only."
}

resource "openstack_networking_secgroup_rule_v2" "public_http" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 80
  port_range_max    = 80
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.public_ingress.id
}

resource "openstack_networking_secgroup_rule_v2" "public_https" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 443
  port_range_max    = 443
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.public_ingress.id
}

resource "openstack_networking_secgroup_v2" "database_internal" {
  name        = "smartcito-database-internal"
  description = "Restrict database access to internal SmartCito networks only."
}

resource "openstack_networking_secgroup_v2" "kubernetes_internal" {
  name        = "smartcito-kubernetes-internal"
  description = "Allow Kubernetes control-plane and node traffic on SmartCito internal networks."
}

resource "openstack_networking_secgroup_rule_v2" "kubernetes_api" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 6443
  port_range_max    = 6443
  remote_ip_prefix  = var.public_subnet_cidr
  security_group_id = openstack_networking_secgroup_v2.kubernetes_internal.id
}

resource "openstack_networking_secgroup_rule_v2" "kubernetes_kubelet" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 10250
  port_range_max    = 10259
  remote_ip_prefix  = var.services_subnet_cidr
  security_group_id = openstack_networking_secgroup_v2.kubernetes_internal.id
}

resource "openstack_networking_secgroup_v2" "data_platform_internal" {
  name        = "smartcito-data-platform-internal"
  description = "Allow Kafka, Spark, and service-plane communication on internal networks only."
}

resource "openstack_networking_secgroup_rule_v2" "data_platform_kafka" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 9092
  port_range_max    = 9093
  remote_ip_prefix  = var.services_subnet_cidr
  security_group_id = openstack_networking_secgroup_v2.data_platform_internal.id
}

resource "openstack_networking_secgroup_rule_v2" "data_platform_spark" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 7077
  port_range_max    = 8080
  remote_ip_prefix  = var.services_subnet_cidr
  security_group_id = openstack_networking_secgroup_v2.data_platform_internal.id
}

resource "openstack_networking_secgroup_rule_v2" "data_platform_memcached" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 11211
  port_range_max    = 11211
  remote_ip_prefix  = var.services_subnet_cidr
  security_group_id = openstack_networking_secgroup_v2.data_platform_internal.id
}

resource "openstack_networking_secgroup_rule_v2" "data_platform_hdfs_rpc" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 8020
  port_range_max    = 8020
  remote_ip_prefix  = var.services_subnet_cidr
  security_group_id = openstack_networking_secgroup_v2.data_platform_internal.id
}

resource "openstack_networking_secgroup_rule_v2" "data_platform_hdfs_web" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 9870
  port_range_max    = 9870
  remote_ip_prefix  = var.services_subnet_cidr
  security_group_id = openstack_networking_secgroup_v2.data_platform_internal.id
}

resource "openstack_networking_secgroup_rule_v2" "data_platform_hdfs_datanode" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 9864
  port_range_max    = 9867
  remote_ip_prefix  = var.services_subnet_cidr
  security_group_id = openstack_networking_secgroup_v2.data_platform_internal.id
}

resource "openstack_networking_secgroup_rule_v2" "data_platform_hbase_master" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 16000
  port_range_max    = 16010
  remote_ip_prefix  = var.services_subnet_cidr
  security_group_id = openstack_networking_secgroup_v2.data_platform_internal.id
}

resource "openstack_networking_secgroup_rule_v2" "data_platform_hbase_regionserver" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 16020
  port_range_max    = 16030
  remote_ip_prefix  = var.services_subnet_cidr
  security_group_id = openstack_networking_secgroup_v2.data_platform_internal.id
}

resource "openstack_networking_secgroup_rule_v2" "data_platform_hbase_thrift" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 9090
  port_range_max    = 9095
  remote_ip_prefix  = var.services_subnet_cidr
  security_group_id = openstack_networking_secgroup_v2.data_platform_internal.id
}

resource "openstack_networking_secgroup_rule_v2" "data_platform_zookeeper_client" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 2181
  port_range_max    = 2181
  remote_ip_prefix  = var.services_subnet_cidr
  security_group_id = openstack_networking_secgroup_v2.data_platform_internal.id
}

resource "openstack_networking_secgroup_rule_v2" "data_platform_zookeeper_quorum" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 2888
  port_range_max    = 3888
  remote_ip_prefix  = var.services_subnet_cidr
  security_group_id = openstack_networking_secgroup_v2.data_platform_internal.id
}

resource "openstack_networking_secgroup_rule_v2" "database_postgres" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 5432
  port_range_max    = 5432
  remote_ip_prefix  = var.services_subnet_cidr
  security_group_id = openstack_networking_secgroup_v2.database_internal.id
}

resource "openstack_networking_secgroup_rule_v2" "database_mysql_block_placeholder" {
  direction         = "egress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 1
  port_range_max    = 65535
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.database_internal.id
}