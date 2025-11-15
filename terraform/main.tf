terraform {
  required_version = ">= 1.0"
  
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }
}

provider "kubernetes" {
  config_path    = var.kubeconfig_path
  config_context = var.kube_context
}

provider "helm" {
  kubernetes {
    config_path    = var.kubeconfig_path
    config_context = var.kube_context
  }
}

# Namespace
resource "kubernetes_namespace" "compliance_copilot" {
  metadata {
    name = "compliance-copilot"
  }
}

# Persistent Volume Claim for ChromaDB
resource "kubernetes_persistent_volume_claim" "chroma_pvc" {
  metadata {
    name      = "chroma-pvc"
    namespace = kubernetes_namespace.compliance_copilot.metadata[0].name
  }
  
  spec {
    access_modes = ["ReadWriteMany"]
    resources {
      requests = {
        storage = "50Gi"
      }
    }
    storage_class_name = "standard"
  }
}

# Secret for API keys
resource "kubernetes_secret" "compliance_secrets" {
  metadata {
    name      = "compliance-secrets"
    namespace = kubernetes_namespace.compliance_copilot.metadata[0].name
  }
  
  type = "Opaque"
  
  data = {
    openai-api-key = base64encode(var.openai_api_key)
  }
}

# Backend Deployment
resource "kubernetes_deployment" "backend" {
  metadata {
    name      = "compliance-copilot-backend"
    namespace = kubernetes_namespace.compliance_copilot.metadata[0].name
    labels = {
      app = "compliance-copilot-backend"
    }
  }
  
  spec {
    replicas = var.backend_replicas
    
    selector {
      match_labels = {
        app = "compliance-copilot-backend"
      }
    }
    
    template {
      metadata {
        labels = {
          app = "compliance-copilot-backend"
        }
      }
      
      spec {
        container {
          name  = "backend"
          image = "${var.container_registry}/compliance-copilot-backend:${var.image_tag}"
          
          port {
            container_port = 8000
          }
          
          env {
            name = "OPENAI_API_KEY"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.compliance_secrets.metadata[0].name
                key  = "openai-api-key"
              }
            }
          }
          
          env {
            name  = "CHROMA_PERSIST_DIRECTORY"
            value = "/app/chroma_db"
          }
          
          env {
            name  = "PORT"
            value = "8000"
          }
          
          env {
            name  = "ENVIRONMENT"
            value = "production"
          }
          
          volume_mount {
            name       = "chroma-storage"
            mount_path = "/app/chroma_db"
          }
          
          resources {
            requests = {
              memory = "2Gi"
              cpu    = "1000m"
            }
            limits = {
              memory = "4Gi"
              cpu    = "2000m"
            }
          }
          
          liveness_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            initial_delay_seconds = 30
            period_seconds       = 10
          }
          
          readiness_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            initial_delay_seconds = 10
            period_seconds       = 5
          }
        }
        
        volume {
          name = "chroma-storage"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.chroma_pvc.metadata[0].name
          }
        }
      }
    }
  }
}

# Backend Service
resource "kubernetes_service" "backend" {
  metadata {
    name      = "compliance-copilot-backend-service"
    namespace = kubernetes_namespace.compliance_copilot.metadata[0].name
  }
  
  spec {
    selector = {
      app = "compliance-copilot-backend"
    }
    
    port {
      port        = 80
      target_port = 8000
    }
    
    type = "LoadBalancer"
  }
}

# Frontend Deployment
resource "kubernetes_deployment" "frontend" {
  metadata {
    name      = "compliance-copilot-frontend"
    namespace = kubernetes_namespace.compliance_copilot.metadata[0].name
    labels = {
      app = "compliance-copilot-frontend"
    }
  }
  
  spec {
    replicas = var.frontend_replicas
    
    selector {
      match_labels = {
        app = "compliance-copilot-frontend"
      }
    }
    
    template {
      metadata {
        labels = {
          app = "compliance-copilot-frontend"
        }
      }
      
      spec {
        container {
          name  = "frontend"
          image = "${var.container_registry}/compliance-copilot-frontend:${var.image_tag}"
          
          port {
            container_port = 3000
          }
          
          env {
            name  = "NEXT_PUBLIC_API_URL"
            value = "http://${kubernetes_service.backend.metadata[0].name}:80"
          }
          
          resources {
            requests = {
              memory = "512Mi"
              cpu    = "250m"
            }
            limits = {
              memory = "1Gi"
              cpu    = "500m"
            }
          }
          
          liveness_probe {
            http_get {
              path = "/"
              port = 3000
            }
            initial_delay_seconds = 30
            period_seconds       = 10
          }
          
          readiness_probe {
            http_get {
              path = "/"
              port = 3000
            }
            initial_delay_seconds = 10
            period_seconds       = 5
          }
        }
      }
    }
  }
}

# Frontend Service
resource "kubernetes_service" "frontend" {
  metadata {
    name      = "compliance-copilot-frontend-service"
    namespace = kubernetes_namespace.compliance_copilot.metadata[0].name
  }
  
  spec {
    selector = {
      app = "compliance-copilot-frontend"
    }
    
    port {
      port        = 80
      target_port = 3000
    }
    
    type = "LoadBalancer"
  }
}

