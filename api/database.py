"""DB 연결 설정.

접속 정보 출처
  - 로컬/CI : DATABASE_URL 환경변수 (읽기용은 선택적으로 READ_DATABASE_URL)
  - EC2     : Secrets Manager (EC2 IAM 롤이 인증 처리 — 코드에 크레덴셜 없음)

읽기/쓰기 세션 분리
  쓰기(및 최신 값이 필요한 조회)는 get_db(), 단순 목록 조회는 get_read_db() 를 씁니다.
  Read Replica 정보(replica_host)가 시크릿에 있으면 읽기 세션만 Replica 로 연결됩니다.
  Terraform 에서 create_read_replica = true 로 Replica 를 만들어도, 애플리케이션이
  별도 연결을 쓰지 않으면 읽기 부하는 분산되지 않기 때문에 연결을 나눠 둡니다.
"""

import json
import os
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


def _url_from_secret(secret: dict, host: str) -> str:
    # 비밀번호에 URL 예약문자가 있어도 깨지지 않도록 인코딩
    return (
        f"postgresql://{quote_plus(secret['username'])}:{quote_plus(secret['password'])}"
        f"@{host}:{secret['port']}/{secret['dbname']}"
    )


def _resolve_urls() -> tuple[str, str]:
    """(쓰기 URL, 읽기 URL) 을 반환한다. Replica 가 없으면 둘이 같다."""
    if url := os.getenv("DATABASE_URL"):
        return url, os.getenv("READ_DATABASE_URL") or url

    import boto3  # AWS 배포 경로에서만 필요 — 로컬/CI 는 DATABASE_URL 로 끝난다

    secret_name = os.getenv("SECRET_NAME", "gym-mgmt-dev/db-credentials")
    region = os.getenv("AWS_REGION", "ap-northeast-2")

    client = boto3.client("secretsmanager", region_name=region)
    secret = json.loads(client.get_secret_value(SecretId=secret_name)["SecretString"])

    write_url = _url_from_secret(secret, secret["host"])
    replica_host = secret.get("replica_host")
    read_url = _url_from_secret(secret, replica_host) if replica_host else write_url
    return write_url, read_url


DATABASE_URL, READ_DATABASE_URL = _resolve_urls()
READ_REPLICA_ENABLED = READ_DATABASE_URL != DATABASE_URL

# 커넥션 풀: 컨테이너 1대가 최대 15개(5 + overflow 10) 사용.
# CloudWatch DatabaseConnections 알람 임계값(20)을 넘지 않도록 기본값을 유지한다.
_ENGINE_OPTIONS = {
    "pool_size": 5,
    "max_overflow": 10,
    "pool_pre_ping": True,  # RDS 유휴 커넥션 끊김 대비
    "pool_recycle": 1800,
}

engine = create_engine(DATABASE_URL, **_ENGINE_OPTIONS)
read_engine = engine if not READ_REPLICA_ENABLED else create_engine(
    READ_DATABASE_URL, **_ENGINE_OPTIONS
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
ReadSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=read_engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """쓰기 세션 (Primary)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_read_db():
    """읽기 전용 세션 (Replica 가 있으면 Replica)."""
    db = ReadSessionLocal()
    try:
        yield db
    finally:
        db.close()
