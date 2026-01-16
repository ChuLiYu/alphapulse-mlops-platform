# Variables for networking module

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

# AWS Networking Variables
variable "aws_vpc_cidr" {
  description = "CIDR block for AWS VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "aws_public_subnet_cidr" {
  description = "CIDR block for AWS public subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "aws_availability_zone" {
  description = "AWS availability zone"
  type        = string
  default     = "us-east-1a"
}

# Hetzner Cloud Networking Variables
variable "hcloud_network_cidr" {
  description = "CIDR block for Hetzner Cloud network"
  type        = string
  default     = "10.1.0.0/16"
}

variable "hcloud_subnet_cidr" {
  description = "CIDR block for Hetzner Cloud subnet"
  type        = string
  default     = "10.1.1.0/24"
}

variable "hcloud_network_zone" {
  description = "Hetzner Cloud network zone"
  type        = string
  default     = "eu-central"
}

# Tags
variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project    = "AlphaPulse"
    ManagedBy  = "Terraform"
    Repository = "https://github.com/your-org/alphapulse-mlops-platform"
  }
}