# Random password for database
resource "random_password" "db_password" {
  length  = 16
  special = true
}

# Store password in AWS Secrets Manager
resource "aws_secretsmanager_secret" "db_password" {
  name                    = "${var.project_name}-${var.environment}-db-password"
  description             = "Database password for MLflow PostgreSQL"
  recovery_window_in_days = 0  # Force delete for dev environments

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_password.id
  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db_password.result
    engine   = "postgres"
    host     = aws_db_instance.mlflow.endpoint
    port     = aws_db_instance.mlflow.port
    dbname   = aws_db_instance.mlflow.db_name
  })
}

# RDS PostgreSQL instance for MLflow tracking
resource "aws_db_instance" "mlflow" {
  identifier = "${var.project_name}-${var.environment}-mlflow-db"

  # Engine configuration
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.db_instance_class

  # Storage configuration
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true

  # Database configuration
  db_name  = "mlflow"
  username = var.db_username
  password = random_password.db_password.result

  # Network configuration
  db_subnet_group_name   = var.db_subnet_group_name
  vpc_security_group_ids = [var.db_security_group_id]
  publicly_accessible    = false

  # Backup configuration
  backup_retention_period = var.backup_retention_period
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  # Monitoring and performance
  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_monitoring.arn
  
  performance_insights_enabled = true
  performance_insights_retention_period = 7

  # Deletion protection
  deletion_protection = var.environment == "prod" ? true : false
  skip_final_snapshot = var.environment == "prod" ? false : true
  final_snapshot_identifier = var.environment == "prod" ? "${var.project_name}-${var.environment}-mlflow-db-final-snapshot" : null

  # Enable automated minor version upgrades
  auto_minor_version_upgrade = true

  # Enable Multi-AZ for production
  multi_az = var.environment == "prod" ? true : false

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-mlflow-db"
  })
}

# IAM role for RDS enhanced monitoring
resource "aws_iam_role" "rds_monitoring" {
  name = "${var.project_name}-${var.environment}-rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# CloudWatch Log Groups for RDS
resource "aws_cloudwatch_log_group" "rds_postgresql" {
  name              = "/aws/rds/instance/${aws_db_instance.mlflow.identifier}/postgresql"
  retention_in_days = 7

  tags = var.tags
}

# RDS parameter group for performance tuning
resource "aws_db_parameter_group" "mlflow" {
  family = "postgres15"
  name   = "${var.project_name}-${var.environment}-mlflow-params"

  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }

  parameter {
    name  = "log_statement"
    value = "all"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"  # Log queries taking more than 1 second
  }

  parameter {
    name  = "max_connections"
    value = "100"
  }

  tags = var.tags
}

# Attach parameter group to RDS instance
resource "aws_db_instance" "mlflow_with_params" {
  count = 0  # This is just to show how to attach parameter group
  
  # ... other configuration would be same as above
  parameter_group_name = aws_db_parameter_group.mlflow.name
}
