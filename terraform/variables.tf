variable "openstack_enabled" {
  description = "Enable OpenStack resources during apply. Keeping this false preserves a no-op OpenStack plan while still allowing init."
  type        = bool
  default     = false
}

variable "openstack_cloud" {
  description = "Named cloud from clouds.yaml. Leave empty to rely on environment variables or explicit auth variables."
  type        = string
  default     = ""
}

variable "openstack_auth_url" {
  description = "OpenStack auth URL. Can also be supplied by OS_AUTH_URL."
  type        = string
  default     = ""
  sensitive   = true
}

variable "openstack_region" {
  description = "OpenStack region name. Can also be supplied by OS_REGION_NAME."
  type        = string
  default     = ""
}

variable "openstack_project_name" {
  description = "OpenStack project or tenant name. Can also be supplied by OS_PROJECT_NAME."
  type        = string
  default     = ""
}

variable "openstack_username" {
  description = "OpenStack username. Can also be supplied by OS_USERNAME."
  type        = string
  default     = ""
}

variable "openstack_password" {
  description = "OpenStack password. Can also be supplied by OS_PASSWORD."
  type        = string
  default     = ""
  sensitive   = true
}

variable "openstack_user_domain_name" {
  description = "OpenStack user domain name. Can also be supplied by OS_USER_DOMAIN_NAME."
  type        = string
  default     = "Default"
}

variable "openstack_project_domain_name" {
  description = "OpenStack project domain name. Can also be supplied by OS_PROJECT_DOMAIN_NAME."
  type        = string
  default     = "Default"
}

variable "openstack_network" {
  description = "Configuration for the reusable OpenStack network module."
  type = object({
    enabled      = bool
    network_name = string
    subnet_name  = string
    subnet_cidr  = string
  })
  default = {
    enabled      = true
    network_name = "orca-platform-network"
    subnet_name  = "orca-platform-subnet"
    subnet_cidr  = "10.42.0.0/24"
  }
}

variable "openstack_compute" {
  description = "Map of OpenStack compute groups to create."
  type = map(object({
    enabled           = bool
    name_prefix       = string
    image_name        = string
    flavor_name       = string
    key_pair          = string
    instance_count    = number
    security_groups   = list(string)
    metadata          = map(string)
    availability_zone = string
    user_data         = string
    network_id        = string
  }))
  default = {
    control = {
      enabled           = true
      name_prefix       = "orca-control"
      image_name        = "ubuntu-22.04"
      flavor_name       = "m1.medium"
      key_pair          = ""
      instance_count    = 1
      security_groups   = ["default"]
      metadata          = { role = "control-plane", stack = "orca" }
      availability_zone = ""
      user_data         = ""
      network_id        = ""
    }
    worker = {
      enabled           = true
      name_prefix       = "orca-worker"
      image_name        = "ubuntu-22.04"
      flavor_name       = "m1.large"
      key_pair          = ""
      instance_count    = 2
      security_groups   = ["default"]
      metadata          = { role = "worker", stack = "orca" }
      availability_zone = ""
      user_data         = ""
      network_id        = ""
    }
  }
}

variable "kubernetes_enabled" {
  description = "Enable Kubernetes namespace and workload deployment during apply."
  type        = bool
  default     = false
}

variable "kubeconfig_path" {
  description = "Path to kubeconfig used by the Kubernetes provider."
  type        = string
  default     = ""
}

variable "kubeconfig_context" {
  description = "Optional kubeconfig context for the Kubernetes provider."
  type        = string
  default     = ""
}

variable "kubernetes_host" {
  description = "Optional direct Kubernetes API host."
  type        = string
  default     = ""
}

variable "kubernetes_token" {
  description = "Optional direct Kubernetes bearer token."
  type        = string
  default     = ""
  sensitive   = true
}

variable "kubernetes_cluster_ca_certificate" {
  description = "Optional base64 encoded Kubernetes CA certificate when configuring the provider directly."
  type        = string
  default     = ""
  sensitive   = true
}

variable "namespaces" {
  description = "Namespaces to ensure exist before ORCA workloads are deployed."
  type        = list(string)
  default     = ["orca-system", "orca-observability"]
}

variable "orca_namespace" {
  description = "Primary namespace for ORCA platform workloads."
  type        = string
  default     = "orca-system"
}

variable "orca_workloads" {
  description = "ORCA workloads deployed through the Kubernetes provider."
  type = map(object({
    model_name     = string
    image          = string
    image_pull_policy = string
    replicas       = number
    service_port   = number
    container_port = number
    service_type   = string
    command        = list(string)
    env            = map(string)
    labels         = map(string)
  }))
  default = {
    orca-telemetry = {
      model_name     = "ORCA-Telemetry"
      image          = "atonixdev/orca-drone-gateway:1.0.0-k8s"
      image_pull_policy = "IfNotPresent"
      replicas       = 2
      service_port   = 8020
      container_port = 8020
      service_type   = "ClusterIP"
      command        = ["uvicorn", "surveillance.drone_gateway_service:app", "--host", "0.0.0.0", "--port", "8020"]
      env            = { PYTHONPATH = "/app" }
      labels         = { component = "telemetry", tier = "edge-ingest" }
    }
    orca-mapping = {
      model_name     = "ORCA-Mapping"
      image          = "atonixdev/orca-mapping-geospatial:1.0.0-k8s"
      image_pull_policy = "IfNotPresent"
      replicas       = 1
      service_port   = 8024
      container_port = 8024
      service_type   = "ClusterIP"
      command        = ["uvicorn", "surveillance.mapping_service:app", "--host", "0.0.0.0", "--port", "8024"]
      env            = { PYTHONPATH = "/app" }
      labels         = { component = "mapping", tier = "geospatial" }
    }
    orca-ai = {
      model_name     = "ORCA-AI"
      image          = "atonixdev/orca-ai-service:1.0.0"
      image_pull_policy = "IfNotPresent"
      replicas       = 1
      service_port   = 8012
      container_port = 8012
      service_type   = "ClusterIP"
      command        = []
      env            = {}
      labels         = { component = "ai", tier = "inference" }
    }
    orca-gateway = {
      model_name     = "ORCA-Gateway"
      image          = "atonixdev/orca-api-gateway:1.0.0-k8s"
      image_pull_policy = "IfNotPresent"
      replicas       = 2
      service_port   = 8000
      container_port = 8000
      service_type   = "ClusterIP"
      command        = []
      env = {
        AI_MODELS_URL          = "http://orca-ai.orca-system.svc.cluster.local:8012"
        DRONE_GATEWAY_URL      = "http://orca-telemetry.orca-system.svc.cluster.local:8020"
        MAPPING_GEOSPATIAL_URL = "http://orca-mapping.orca-system.svc.cluster.local:8024"
        OBJECT_STORAGE_ENDPOINT = "file:///tmp/orca-object-storage"
        PYTHONPATH              = "/app"
      }
      labels = { component = "gateway", tier = "api" }
    }
    orca-agent = {
      model_name     = "ORCA-Agent"
      image          = "atonixdev/orca-hardware-agent:1.0.0"
      image_pull_policy = "IfNotPresent"
      replicas       = 1
      service_port   = 8014
      container_port = 8014
      service_type   = "ClusterIP"
      command        = []
      env            = {}
      labels         = { component = "agent", tier = "edge" }
    }
  }
}