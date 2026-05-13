import json
import os

import boto3
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


def _get_database_url() -> str:
    # 로컬 개발: DATABASE_URL 환경변수 직접 사용
    if url := os.getenv("DATABASE_URL"):
        return url

    # EC2 배포: Secrets Manager에서 DB 정보 가져오기
    # EC2 IAM 롤이 자동으로 인증 처리 (크레덴셜 코드에 없음)
    secret_arn = os.getenv("SECRET_ARN")
    region = os.getenv("AWS_REGION", "ap-northeast-2")

    client = boto3.client("secretsmanager", region_name=region)
    secret = json.loads(
        client.get_secret_value(SecretId=secret_arn)["SecretString"]
    )

    return (
        f"postgresql://{secret['username']}:{secret['password']}"
        f"@{secret['host']}:{secret['port']}/{secret['dbname']}"
    )


DATABASE_URL = _get_database_url()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
