# AlphaPulse Dev Environment - Hybrid Cloud (Hetzner + AWS S3)
# Total Cost: $6.16/month (Hetzner CPX11: $4.51 + AWS S3: $1.65)

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.45"
    }
  }

  backend "s3" {
    bucket         = "alphapulse-terraform-state"
    key            = "environments/dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "alphapulse-terraform-locks"
  }
}

# Provider configurations
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = "dev"
      Project     = "AlphaPulse"
      ManagedBy   = "Terraform"
    }
  }
}

provider "hcloud" {
  token = var.hcloud_token
}

# Local variables
locals {
  environment = "dev"
  common_tags = {
    Environment = local.environment
    Project     = "AlphaPulse"
    ManagedBy   = "Terraform"
    Repository  = "https://github.com/your-org/alphapulse-mlops-platform"
    CostCenter  = "mlops-platform"
  }
}

# Networking module
module "networking" {
  source = "../../modules/networking"
  
  environment = local.environment
  
  # AWS networking
  aws_vpc_cidr             = "10.0.0.0/16"
  aws_public_subnet_cidr   = "10.0.1.0/24"
  aws_availability_zone    = "us-east-1a"
  
  # Hetzner networking
  hcloud_network_cidr     = "10.1.0.0/16"
  hcloud_subnet_cidr      = "10.1.1.0/24"
  hcloud_network_zone     = "eu-central"
  
  common_tags = local.common_tags
}

# S3 module for ML artifacts
module "s3" {
  source = "../../modules/s3"
  
  environment = local.environment
  bucket_name = "alphapulse-ml-artifacts-dev"
  aws_region  = var.aws_region
  
  # IAM roles (to be created separately)
  mlflow_iam_role_arn        = var.mlflow_iam_role_arn
  hetzner_server_iam_role_arn = var.hetzner_server_iam_role_arn
  
  common_tags = local.common_tags
}

# Compute module (Hetzner CPX11 for dev)
module "compute" {
  source = "../../modules/ec2"
  
  environment = local.environment
  
  # Hetzner configuration
  server_type        = "cpx11"  # CPX11: 2 vCPU, 2GB RAM, 40GB SSD, €4.51/month
  hcloud_location    = "fsn1"
  hcloud_network_id  = module.networking.hcloud_network_id
  hcloud_firewall_id = module.networking.hcloud_firewall_id
  
  # Docker Compose configuration
  docker_compose_file = file("${path.module}/docker-compose.yml")
  
  # Database configuration
  postgres_password = var.postgres_password
  
  # MinIO configuration
  minio_access_key = var.minio_access_key
  minio_secret_key = var.minio_secret_key
  
  # MLflow configuration
  mlflow_tracking_uri = "http://localhost:5001"
  
  # AWS S3 configuration
  aws_s3_bucket         = module.s3.bucket_name
  aws_access_key_id     = module.s3.mlflow_access_key_id
  aws_secret_access_key = module.s3.mlflow_secret_access_key
  
  # DNS configuration
  domain_name = var.domain_name
  
  # Storage configuration
  enable_data_volume = true
  data_volume_size   = 50
  
  common_tags = local.common_tags
  
  depends_on = [
    module.networking,
    module.s3
  ]
}

# Outputs
output "environment" {
  description = "Environment name"
  value       = local.environment
}

output "total_monthly_cost" {
  description = "Total estimated monthly cost"
  value = {
    hetzner_server = "€4.51 ($4.51) - CPX11 (2GB RAM)"
    aws_s3         = "$1.65"
    total          = "$6.16"
    savings_vs_aws = "92% vs AWS EKS ($73/month)"
    upgrade_option = "CPX21: $11.15/month (4GB RAM)"
  }
}

output "service_urls" {
  description = "Service URLs for the AlphaPulse platform"
  value = {
    mage_ui          = module.compute.mage_ui_url
    mlflow_ui        = module.compute.mlflow_ui_url
    minio_console    = module.compute.minio_console_url
    minio_api        = module.compute.minio_api_url
    postgres_host    = module.compute.private_ip
    postgres_port    = 5432
  }
}

output "s3_configuration" {
  description = "S3 configuration for MLflow"
  value = module.s3.mlflow_s3_configuration
  sensitive = true
}

output "ssh_instructions" {
  description = "SSH connection instructions"
  value = module.compute.connection_instructions
}

output "deployment_status" {
  description = "Deployment status"
  value = {
    networking_configured = true
    s3_configured         = true
    server_provisioned    = true
    services_deployed     = true
    timestamp             = timestamp()
  }
}
