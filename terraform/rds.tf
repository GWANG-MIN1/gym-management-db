# ─── Parameter Group ─────────────────────────────────────────
resource "aws_db_parameter_group" "main" {
  name   = "${local.name}-pg15"
  family = "postgres15"

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"  # 1초 이상 쿼리 로깅
  }

  tags = { Name = "${local.name}-pg15" }
}

# ─── IAM Role for Enhanced Monitoring ────────────────────────
resource "aws_iam_role" "rds_monitoring" {
  name = "${local.name}-rds-monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "monitoring.rds.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# ─── RDS Primary ─────────────────────────────────────────────
resource "aws_db_instance" "primary" {
  identifier = "${local.name}-primary"

  # Engine
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.db_instance_class

  # Storage
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = var.storage_encrypted
  kms_key_id            = var.storage_encrypted ? aws_kms_key.rds[0].arn : null

  # Database
  db_name  = "gymdb"
  username = var.db_username
  password = var.db_password

  # Network
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  # Stage 4: Multi-AZ — 같은 Region 내 다른 AZ에 Standby 자동 생성
  # Standby는 동기 복제(Synchronous Replication)로 항상 최신 상태 유지
  # Primary 장애 시 자동 Failover (보통 60~120초)
  multi_az = var.multi_az

  # Backup
  backup_retention_period = var.environment == "prod" ? 7 : 1
  backup_window           = "18:00-19:00"  # UTC (KST 03:00-04:00)
  maintenance_window      = "Mon:19:00-Mon:20:00"

  # Enhanced Monitoring (60초 간격)
  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_monitoring.arn

  parameter_group_name = aws_db_parameter_group.main.name

  # prod: 삭제 보호 + 최종 스냅샷 / dev: 빠른 삭제
  deletion_protection       = var.environment == "prod" ? true : false
  skip_final_snapshot       = var.environment == "prod" ? false : true
  final_snapshot_identifier = var.environment == "prod" ? "${local.name}-final-snapshot" : null

  apply_immediately = var.environment == "prod" ? false : true

  tags = { Name = "${local.name}-primary", Role = "primary" }
}

# ─── Read Replica (Stage 4) ───────────────────────────────────
# Read Replica는 비동기 복제(Asynchronous Replication)
# 읽기 쿼리 부하 분산 목적 (통계/리포트 쿼리 → Replica로 라우팅)
# Multi-AZ Standby와는 다름: Replica는 직접 쿼리 가능, Standby는 불가
resource "aws_db_instance" "replica" {
  count = var.create_read_replica ? 1 : 0

  identifier          = "${local.name}-replica"
  replicate_source_db = aws_db_instance.primary.identifier

  instance_class    = var.db_instance_class
  storage_encrypted = var.storage_encrypted
  kms_key_id        = var.storage_encrypted ? aws_kms_key.rds[0].arn : null

  # Primary와 다른 AZ에 배치하여 AZ 장애 내성 확보
  availability_zone      = "${var.aws_region}b"
  publicly_accessible    = false
  vpc_security_group_ids = [aws_security_group.rds.id]

  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_monitoring.arn

  skip_final_snapshot = true
  apply_immediately   = true

  tags = { Name = "${local.name}-replica", Role = "read-replica" }
}
