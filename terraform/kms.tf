# ─── KMS (Stage 4: storage_encrypted = true 일 때만 생성) ────
resource "aws_kms_key" "rds" {
  count = var.storage_encrypted ? 1 : 0

  description             = "KMS CMK for RDS storage encryption — ${local.name}"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = { Name = "${local.name}-rds-kms" }
}

resource "aws_kms_alias" "rds" {
  count = var.storage_encrypted ? 1 : 0

  name          = "alias/${local.name}-rds"
  target_key_id = aws_kms_key.rds[0].key_id
}
