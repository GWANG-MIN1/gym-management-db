"""스키마 비교용 헬퍼.

정의가 세 곳에 있다 — sql/01_create_tables_pg.sql(로컬 초기화),
api/models.py(ORM), api/migrations(배포 시 적용). 셋이 벌어지면 환경마다 스키마가
달라지므로 컬럼·제약·인덱스를 같은 형태로 뽑아 비교한다.
(alembic 이력 테이블은 비교 대상이 아니므로 제외)
"""

import re

from sqlalchemy import text

COLUMNS_QUERY = """
    SELECT table_name, column_name, data_type,
           coalesce(character_maximum_length, -1), coalesce(numeric_precision, -1),
           coalesce(numeric_scale, -1), is_nullable, coalesce(column_default, '-'), is_identity
    FROM information_schema.columns
    WHERE table_schema = :schema AND table_name <> 'alembic_version'
"""

CONSTRAINTS_QUERY = """
    SELECT conrelid::regclass::text, conname, pg_get_constraintdef(oid)
    FROM pg_constraint
    WHERE connamespace = :schema ::regnamespace
      AND conrelid::regclass::text NOT LIKE '%alembic_version'
"""

INDEXES_QUERY = """
    SELECT tablename, indexname, indexdef
    FROM pg_indexes
    WHERE schemaname = :schema AND tablename <> 'alembic_version'
"""

SNAPSHOT_QUERIES = {
    "컬럼": COLUMNS_QUERY,
    "제약": CONSTRAINTS_QUERY,
    "인덱스": INDEXES_QUERY,
}


def _normalize(row, schema: str) -> tuple[str, ...]:
    """스키마 이름(public. / sql_ref.)을 지워 서로 다른 스키마의 정의를 비교 가능하게 만든다."""
    return tuple(re.sub(rf"\b{schema}\.", "", str(value)) for value in row)


def snapshot(conn, query: str, schema: str = "public") -> set[tuple[str, ...]]:
    rows = conn.execute(text(query), {"schema": schema}).fetchall()
    return {_normalize(row, schema) for row in rows}


def diff_message(label: str, left_name: str, left: set, right_name: str, right: set) -> str:
    return (
        f"{label} 불일치\n"
        f"  {left_name} 에만: {sorted(left - right)}\n"
        f"  {right_name} 에만: {sorted(right - left)}"
    )
