terraform {
  required_providers {
    kubernetes = {
      source = "hashicorp/kubernetes"
    }
  }
}

locals {
  workload_labels = {
    for name, workload in var.workloads : name => merge(
      {
        "app.kubernetes.io/name"       = name
        "app.kubernetes.io/component"  = "orca-workload"
        "app.kubernetes.io/managed-by" = "terraform"
        "orca.atonix.dev/model"        = workload.model_name
      },
      workload.labels,
    )
  }
}

resource "kubernetes_deployment_v1" "workload" {
  for_each = var.enabled ? var.workloads : {}

  metadata {
    name      = each.key
    namespace = var.namespace
    labels    = local.workload_labels[each.key]
  }

  spec {
    replicas = each.value.replicas

    selector {
      match_labels = local.workload_labels[each.key]
    }

    template {
      metadata {
        labels = local.workload_labels[each.key]
      }

      spec {
        container {
          name  = each.key
          image = each.value.image
          image_pull_policy = each.value.image_pull_policy
          command = each.value.command

          port {
            container_port = each.value.container_port
          }

          dynamic "env" {
            for_each = each.value.env
            content {
              name  = env.key
              value = env.value
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service_v1" "workload" {
  for_each = var.enabled ? var.workloads : {}

  metadata {
    name      = each.key
    namespace = var.namespace
    labels    = local.workload_labels[each.key]
  }

  spec {
    selector = local.workload_labels[each.key]
    type     = each.value.service_type

    port {
      port        = each.value.service_port
      target_port = each.value.container_port
      protocol    = "TCP"
    }
  }
}