# Lambda function for data drift detection
resource "aws_lambda_function" "data_drift_detector" {
  filename         = "data_drift_detector.zip"
  function_name    = "${var.project_name}-${var.environment}-data-drift-detector"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.9"
  timeout         = 300
  memory_size     = 1024

  environment {
    variables = {
      ENVIRONMENT         = var.environment
      S3_BUCKET          = var.embeddings_bucket
      TRAINING_SET_S3_KEY = var.training_set_key
      SNS_TOPIC_ARN      = var.alerts_topic_arn
    }
  }

  tags = var.tags
}

# IAM role for Lambda function
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-${var.environment}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# IAM policy for Lambda function
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-${var.environment}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.embeddings_bucket}",
          "arn:aws:s3:::${var.embeddings_bucket}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = var.alerts_topic_arn
      }
    ]
  })
}

# CloudWatch Event Rule to trigger Lambda nightly
resource "aws_cloudwatch_event_rule" "nightly_drift_check" {
  name                = "${var.project_name}-${var.environment}-nightly-drift-check"
  description         = "Trigger data drift check nightly"
  schedule_expression = "cron(0 2 * * ? *)"  # 2 AM UTC daily

  tags = var.tags
}

# CloudWatch Event Target
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.nightly_drift_check.name
  target_id = "DataDriftDetectorTarget"
  arn       = aws_lambda_function.data_drift_detector.arn
}

# Lambda permission for CloudWatch Events
resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.data_drift_detector.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.nightly_drift_check.arn
}

# S3 bucket for storing embeddings and training data
resource "aws_s3_bucket" "embeddings" {
  bucket = "${var.project_name}-${var.environment}-embeddings"
  tags   = var.tags
}

# S3 bucket versioning
resource "aws_s3_bucket_versioning" "embeddings_versioning" {
  bucket = aws_s3_bucket.embeddings.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "embeddings_encryption" {
  bucket = aws_s3_bucket.embeddings.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
