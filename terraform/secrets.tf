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

  # replica_host 는 Read Replica 를 만든 경우에만 포함된다.
  # API(api/database.py)는 이 값이 있을 때만 읽기 전용 커넥션을 Replica 로 연결한다.
  secret_string = jsonencode(merge(
    {
      username = var.db_username
      password = var.db_password
      host     = aws_db_instance.primary.address
      port     = aws_db_instance.primary.port
      dbname   = aws_db_instance.primary.db_name
    },
    var.create_read_replica ? { replica_host = aws_db_instance.replica[0].address } : {}
  ))
}
