output "rds_primary_endpoint" {
  description = "RDS primary instance endpoint (write)"
  value       = aws_db_instance.primary.endpoint
}

output "rds_replica_endpoint" {
  description = "RDS read replica endpoint (read-only)"
  value       = var.create_read_replica ? aws_db_instance.replica[0].endpoint : "read replica not created"
}

output "rds_port" {
  description = "PostgreSQL port"
  value       = aws_db_instance.primary.port
}

output "db_name" {
  description = "Database name"
  value       = aws_db_instance.primary.db_name
}

output "multi_az_enabled" {
  description = "Whether Multi-AZ is enabled"
  value       = aws_db_instance.primary.multi_az
}

output "storage_encrypted" {
  description = "Whether storage encryption is enabled"
  value       = aws_db_instance.primary.storage_encrypted
}

output "kms_key_arn" {
  description = "KMS key ARN used for RDS encryption"
  value       = var.storage_encrypted ? aws_kms_key.rds[0].arn : "encryption disabled"
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "cloudwatch_dashboard_url" {
  description = "CloudWatch 대시보드 URL"
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

output "db_secret_arn" {
  description = "Secrets Manager ARN — EC2_SSH_KEY 대신 SECRET_ARN GitHub Secret에 등록"
  value       = aws_secretsmanager_secret.db.arn
}

output "ecr_repository_url" {
  description = "ECR repository URL for the API image"
  value       = aws_ecr_repository.api.repository_url
}

output "ec2_public_ip" {
  description = "EC2 app server public IP (set as EC2_HOST secret in GitHub)"
  value       = aws_instance.app.public_ip
}

output "ec2_public_dns" {
  description = "EC2 app server public DNS"
  value       = aws_instance.app.public_dns
}
