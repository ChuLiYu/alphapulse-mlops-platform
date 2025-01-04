# Outputs for S3 module

# Bucket Information
output "bucket_id" {
  description = "ID of the S3 bucket"
  value       = aws_s3_bucket.ml_artifacts.id
}

output "bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.ml_artifacts.arn
}

output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.ml_artifacts.bucket
}

output "bucket_domain_name" {
  description = "Domain name of the S3 bucket"
  value       = aws_s3_bucket.ml_artifacts.bucket_domain_name
}

output "bucket_regional_domain_name" {
  description = "Regional domain name of the S3 bucket"
  value       = aws_s3_bucket.ml_artifacts.bucket_regional_domain_name
}

# IAM User Information (for MLflow access)
output "mlflow_iam_user_name" {
  description = "Name of the IAM user for MLflow"
  value       = aws_iam_user.mlflow_user.name
}

output "mlflow_iam_user_arn" {
  description = "ARN of the IAM user for MLflow"
  value       = aws_iam_user.mlflow_user.arn
}

output "mlflow_access_key_id" {
  description = "Access key ID for MLflow IAM user"
  value       = aws_iam_access_key.mlflow_user.id
  sensitive   = true
}

output "mlflow_secret_access_key" {
  description = "Secret access key for MLflow IAM user"
  value       = aws_iam_access_key.mlflow_user.secret
  sensitive   = true
}

# Cost Information
output "monthly_cost_estimate" {
  description = "Estimated monthly cost for S3 storage"
  value = {
    standard_storage = "~$0.023 per GB"
    glacier_storage  = "~$0.0036 per GB"
    api_requests     = "~$0.0004 per 1000 requests"
    data_transfer    = "~$0.09 per GB (outbound)"
    estimated_monthly = "$1.15 (based on 50GB storage + minimal usage)"
  }
}

# Configuration Information
output "bucket_configuration" {
  description = "S3 bucket configuration summary"
  value = {
    versioning_enabled      = true
    encryption_enabled      = true
    public_access_blocked   = true
    lifecycle_rules         = true
    environment             = var.environment
    region                  = var.aws_region
    storage_classes         = ["STANDARD", "GLACIER"]
    transition_days         = 90
  }
}

# Connection Information
output "mlflow_s3_configuration" {
  description = "MLflow S3 configuration"
  value = {
    aws_access_key_id     = aws_iam_access_key.mlflow_user.id
    aws_secret_access_key = aws_iam_access_key.mlflow_user.secret
    s3_bucket             = aws_s3_bucket.ml_artifacts.bucket
    s3_endpoint_url       = "https://s3.${var.aws_region}.amazonaws.com"
    s3_region             = var.aws_region
  }
  sensitive = true
}

# Monitoring Information
output "cloudwatch_dashboard_url" {
  description = "CloudWatch dashboard URL for S3 metrics"
  value = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=alphapulse-s3-metrics-${var.environment}"
}

# Resource Group Information
output "resource_group_name" {
  description = "Name of the AWS Resource Group"
  value       = aws_resourcegroups_group.alphapulse.name
}

output "resource_group_arn" {
  description = "ARN of the AWS Resource Group"
  value       = aws_resourcegroups_group.alphapulse.arn
}