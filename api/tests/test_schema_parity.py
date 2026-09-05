"""sql/01_create_tables_pg.sql 과 api/models.py 가 같은 스키마를 만드는지 확인.

로컬 docker compose 는 SQL 파일로 테이블을 만들고 테스트는 ORM 정의를 쓴다.
둘이 벌어지면 환경마다 스키마가 달라지므로(예전에는 SQL 6개 / 모델 3개였음)
CI 에서 컬럼·제약·인덱스를 비교해 차이를 잡는다.
배포 경로(마이그레이션 결과)와의 비교는 test_migration_from_legacy.py 가 담당한다.
"""

import pathlib

import pytest
from sqlalchemy import text

from database import engine
from tests.schema_snapshot import SNAPSHOT_QUERIES, diff_message, snapshot

SQL_FILE = pathlib.Path(__file__).resolve().parents[2] / "sql" / "01_create_tables_pg.sql"
REF_SCHEMA = "sql_ref"  # SQL 파일을 적용해 볼 임시 스키마


@pytest.fixture
def sql_reference_schema():
    with engine.begin() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {REF_SCHEMA} CASCADE"))
        conn.execute(text(f"CREATE SCHEMA {REF_SCHEMA}"))
        conn.execute(text(f"SET LOCAL search_path TO {REF_SCHEMA}"))
        conn.execute(text(SQL_FILE.read_text()))
    yield REF_SCHEMA
    with engine.begin() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {REF_SCHEMA} CASCADE"))


@pytest.mark.parametrize(("label", "query"), list(SNAPSHOT_QUERIES.items()))
def test_sql_and_orm_schemas_match(sql_reference_schema, label, query):
    with engine.connect() as conn:
        from_sql = snapshot(conn, query, sql_reference_schema)
        from_orm = snapshot(conn, query, "public")

    assert from_sql, f"{label} 정보를 읽지 못했습니다"
    assert from_sql == from_orm, diff_message(label, "SQL 파일", from_sql, "ORM 모델", from_orm)
