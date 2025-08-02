# Networking Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.networking.private_subnet_ids
}

# S3 Outputs
output "mlflow_artifacts_bucket" {
  description = "S3 bucket for MLflow artifacts"
  value       = module.s3.mlflow_artifacts_bucket
}

output "dvc_storage_bucket" {
  description = "S3 bucket for DVC data storage"
  value       = module.s3.dvc_storage_bucket
}

output "data_bucket" {
  description = "S3 bucket for data storage"
  value       = module.s3.data_bucket
}

output "models_bucket" {
  description = "S3 bucket for model artifacts"
  value       = module.s3.models_bucket
}

output "logs_bucket" {
  description = "S3 bucket for logs"
  value       = module.s3.logs_bucket
}

# ECR Outputs
output "train_repository_url" {
  description = "URL of the training ECR repository"
  value       = module.ecr.train_repository_url
}

output "serve_repository_url" {
  description = "URL of the serving ECR repository"
  value       = module.ecr.serve_repository_url
}

output "mlflow_repository_url" {
  description = "URL of the MLflow ECR repository"
  value       = module.ecr.mlflow_repository_url
}

# RDS Outputs
output "db_instance_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.db_instance_endpoint
}

output "db_secret_arn" {
  description = "ARN of the database secret in Secrets Manager"
  value       = module.rds.db_secret_arn
}

# ECS Outputs
output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.ecs.cluster_name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = module.ecs.cluster_arn
}

# ALB Outputs
output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = module.alb.alb_dns_name
}

output "mlflow_url" {
  description = "URL for MLflow UI"
  value       = module.alb.mlflow_url
}

output "api_url" {
  description = "URL for API endpoints"
  value       = module.alb.api_url
}

# Monitoring Outputs
output "dashboard_url" {
  description = "URL of the CloudWatch dashboard"
  value       = module.monitoring.dashboard_url
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for alerts"
  value       = module.monitoring.sns_topic_arn
}

# General Outputs
output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "project_name" {
  description = "Project name"
  value       = var.project_name
}
