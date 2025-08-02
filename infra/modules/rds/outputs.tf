output "db_instance_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.mlflow.endpoint
}

output "db_instance_port" {
  description = "RDS instance port"
  value       = aws_db_instance.mlflow.port
}

output "db_instance_name" {
  description = "RDS instance database name"
  value       = aws_db_instance.mlflow.db_name
}

output "db_instance_username" {
  description = "RDS instance username"
  value       = aws_db_instance.mlflow.username
  sensitive   = true
}

output "db_instance_id" {
  description = "RDS instance ID"
  value       = aws_db_instance.mlflow.id
}

output "db_secret_arn" {
  description = "ARN of the secrets manager secret"
  value       = aws_secretsmanager_secret.db_password.arn
}

output "db_secret_name" {
  description = "Name of the secrets manager secret"
  value       = aws_secretsmanager_secret.db_password.name
}
