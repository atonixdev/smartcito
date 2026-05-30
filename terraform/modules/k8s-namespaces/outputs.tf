output "namespaces" {
  description = "Names of the managed namespaces."
  value       = [for namespace in kubernetes_namespace_v1.namespace : namespace.metadata[0].name]
}