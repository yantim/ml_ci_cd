output "lambda_function_arn" {
  description = "ARN of the data drift detection Lambda function"
  value       = aws_lambda_function.data_drift_detector.arn
}

output "lambda_function_name" {
  description = "Name of the data drift detection Lambda function"
  value       = aws_lambda_function.data_drift_detector.function_name
}

output "embeddings_bucket_name" {
  description = "Name of the S3 bucket for embeddings"
  value       = aws_s3_bucket.embeddings.id
}

output "embeddings_bucket_arn" {
  description = "ARN of the S3 bucket for embeddings"
  value       = aws_s3_bucket.embeddings.arn
}
