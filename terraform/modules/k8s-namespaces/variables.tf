variable "enabled" {
  description = "Create namespaces when true."
  type        = bool
  default     = true
}

variable "namespaces" {
  description = "Namespaces to create or manage."
  type        = list(string)
}