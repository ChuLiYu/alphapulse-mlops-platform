# S3 module for AlphaPulse hybrid cloud infrastructure
# Provides AWS S3 bucket for ML artifacts storage

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# S3 Bucket for ML artifacts
resource "aws_s3_bucket" "ml_artifacts" {
  bucket = var.bucket_name
  tags = {
    Name        = "alphapulse-ml-artifacts"
    Environment = var.environment
    Project     = "AlphaPulse"
    CostCenter  = "mlops-platform"
  }
}

# Enable versioning for ML artifacts
resource "aws_s3_bucket_versioning" "ml_artifacts" {
  bucket = aws_s3_bucket.ml_artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Enable server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "ml_artifacts" {
  bucket = aws_s3_bucket.ml_artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "ml_artifacts" {
  bucket = aws_s3_bucket.ml_artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle rules for cost optimization
resource "aws_s3_bucket_lifecycle_configuration" "ml_artifacts" {
  bucket = aws_s3_bucket.ml_artifacts.id

  rule {
    id     = "transition_to_glacier"
    status = "Enabled"

    # Apply to all objects
    filter {}

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "GLACIER"
    }

    # Expire non-current versions after 1 year
    noncurrent_version_expiration {
      noncurrent_days = 365
    }
  }

  rule {
    id     = "abort_incomplete_multipart_upload"
    status = "Enabled"

    # Apply to all objects
    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# Bucket policy for secure access
resource "aws_s3_bucket_policy" "ml_artifacts" {
  bucket = aws_s3_bucket.ml_artifacts.id
  policy = data.aws_iam_policy_document.bucket_policy.json
}

# IAM policy document for bucket access
data "aws_iam_policy_document" "bucket_policy" {
  statement {
    sid    = "AllowMLflowAccess"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = [var.mlflow_iam_role_arn]
    }

    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket"
    ]

    resources = [
      aws_s3_bucket.ml_artifacts.arn,
      "${aws_s3_bucket.ml_artifacts.arn}/*"
    ]
  }

  statement {
    sid    = "AllowHetznerServerAccess"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = [var.hetzner_server_iam_role_arn]
    }

    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket"
    ]

    resources = [
      aws_s3_bucket.ml_artifacts.arn,
      "${aws_s3_bucket.ml_artifacts.arn}/*"
    ]
  }

  statement {
    sid    = "DenyNonSSL"
    effect = "Deny"

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions = [
      "s3:*"
    ]

    resources = [
      aws_s3_bucket.ml_artifacts.arn,
      "${aws_s3_bucket.ml_artifacts.arn}/*"
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

# IAM user for programmatic access (for MLflow, etc.)
resource "aws_iam_user" "mlflow_user" {
  name = "alphapulse-mlflow-${var.environment}"
  path = "/alphapulse/"

  tags = {
    Environment = var.environment
    Project     = "AlphaPulse"
    Purpose     = "mlflow-artifacts"
  }
}

# IAM access key for the user
resource "aws_iam_access_key" "mlflow_user" {
  user = aws_iam_user.mlflow_user.name
}

# IAM policy for MLflow user
resource "aws_iam_user_policy" "mlflow_s3_access" {
  name = "alphapulse-mlflow-s3-access"
  user = aws_iam_user.mlflow_user.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.ml_artifacts.arn,
          "${aws_s3_bucket.ml_artifacts.arn}/*"
        ]
      }
    ]
  })
}

# Cost allocation tags
resource "aws_resourcegroups_group" "alphapulse" {
  name = "alphapulse-resources-${var.environment}"

  resource_query {
    query = jsonencode({
      ResourceTypeFilters = ["AWS::AllSupported"]
      TagFilters = [
        {
          Key    = "Project"
          Values = ["AlphaPulse"]
        },
        {
          Key    = "Environment"
          Values = [var.environment]
        }
      ]
    })
  }
}

# CloudWatch metrics for monitoring
resource "aws_cloudwatch_dashboard" "s3_metrics" {
  dashboard_name = "alphapulse-s3-metrics-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/S3", "NumberOfObjects", "StorageType", "AllStorageTypes", "BucketName", var.bucket_name],
            [".", "BucketSizeBytes", ".", "StandardStorage", ".", "."]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "S3 Bucket Metrics - ${var.bucket_name}"
        }
      }
    ]
  })
}