output "cluster_id" {
  description = "ID of the ECS cluster"
  value       = aws_ecs_cluster.main.id
}

output "cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "task_execution_role_arn" {
  description = "ARN of the task execution IAM role"
  value       = aws_iam_role.ecs_task_execution.arn
}

output "task_role_arn" {
  description = "ARN of the task IAM role"
  value       = aws_iam_role.ecs_task.arn
}

output "mlflow_service_name" {
  description = "Name of the MLflow service"
  value       = aws_ecs_service.mlflow.name
}

output "serve_service_name" {
  description = "Name of the serving service"
  value       = aws_ecs_service.serve.name
}

output "train_task_definition_arn" {
  description = "ARN of the training task definition"
  value       = aws_ecs_task_definition.train.arn
}
