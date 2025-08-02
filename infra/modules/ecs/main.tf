# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-cluster"
  })
}

# CloudWatch Log Groups for ECS tasks
resource "aws_cloudwatch_log_group" "mlflow" {
  name              = "/ecs/${var.project_name}-${var.environment}/mlflow"
  retention_in_days = 7

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "train" {
  name              = "/ecs/${var.project_name}-${var.environment}/train"
  retention_in_days = 7

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "serve" {
  name              = "/ecs/${var.project_name}-${var.environment}/serve"
  retention_in_days = 7

  tags = var.tags
}

# IAM Role for ECS Task Execution
resource "aws_iam_role" "ecs_task_execution" {
  name = "${var.project_name}-${var.environment}-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# IAM Role for ECS Tasks (application permissions)
resource "aws_iam_role" "ecs_task" {
  name = "${var.project_name}-${var.environment}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# IAM Policy for ECS Tasks to access S3, Secrets Manager, X-Ray, etc.
resource "aws_iam_role_policy" "ecs_task_policy" {
  name = "${var.project_name}-${var.environment}-ecs-task-policy"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "${var.mlflow_artifacts_bucket_arn}",
          "${var.mlflow_artifacts_bucket_arn}/*",
          "${var.data_bucket_arn}",
          "${var.data_bucket_arn}/*",
          "${var.models_bucket_arn}",
          "${var.models_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          var.db_secret_arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords",
          "xray:GetSamplingRules",
          "xray:GetSamplingTargets",
          "xray:GetSamplingStatisticSummaries"
        ]
        Resource = "*"
      }
    ]
  })
}

# MLflow Task Definition
resource "aws_ecs_task_definition" "mlflow" {
  family                   = "${var.project_name}-${var.environment}-mlflow"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.fargate_cpu
  memory                   = var.fargate_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "mlflow"
      image = "${var.mlflow_image_uri}:latest"
      
      portMappings = [
        {
          containerPort = 5000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "MLFLOW_S3_ENDPOINT_URL"
          value = "https://s3.${var.aws_region}.amazonaws.com"
        },
        {
          name  = "AWS_DEFAULT_REGION"
          value = var.aws_region
        }
      ]

      secrets = [
        {
          name      = "MLFLOW_BACKEND_STORE_URI"
          valueFrom = "${var.db_secret_arn}:engine::"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.mlflow.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:5000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = var.tags
}

# Training Task Definition
resource "aws_ecs_task_definition" "train" {
  family                   = "${var.project_name}-${var.environment}-train"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.fargate_cpu
  memory                   = var.fargate_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "train"
      image = "${var.train_image_uri}:latest"

      environment = [
        {
          name  = "MLFLOW_TRACKING_URI"
          value = "http://${var.mlflow_service_name}.${var.cluster_name}.local:5000"
        },
        {
          name  = "AWS_DEFAULT_REGION"
          value = var.aws_region
        },
        {
          name  = "S3_BUCKET_DATA"
          value = var.data_bucket
        },
        {
          name  = "S3_BUCKET_MODELS"
          value = var.models_bucket
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.train.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = var.tags
}

# Serving Task Definition
resource "aws_ecs_task_definition" "serve" {
  family                   = "${var.project_name}-${var.environment}-serve"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.fargate_cpu
  memory                   = var.fargate_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "serve"
      image = "${var.serve_image_uri}:latest"
      
      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "MLFLOW_TRACKING_URI"
          value = "http://${var.mlflow_service_name}.${var.cluster_name}.local:5000"
        },
        {
          name  = "AWS_DEFAULT_REGION"
          value = var.aws_region
        },
        {
          name  = "MODEL_URI"
          value = "models:/code_model_fine_tuning_model/Production"
        },
        {
          name  = "_X_AMZN_TRACE_ID"
          value = "Root=1-5e1b4151-5ac6c58f2c2d2b4c1234567a"
        },
        {
          name  = "AWS_XRAY_TRACING_NAME"
          value = "${var.project_name}-${var.environment}-serve"
        },
        {
          name  = "AWS_XRAY_CONTEXT_MISSING"
          value = "LOG_ERROR"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.serve.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    },
    {
      name  = "xray-daemon"
      image = "amazon/aws-xray-daemon:latest"
      cpu   = 32
      memory = 256
      
      portMappings = [
        {
          containerPort = 2000
          protocol      = "udp"
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.serve.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "xray"
        }
      }
    }
  ])

  tags = var.tags
}

# MLflow ECS Service
resource "aws_ecs_service" "mlflow" {
  name            = "${var.project_name}-${var.environment}-mlflow"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.mlflow.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.mlflow_target_group_arn
    container_name   = "mlflow"
    container_port   = 5000
  }

  depends_on = [var.mlflow_target_group_arn]

  tags = var.tags
}

# Serving ECS Service
resource "aws_ecs_service" "serve" {
  name            = "${var.project_name}-${var.environment}-serve"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.serve.arn
  desired_count   = var.min_capacity
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.serve_target_group_arn
    container_name   = "serve"
    container_port   = 8000
  }

  depends_on = [var.serve_target_group_arn]

  tags = var.tags
}

# Auto Scaling Target for Serving Service
resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = var.max_capacity
  min_capacity       = var.min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.serve.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"

  tags = var.tags
}

# Auto Scaling Policy - Scale Up
resource "aws_appautoscaling_policy" "ecs_scale_up" {
  name               = "${var.project_name}-${var.environment}-scale-up"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = var.target_cpu_utilization
    scale_in_cooldown  = 300
    scale_out_cooldown = 300
  }
}
