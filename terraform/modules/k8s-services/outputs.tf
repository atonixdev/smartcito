output "workloads" {
  description = "Workload deployment and service names keyed by ORCA workload."
  value = {
    for name, deployment in kubernetes_deployment_v1.workload : name => {
      deployment_name = deployment.metadata[0].name
      service_name    = kubernetes_service_v1.workload[name].metadata[0].name
      namespace       = deployment.metadata[0].namespace
      image           = deployment.spec[0].template[0].spec[0].container[0].image
      service_port    = kubernetes_service_v1.workload[name].spec[0].port[0].port
    }
  }
}