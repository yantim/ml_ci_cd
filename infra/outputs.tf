output "mlflow_artifacts_bucket" {
  description = "S3 bucket for MLflow artifacts"
  value       = aws_s3_bucket.mlflow_artifacts.bucket
}

output "dvc_storage_bucket" {
  description = "S3 bucket for DVC data storage"
  value       = aws_s3_bucket.dvc_storage.bucket
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}
