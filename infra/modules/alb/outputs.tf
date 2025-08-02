output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the load balancer"
  value       = aws_lb.main.zone_id
}

output "alb_arn" {
  description = "ARN of the load balancer"
  value       = aws_lb.main.arn
}

output "mlflow_target_group_arn" {
  description = "ARN of the MLflow target group"
  value       = aws_lb_target_group.mlflow.arn
}

output "serve_target_group_arn" {
  description = "ARN of the serving target group"
  value       = aws_lb_target_group.serve.arn
}

output "certificate_arn" {
  description = "ARN of the ACM certificate"
  value       = var.domain_name != "" ? aws_acm_certificate_validation.main[0].certificate_arn : null
}

output "mlflow_url" {
  description = "URL for MLflow UI"
  value = var.domain_name != "" ? (
    "https://${var.subdomain_mlflow}.${var.domain_name}"
  ) : (
    "http://${aws_lb.main.dns_name}"
  )
}

output "api_url" {
  description = "URL for API endpoints"
  value = var.domain_name != "" ? (
    "https://${var.subdomain_api}.${var.domain_name}"
  ) : (
    "http://${aws_lb.main.dns_name}"
  )
}
