"""현재 스키마로 업그레이드 — 테이블 3개 추가, 기본값·제약·인덱스 정리

예전 스키마에서 바뀐 것

  1. Exercise / Workout_Log / Payment 테이블 추가
  2. created_at 등에 DB 기본값(CURRENT_DATE) 부여.
     예전 테이블에는 기본값이 없고 NOT NULL 이라, 값을 보내지 않는 현재 API 의
     등록 요청이 NOT NULL 위반으로 전부 실패했다.
  3. PT 예약 중복 방지 제약을 부분 유니크 인덱스로 교체.
     예전의 일반 UNIQUE 제약은 취소(CANCELLED)된 예약도 슬롯을 계속 점유해
     취소 후 같은 시간에 다시 예약하면 409 가 났다. 회원 기준 중복 방지도 추가.
  4. 예약 시각 형식 CHECK, FK 제약 이름 통일, 조회용 인덱스 추가
  5. SERIAL PK 를 GENERATED ALWAYS AS IDENTITY 로 전환 (현재 모델·SQL 스키마와 일치)

이 리비전은 여러 번 실행해도 안전하도록(이미 적용된 부분은 건너뛰도록) 작성했다.
운영 DB 는 "예전 3개 테이블 + create_all 이 만든 새 3개 테이블"이 섞여 있을 수 있다.

Revision ID: 0002
Revises: 0001
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SESSION_TIME_REGEX = r"^([01][0-9]|2[0-3]):[0-5][0-9]$"

# (테이블, 컬럼, 기본값)
COLUMN_DEFAULTS = [
    ("member", "join_date", "CURRENT_DATE"),
    ("member", "remaining_pt_count", "0"),
    ("member", "created_at", "CURRENT_DATE"),
    ("trainer", "created_at", "CURRENT_DATE"),
    ("exercise", "created_at", "CURRENT_DATE"),
    ("pt_session", "status", "'SCHEDULED'"),
    ("pt_session", "created_at", "CURRENT_DATE"),
    ("workout_log", "log_date", "CURRENT_DATE"),
    ("workout_log", "created_at", "CURRENT_DATE"),
    ("payment", "payment_date", "CURRENT_DATE"),
    ("payment", "created_at", "CURRENT_DATE"),
]

ALL_TABLES = ("member", "trainer", "exercise", "pt_session", "workout_log", "payment")

# (테이블, 예전 이름, 새 이름)
FK_RENAMES = [
    ("pt_session", "pt_session_member_id_fkey", "fk_pt_session_member"),
    ("pt_session", "pt_session_trainer_id_fkey", "fk_pt_session_trainer"),
    ("workout_log", "workout_log_member_id_fkey", "fk_workout_member"),
    ("workout_log", "workout_log_exercise_id_fkey", "fk_workout_exercise"),
    ("payment", "payment_member_id_fkey", "fk_payment_member"),
]

# (테이블, 제약 이름, 조건)
CHECK_CONSTRAINTS = [
    ("member", "ck_member_gender", "gender IN ('M', 'F')"),
    ("member", "ck_member_pt_count", "remaining_pt_count >= 0"),
    ("trainer", "ck_trainer_career", "career_year >= 0"),
    ("pt_session", "ck_session_status", "status IN ('SCHEDULED', 'COMPLETED', 'CANCELLED')"),
    ("pt_session", "ck_session_time_format", f"session_time ~ '{SESSION_TIME_REGEX}'"),
    ("workout_log", "ck_workout_weight", "weight IS NULL OR weight > 0"),
    ("workout_log", "ck_workout_sets", "sets > 0"),
    ("workout_log", "ck_workout_reps", "reps > 0"),
    ("payment", "ck_payment_amount", "amount > 0"),
    ("payment", "ck_payment_method", "method IN ('Card', 'Cash', 'Transfer')"),
    ("payment", "ck_payment_category", "category IN ('PT', 'Membership', 'Visit')"),
]

# (인덱스 이름, 테이블, 컬럼)
INDEXES = [
    ("idx_member_expiry", "member", "(expiry_date)"),
    ("idx_pt_session_date", "pt_session", "(session_date)"),
    ("idx_workout_member", "workout_log", "(member_id)"),
    ("idx_workout_date", "workout_log", "(log_date)"),
    ("idx_payment_member", "payment", "(member_id)"),
]

IDENTITY_COLUMNS = [
    ("member", "member_id"),
    ("trainer", "trainer_id"),
    ("exercise", "exercise_id"),
    ("pt_session", "session_id"),
    ("workout_log", "log_id"),
    ("payment", "payment_id"),
]


def _check_existing_data(conn) -> None:
    """새 제약을 붙이기 전에, 기존 데이터가 그 제약을 위반하는지 먼저 알려준다.

    그냥 ALTER 를 실행하면 PostgreSQL 오류만 올라와 어떤 행이 문제인지 알 수 없다.
    """
    bad_times = conn.execute(
        text(
            "SELECT session_id, session_time FROM pt_session "
            f"WHERE session_time !~ '{SESSION_TIME_REGEX}' LIMIT 5"
        )
    ).fetchall()
    if bad_times:
        raise RuntimeError(
            "예약 시각 형식(00:00~23:59)에 맞지 않는 행이 있어 마이그레이션을 중단합니다. "
            f"먼저 수정하세요: {bad_times}"
        )

    for label, column in (("트레이너", "trainer_id"), ("회원", "member_id")):
        duplicates = conn.execute(
            text(
                f"SELECT {column}, session_date, session_time, count(*) AS cnt "
                "FROM pt_session WHERE status <> 'CANCELLED' "
                f"GROUP BY {column}, session_date, session_time HAVING count(*) > 1 LIMIT 5"
            )
        ).fetchall()
        if duplicates:
            raise RuntimeError(
                f"같은 {label}·날짜·시간에 예약이 여러 건 있어 중복 방지 인덱스를 만들 수 없습니다. "
                f"먼저 정리하세요: {duplicates}"
            )


def _create_missing_tables(existing: set[str]) -> None:
    if "exercise" not in existing:
        op.create_table(
            "exercise",
            sa.Column("exercise_id", sa.Integer(), sa.Identity(always=True), nullable=False),
            sa.Column("name", sa.String(length=50), nullable=False),
            sa.Column("part", sa.String(length=20), nullable=False),
            sa.Column("created_at", sa.Date(), server_default=sa.func.current_date()),
            sa.PrimaryKeyConstraint("exercise_id", name="exercise_pkey"),
            sa.UniqueConstraint("name", name="exercise_name_key"),
        )

    if "workout_log" not in existing:
        op.create_table(
            "workout_log",
            sa.Column("log_id", sa.Integer(), sa.Identity(always=True), nullable=False),
            sa.Column("member_id", sa.Integer(), nullable=False),
            sa.Column("exercise_id", sa.Integer(), nullable=False),
            sa.Column(
                "log_date", sa.Date(), server_default=sa.func.current_date(), nullable=False
            ),
            sa.Column("weight", sa.Numeric(precision=6, scale=2)),
            sa.Column("sets", sa.Integer(), nullable=False),
            sa.Column("reps", sa.Integer(), nullable=False),
            sa.Column("feedback", sa.String(length=200)),
            sa.Column("created_at", sa.Date(), server_default=sa.func.current_date()),
            sa.ForeignKeyConstraint(
                ["member_id"],
                ["member.member_id"],
                name="fk_workout_member",
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["exercise_id"], ["exercise.exercise_id"], name="fk_workout_exercise"
            ),
            sa.PrimaryKeyConstraint("log_id", name="workout_log_pkey"),
        )

    if "payment" not in existing:
        op.create_table(
            "payment",
            sa.Column("payment_id", sa.Integer(), sa.Identity(always=True), nullable=False),
            sa.Column("member_id", sa.Integer(), nullable=False),
            sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column(
                "payment_date", sa.Date(), server_default=sa.func.current_date(), nullable=False
            ),
            sa.Column("method", sa.String(length=20), nullable=False),
            sa.Column("category", sa.String(length=20), nullable=False),
            sa.Column("created_at", sa.Date(), server_default=sa.func.current_date()),
            sa.ForeignKeyConstraint(
                ["member_id"],
                ["member.member_id"],
                name="fk_payment_member",
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("payment_id", name="payment_pkey"),
        )


def _apply_defaults() -> None:
    for table, column, default in COLUMN_DEFAULTS:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} SET DEFAULT {default}")
    # created_at 은 현재 모델에서 nullable (Mapped[date | None])
    for table in ALL_TABLES:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN created_at DROP NOT NULL")


def _rename_foreign_keys() -> None:
    for table, old_name, new_name in FK_RENAMES:
        op.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = '{old_name}' AND conrelid = '{table}'::regclass
                ) AND NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = '{new_name}' AND conrelid = '{table}'::regclass
                ) THEN
                    ALTER TABLE {table} RENAME CONSTRAINT {old_name} TO {new_name};
                END IF;
            END $$;
            """
        )


def _apply_check_constraints() -> None:
    for table, name, condition in CHECK_CONSTRAINTS:
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {name}")
        op.execute(f"ALTER TABLE {table} ADD CONSTRAINT {name} CHECK ({condition})")


def _replace_slot_constraints() -> None:
    for name, columns in (
        ("uq_trainer_slot", "(trainer_id, session_date, session_time)"),
        ("uq_member_slot", "(member_id, session_date, session_time)"),
    ):
        # 예전에는 UNIQUE 제약, 현재는 부분 유니크 인덱스 — 두 형태 모두 제거 후 다시 만든다
        op.execute(f"ALTER TABLE pt_session DROP CONSTRAINT IF EXISTS {name}")
        op.execute(f"DROP INDEX IF EXISTS {name}")
        op.execute(
            f"CREATE UNIQUE INDEX {name} ON pt_session {columns} "
            "WHERE status <> 'CANCELLED'"
        )


def _create_indexes() -> None:
    for name, table, columns in INDEXES:
        op.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {table} {columns}")


def _convert_serial_to_identity(conn) -> None:
    for table, column in IDENTITY_COLUMNS:
        is_identity = conn.execute(
            text(
                "SELECT is_identity FROM information_schema.columns "
                "WHERE table_schema = current_schema() "
                "AND table_name = :table AND column_name = :column"
            ),
            {"table": table, "column": column},
        ).scalar()
        if is_identity == "YES":
            continue

        sequence = conn.execute(
            text("SELECT pg_get_serial_sequence(:table, :column)"),
            {"table": table, "column": column},
        ).scalar()
        next_value = conn.execute(
            text(f"SELECT coalesce(max({column}), 0) + 1 FROM {table}")
        ).scalar()

        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} DROP DEFAULT")
        if sequence:
            op.execute(f"DROP SEQUENCE IF EXISTS {sequence}")
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} ADD GENERATED ALWAYS AS IDENTITY")
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} RESTART WITH {next_value}")


def upgrade() -> None:
    conn = op.get_bind()
    existing = set(sa.inspect(conn).get_table_names())

    _check_existing_data(conn)
    _create_missing_tables(existing)
    _apply_defaults()
    _rename_foreign_keys()
    _apply_check_constraints()
    _replace_slot_constraints()
    _create_indexes()
    _convert_serial_to_identity(conn)


def downgrade() -> None:
    raise NotImplementedError(
        "0002 는 되돌릴 수 없습니다. "
        "테이블 추가와 SERIAL → IDENTITY 전환이 포함돼 있어 자동 복구가 안전하지 않습니다. "
        "되돌려야 한다면 RDS 스냅샷에서 복구하세요."
    )
