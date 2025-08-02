variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "embeddings_bucket" {
  description = "S3 bucket for storing embeddings data"
  type        = string
}

variable "training_set_key" {
  description = "S3 key for training set embeddings"
  type        = string
  default     = "training_embeddings/training_set.json"
}

variable "alerts_topic_arn" {
  description = "SNS topic ARN for alerts"
  type        = string
}

variable "tags" {
  description = "A map of tags to assign to the resource"
  type        = map(string)
  default     = {}
}
