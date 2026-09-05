"""legacy baseline — 이전 버전(회원/트레이너/PT 3개 테이블) 스키마

이 리비전은 "예전 create_all() 이 만들던 스키마"를 그대로 정의한다.

  - 빈 DB     : 0001 로 예전 스키마를 만들고 0002 로 현재 스키마까지 올린다.
  - 기존 DB   : 이미 테이블이 있고 alembic_version 이 없으면 이 리비전으로 stamp 한 뒤
                0002 만 적용한다 (api/migrate.py 참고).

Revision ID: 0001
Revises:
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "member",
        sa.Column("member_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("gender", sa.String(length=1), nullable=False),
        sa.Column("join_date", sa.Date(), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=False),
        sa.Column("remaining_pt_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.Date(), nullable=False),
        sa.CheckConstraint("gender IN ('M', 'F')", name="ck_member_gender"),
        sa.CheckConstraint("remaining_pt_count >= 0", name="ck_member_pt_count"),
        sa.PrimaryKeyConstraint("member_id", name="member_pkey"),
        sa.UniqueConstraint("phone", name="member_phone_key"),
    )
    op.create_table(
        "trainer",
        sa.Column("trainer_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("specialty", sa.String(length=50), nullable=False),
        sa.Column("career_year", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.Date(), nullable=False),
        sa.CheckConstraint("career_year >= 0", name="ck_trainer_career"),
        sa.PrimaryKeyConstraint("trainer_id", name="trainer_pkey"),
    )
    op.create_table(
        "pt_session",
        sa.Column("session_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("trainer_id", sa.Integer(), nullable=False),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("session_time", sa.String(length=5), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.Date(), nullable=False),
        sa.CheckConstraint(
            "status IN ('SCHEDULED', 'COMPLETED', 'CANCELLED')", name="ck_session_status"
        ),
        sa.ForeignKeyConstraint(
            ["member_id"],
            ["member.member_id"],
            name="pt_session_member_id_fkey",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["trainer_id"], ["trainer.trainer_id"], name="pt_session_trainer_id_fkey"
        ),
        sa.PrimaryKeyConstraint("session_id", name="pt_session_pkey"),
        sa.UniqueConstraint(
            "trainer_id", "session_date", "session_time", name="uq_trainer_slot"
        ),
    )


def downgrade() -> None:
    op.drop_table("pt_session")
    op.drop_table("trainer")
    op.drop_table("member")
