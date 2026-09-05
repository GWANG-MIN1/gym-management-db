"""sql/01_create_tables_pg.sql 과 api/models.py 가 같은 스키마를 만드는지 확인.

로컬 docker compose 는 SQL 파일로, AWS 배포는 ORM 의 create_all() 로 테이블을 만듭니다.
둘이 벌어지면 환경마다 스키마가 달라지므로(예전에는 SQL 6개 / 모델 3개였음)
CI 에서 컬럼·제약·인덱스를 비교해 차이를 잡습니다.
"""

import pathlib
import re

import pytest
from sqlalchemy import text

from database import engine

SQL_FILE = pathlib.Path(__file__).resolve().parents[2] / "sql" / "01_create_tables_pg.sql"
REF_SCHEMA = "sql_ref"  # SQL 파일을 적용해 볼 임시 스키마

COLUMNS_QUERY = """
    SELECT table_name, column_name, data_type,
           coalesce(character_maximum_length, -1), coalesce(numeric_precision, -1),
           coalesce(numeric_scale, -1), is_nullable, coalesce(column_default, '-'), is_identity
    FROM information_schema.columns
    WHERE table_schema = :schema
"""

CONSTRAINTS_QUERY = """
    SELECT conrelid::regclass::text, conname, pg_get_constraintdef(oid)
    FROM pg_constraint
    WHERE connamespace = :schema ::regnamespace
"""

INDEXES_QUERY = """
    SELECT tablename, indexname, indexdef
    FROM pg_indexes
    WHERE schemaname = :schema
"""


def _normalize(row, schema: str) -> tuple[str, ...]:
    """스키마 이름(sql_ref. / public.)을 지워 두 스키마의 정의를 비교 가능하게 만든다."""
    return tuple(re.sub(rf"\b{schema}\.", "", str(value)) for value in row)


def _snapshot(conn, query: str, schema: str) -> set[tuple[str, ...]]:
    rows = conn.execute(text(query), {"schema": schema}).fetchall()
    return {_normalize(row, schema) for row in rows}


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


@pytest.mark.parametrize(
    ("label", "query"),
    [("컬럼", COLUMNS_QUERY), ("제약", CONSTRAINTS_QUERY), ("인덱스", INDEXES_QUERY)],
)
def test_sql_and_orm_schemas_match(sql_reference_schema, label, query):
    with engine.connect() as conn:
        from_sql = _snapshot(conn, query, sql_reference_schema)
        from_orm = _snapshot(conn, query, "public")

    assert from_sql, f"{label} 정보를 읽지 못했습니다"
    assert from_sql == from_orm, (
        f"{label} 불일치\n"
        f"  SQL 파일에만: {sorted(from_sql - from_orm)}\n"
        f"  ORM 모델에만: {sorted(from_orm - from_sql)}"
    )
