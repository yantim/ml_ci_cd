variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "fargate_cpu" {
  description = "Fargate instance CPU units to provision (1 vCPU = 1024 CPU units)"
  type        = number
  default     = 1024
}

variable "fargate_memory" {
  description = "Fargate instance memory to provision (in MiB)"
  type        = number
  default     = 2048
}

variable "min_capacity" {
  description = "Minimum number of tasks"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "Maximum number of tasks"
  type        = number
  default     = 10
}

variable "target_cpu_utilization" {
  description = "Target CPU utilization for auto scaling"
  type        = number
  default     = 70
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs"
  type        = list(string)
}

variable "ecs_security_group_id" {
  description = "Security group ID for ECS services"
  type        = string
}

variable "mlflow_target_group_arn" {
  description = "ARN of the MLflow target group"
  type        = string
}

variable "serve_target_group_arn" {
  description = "ARN of the serving target group"
  type        = string
}

variable "mlflow_image_uri" {
  description = "URI of the MLflow container image"
  type        = string
}

variable "train_image_uri" {
  description = "URI of the training container image"
  type        = string
}

variable "serve_image_uri" {
  description = "URI of the serving container image"
  type        = string
}

variable "mlflow_artifacts_bucket_arn" {
  description = "ARN of the MLflow artifacts S3 bucket"
  type        = string
}

variable "data_bucket_arn" {
  description = "ARN of the data S3 bucket"
  type        = string
}

variable "data_bucket" {
  description = "Name of the data S3 bucket"
  type        = string
}

variable "models_bucket_arn" {
  description = "ARN of the models S3 bucket"
  type        = string
}

variable "models_bucket" {
  description = "Name of the models S3 bucket"
  type        = string
}

variable "db_secret_arn" {
  description = "ARN of the database secret"
  type        = string
}

variable "mlflow_service_name" {
  description = "Name of the MLflow service"
  type        = string
  default     = "mlflow"
}

variable "cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
}

variable "tags" {
  description = "A map of tags to assign to the resource"
  type        = map(string)
  default     = {}
}
