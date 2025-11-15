output "backend_service_endpoint" {
  description = "Backend service endpoint"
  value       = kubernetes_service.backend.status[0].load_balancer[0].ingress[0].hostname
}

output "frontend_service_endpoint" {
  description = "Frontend service endpoint"
  value       = kubernetes_service.frontend.status[0].load_balancer[0].ingress[0].hostname
}

output "namespace" {
  description = "Kubernetes namespace"
  value       = kubernetes_namespace.compliance_copilot.metadata[0].name
}

