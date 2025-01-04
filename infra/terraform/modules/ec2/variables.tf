# Variables for compute module

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

# Hetzner Cloud Configuration
variable "server_type" {
  description = "Hetzner server type (cpx11 for dev, cpx21 for prod)"
  type        = string
  default     = "cpx11"

  validation {
    condition     = contains(["cpx11", "cpx21", "cpx31"], var.server_type)
    error_message = "Server type must be one of: cpx11, cpx21, cpx31."
  }
}

variable "hcloud_location" {
  description = "Hetzner Cloud location"
  type        = string
  default     = "fsn1"  # Falkenstein, Germany
}

variable "hcloud_network_id" {
  description = "ID of Hetzner Cloud network"
  type        = string
}

variable "hcloud_firewall_id" {
  description = "ID of Hetzner Cloud firewall"
  type        = string
}

# Docker Compose Configuration
variable "docker_compose_file" {
  description = "Docker Compose file content for deployment"
  type        = string
  default     = ""
}

# Database Configuration
variable "postgres_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
  default     = "postgres"
}

# MinIO Configuration
variable "minio_access_key" {
  description = "MinIO access key"
  type        = string
  sensitive   = true
  default     = "minioadmin"
}

variable "minio_secret_key" {
  description = "MinIO secret key"
  type        = string
  sensitive   = true
  default     = "minioadmin"
}

# MLflow Configuration
variable "mlflow_tracking_uri" {
  description = "MLflow tracking URI"
  type        = string
  default     = "http://localhost:5001"
}

# AWS S3 Configuration (for hybrid cloud)
variable "aws_s3_bucket" {
  description = "AWS S3 bucket name for artifacts"
  type        = string
  default     = ""
}

variable "aws_access_key_id" {
  description = "AWS access key ID"
  type        = string
  sensitive   = true
  default     = ""
}

variable "aws_secret_access_key" {
  description = "AWS secret access key"
  type        = string
  sensitive   = true
  default     = ""
}

# DNS Configuration
variable "domain_name" {
  description = "Domain name for DNS records"
  type        = string
  default     = ""
}

# Storage Configuration
variable "enable_data_volume" {
  description = "Enable persistent data volume"
  type        = bool
  default     = false
}

variable "data_volume_size" {
  description = "Size of data volume in GB"
  type        = number
  default     = 50
}

# Tags
variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "AlphaPulse"
    ManagedBy   = "Terraform"
    Repository  = "https://github.com/your-org/alphapulse-mlops-platform"
  }
}