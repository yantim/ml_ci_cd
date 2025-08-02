terraform {
  backend "s3" {
    # Update these values for your environment
    bucket         = "your-terraform-state-bucket"
    key            = "ml-ci-cd/terraform.tfstate"
    region         = "us-west-2"
    
    # DynamoDB table for state locking
    dynamodb_table = "terraform-state-locks"
    encrypt        = true
    
    # Optional: Use AWS profiles or IAM roles
    # profile = "your-aws-profile"
  }
}

# DynamoDB table for Terraform state locking
resource "aws_dynamodb_table" "terraform_locks" {
  name           = "terraform-state-locks"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = var.tags
}

# S3 bucket for Terraform state (create this manually first or use a separate bootstrap script)
# resource "aws_s3_bucket" "terraform_state" {
#   bucket = "your-terraform-state-bucket"
#   tags   = var.tags
# }
#
# resource "aws_s3_bucket_versioning" "terraform_state" {
#   bucket = aws_s3_bucket.terraform_state.id
#   versioning_configuration {
#     status = "Enabled"
#   }
# }
#
# resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
#   bucket = aws_s3_bucket.terraform_state.id
#
#   rule {
#     apply_server_side_encryption_by_default {
#       sse_algorithm = "AES256"
#     }
#   }
# }
