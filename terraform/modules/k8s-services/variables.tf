variable "enabled" {
  description = "Create Kubernetes deployments and services when true."
  type        = bool
  default     = true
}

variable "namespace" {
  description = "Namespace where ORCA workloads are deployed."
  type        = string
}

variable "workloads" {
  description = "Map of ORCA workloads to deploy."
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
}