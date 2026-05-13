# ─── Secrets Manager ──────────────────────────────────────────
resource "aws_secretsmanager_secret" "db" {
  name        = "${local.name}/db-credentials"
  description = "Gym management DB credentials"

  # dev: 즉시 삭제 가능 (terraform destroy 재실행 대비)
  recovery_window_in_days = 0

  tags = { Name = "${local.name}/db-credentials" }
}

resource "aws_secretsmanager_secret_version" "db" {
  secret_id = aws_secretsmanager_secret.db.id

  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password
    host     = aws_db_instance.primary.address
    port     = aws_db_instance.primary.port
    dbname   = aws_db_instance.primary.db_name
  })
}
