terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# S3 bucket for MLflow artifacts
resource "aws_s3_bucket" "mlflow_artifacts" {
  bucket = "${var.project_name}-mlflow-artifacts-${random_string.suffix.result}"
}

resource "aws_s3_bucket_versioning" "mlflow_artifacts" {
  bucket = aws_s3_bucket.mlflow_artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "mlflow_artifacts" {
  bucket = aws_s3_bucket.mlflow_artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 bucket for DVC data storage
resource "aws_s3_bucket" "dvc_storage" {
  bucket = "${var.project_name}-dvc-storage-${random_string.suffix.result}"
}

resource "aws_s3_bucket_versioning" "dvc_storage" {
  bucket = aws_s3_bucket.dvc_storage.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}
