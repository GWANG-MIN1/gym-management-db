"""Alembic 환경 설정.

접속 정보는 api/database.py 한 곳에서만 관리한다(로컬은 DATABASE_URL 환경변수,
EC2 는 Secrets Manager). 다른 DB 를 대상으로 실행해야 할 때는
Config.attributes["engine"] 에 엔진을 넣어 전달한다(테스트에서 사용).
"""

from alembic import context

from database import DATABASE_URL, Base
from database import engine as default_engine

import models  # noqa: F401  — Base.metadata 에 테이블을 등록하기 위한 임포트

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = context.config.attributes.get("engine") or default_engine
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
