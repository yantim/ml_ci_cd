output "mlflow_artifacts_bucket" {
  description = "S3 bucket name for MLflow artifacts"
  value       = aws_s3_bucket.mlflow_artifacts.bucket
}

output "mlflow_artifacts_bucket_arn" {
  description = "S3 bucket ARN for MLflow artifacts"
  value       = aws_s3_bucket.mlflow_artifacts.arn
}

output "dvc_storage_bucket" {
  description = "S3 bucket name for DVC storage"
  value       = aws_s3_bucket.dvc_storage.bucket
}

output "dvc_storage_bucket_arn" {
  description = "S3 bucket ARN for DVC storage"
  value       = aws_s3_bucket.dvc_storage.arn
}

output "data_bucket" {
  description = "S3 bucket name for data storage"
  value       = aws_s3_bucket.data.bucket
}

output "data_bucket_arn" {
  description = "S3 bucket ARN for data storage"
  value       = aws_s3_bucket.data.arn
}

output "models_bucket" {
  description = "S3 bucket name for model artifacts"
  value       = aws_s3_bucket.models.bucket
}

output "models_bucket_arn" {
  description = "S3 bucket ARN for model artifacts"
  value       = aws_s3_bucket.models.arn
}

output "logs_bucket" {
  description = "S3 bucket name for logs"
  value       = aws_s3_bucket.logs.bucket
}

output "logs_bucket_arn" {
  description = "S3 bucket ARN for logs"
  value       = aws_s3_bucket.logs.arn
}
