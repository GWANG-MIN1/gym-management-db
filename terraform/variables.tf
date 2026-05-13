variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-2"
}

variable "project_name" {
  description = "Project name used as resource name prefix"
  type        = string
  default     = "gym-mgmt"
}

variable "environment" {
  description = "Deployment environment (dev / prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "environment must be 'dev' or 'prod'."
  }
}

# ─── Database ────────────────────────────────────────────────
variable "db_username" {
  description = "RDS master username"
  type        = string
  default     = "gymadmin"
  sensitive   = true
}

variable "db_password" {
  description = "RDS master password (min 8 chars, no @, /, space)"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro" # free-tier eligible
}

variable "db_allocated_storage" {
  description = "Initial allocated storage in GiB"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Maximum storage autoscaling ceiling in GiB"
  type        = number
  default     = 100
}

# ─── Stage 4: High Availability ──────────────────────────────
variable "multi_az" {
  description = "Enable Multi-AZ standby (Stage 4)"
  type        = bool
  default     = false
}

variable "create_read_replica" {
  description = "Create a read replica in a separate AZ (Stage 4)"
  type        = bool
  default     = false
}

# ─── Stage 4: Encryption ─────────────────────────────────────
variable "storage_encrypted" {
  description = "Enable KMS storage encryption (Stage 4)"
  type        = bool
  default     = false
}

# ─── EC2 ─────────────────────────────────────────────────────
variable "ec2_key_name" {
  description = "EC2 key pair name for SSH access"
  type        = string
  default     = "gym-mgmt-key"
}

# ─── Monitoring ───────────────────────────────────────────────
variable "alert_email" {
  description = "Email address to receive CloudWatch alarm notifications"
  type        = string
  default     = "gwangminions@gmail.com"
}
