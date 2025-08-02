terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Networking Module
module "networking" {
  source = "./modules/networking"

  project_name       = var.project_name
  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  tags               = var.tags
}

# Security Module
module "security" {
  source = "./modules/security"

  project_name      = var.project_name
  environment       = var.environment
  vpc_id            = module.networking.vpc_id
  vpc_cidr_block    = module.networking.vpc_cidr_block
  tags              = var.tags
}

# S3 Module
module "s3" {
  source = "./modules/s3"

  project_name = var.project_name
  environment  = var.environment
  tags         = var.tags
}

# ECR Module
module "ecr" {
  source = "./modules/ecr"

  project_name = var.project_name
  environment  = var.environment
  tags         = var.tags
}

# RDS Module
module "rds" {
  source = "./modules/rds"

  project_name            = var.project_name
  environment             = var.environment
  db_username             = var.db_username
  db_instance_class       = var.db_instance_class
  db_allocated_storage    = var.db_allocated_storage
  db_max_allocated_storage = var.db_max_allocated_storage
  db_subnet_group_name    = module.networking.db_subnet_group_name
  db_security_group_id    = module.security.rds_security_group_id
  tags                    = var.tags
}

# ALB Module
module "alb" {
  source = "./modules/alb"

  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.networking.vpc_id
  public_subnet_ids     = module.networking.public_subnet_ids
  alb_security_group_id = module.security.alb_security_group_id
  logs_bucket           = module.s3.logs_bucket
  domain_name           = var.domain_name
  subdomain_mlflow      = var.subdomain_mlflow
  subdomain_api         = var.subdomain_api
  tags                  = var.tags
}

# ECS Module
module "ecs" {
  source = "./modules/ecs"

  project_name                  = var.project_name
  environment                   = var.environment
  aws_region                    = var.aws_region
  fargate_cpu                   = var.fargate_cpu
  fargate_memory                = var.fargate_memory
  min_capacity                  = var.min_capacity
  max_capacity                  = var.max_capacity
  target_cpu_utilization        = var.target_cpu_utilization
  private_subnet_ids            = module.networking.private_subnet_ids
  ecs_security_group_id         = module.security.ecs_service_security_group_id
  mlflow_target_group_arn       = module.alb.mlflow_target_group_arn
  serve_target_group_arn        = module.alb.serve_target_group_arn
  mlflow_image_uri              = module.ecr.mlflow_repository_url
  train_image_uri               = module.ecr.train_repository_url
  serve_image_uri               = module.ecr.serve_repository_url
  mlflow_artifacts_bucket_arn   = module.s3.mlflow_artifacts_bucket_arn
  data_bucket_arn               = module.s3.data_bucket_arn
  data_bucket                   = module.s3.data_bucket
  models_bucket_arn             = module.s3.models_bucket_arn
  models_bucket                 = module.s3.models_bucket
  db_secret_arn                 = module.rds.db_secret_arn
  cluster_name                  = var.ecs_cluster_name
  tags                          = var.tags
}

# Monitoring Module
module "monitoring" {
  source = "./modules/monitoring"

  project_name         = var.project_name
  environment          = var.environment
  aws_region           = var.aws_region
  alb_arn_suffix       = split("/", module.alb.alb_arn)[1]
  cluster_name         = module.ecs.cluster_name
  mlflow_service_name  = module.ecs.mlflow_service_name
  serve_service_name   = module.ecs.serve_service_name
  db_instance_id       = module.rds.db_instance_id
  alert_email          = var.alert_email
  tags                 = var.tags
}

# Lambda Module for Data Drift Detection
module "lambda" {
  source = "./modules/lambda"

  project_name      = var.project_name
  environment       = var.environment
  embeddings_bucket = "${var.project_name}-${var.environment}-embeddings"
  alerts_topic_arn  = module.monitoring.sns_topic_arn
  tags              = var.tags
}
