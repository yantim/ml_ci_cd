output "train_repository_url" {
  description = "URL of the training ECR repository"
  value       = aws_ecr_repository.train.repository_url
}

output "train_repository_name" {
  description = "Name of the training ECR repository"
  value       = aws_ecr_repository.train.name
}

output "serve_repository_url" {
  description = "URL of the serving ECR repository"
  value       = aws_ecr_repository.serve.repository_url
}

output "serve_repository_name" {
  description = "Name of the serving ECR repository"
  value       = aws_ecr_repository.serve.name
}

output "mlflow_repository_url" {
  description = "URL of the MLflow ECR repository"
  value       = aws_ecr_repository.mlflow.repository_url
}

output "mlflow_repository_name" {
  description = "Name of the MLflow ECR repository"
  value       = aws_ecr_repository.mlflow.name
}
