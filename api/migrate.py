"""스키마 마이그레이션 실행 (Alembic).

  - 빈 DB          : 0001(예전 스키마) → 0002(현재 스키마) 를 모두 적용
  - 기존 DB        : 테이블은 있는데 alembic_version 이 없으면(= 예전 create_all 로 만든 DB)
                     0001 로 stamp 한 뒤 0002 만 적용
  - 이미 최신 DB   : 아무것도 하지 않음

예전에는 앱 시작 시 create_all() 을 호출했지만, create_all 은 '없는 테이블'만 만들고
기존 테이블의 기본값·제약·인덱스는 손대지 않는다. 그래서 예전 스키마 위에 새 버전을
올리면 등록 요청이 전부 실패했다(created_at 기본값 없음 → NOT NULL 위반).
"""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.engine import Engine

from database import engine as default_engine

BASE_DIR = Path(__file__).resolve().parent
LEGACY_BASELINE = "0001"


def _alembic_config(target: Engine) -> Config:
    config = Config(str(BASE_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BASE_DIR / "migrations"))
    # env.py 가 database / models 를 임포트할 수 있도록 (실행 위치와 무관하게)
    config.set_main_option("prepend_sys_path", str(BASE_DIR))
    config.attributes["engine"] = target
    return config


def run_migrations(target: Engine | None = None) -> None:
    target = target or default_engine
    config = _alembic_config(target)

    with target.connect() as connection:
        tables = set(inspect(connection).get_table_names())

    if "alembic_version" not in tables and "member" in tables:
        # 마이그레이션 이력이 없는 기존 DB — 예전 스키마 기준으로 이력을 맞춘다
        command.stamp(config, LEGACY_BASELINE)

    command.upgrade(config, "head")
