# Variables for dev environment

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "hcloud_token" {
  description = "Hetzner Cloud API token"
  type        = string
  sensitive   = true
}

variable "postgres_password" {
  description = "PostgreSQL database password"
  type        = string
  sensitive   = true
  default     = "postgres"
}

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

variable "mlflow_iam_role_arn" {
  description = "ARN of IAM role for MLflow access"
  type        = string
  default     = ""
}

variable "hetzner_server_iam_role_arn" {
  description = "ARN of IAM role for Hetzner server access"
  type        = string
  default     = ""
}

variable "domain_name" {
  description = "Domain name for DNS records"
  type        = string
  default     = ""
}

# Cost tracking variables
variable "monthly_budget" {
  description = "Monthly budget for dev environment"
  type        = number
  default     = 15.00  # $15/month budget
}

variable "cost_alert_threshold" {
  description = "Cost alert threshold percentage"
  type        = number
  default     = 80  # Alert at 80% of budget
}