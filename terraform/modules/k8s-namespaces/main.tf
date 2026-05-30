terraform {
  required_providers {
    kubernetes = {
      source = "hashicorp/kubernetes"
    }
  }
}

resource "kubernetes_namespace_v1" "namespace" {
  for_each = var.enabled ? toset(var.namespaces) : toset([])

  metadata {
    name = each.value

    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
      "orca.atonix.dev/platform"     = "orca"
    }
  }
}