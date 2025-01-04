# Variables for S3 module

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "bucket_name" {
  description = "Name of the S3 bucket for ML artifacts"
  type        = string
  default     = "alphapulse-ml-artifacts"
}

variable "aws_region" {
  description = "AWS region for S3 bucket"
  type        = string
  default     = "us-east-1"
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