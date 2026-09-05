"""SQLAlchemy ORM 모델.

sql/01_create_tables_pg.sql 과 1:1로 대응합니다(테이블 6개 / 제약 / 인덱스 동일).
AWS 환경에서는 이 정의로 create_all() 이 실행되므로, SQL 파일만 고치고 여기를
빠뜨리면 로컬과 배포 환경의 스키마가 달라집니다. 한쪽을 바꾸면 반드시 같이 수정하세요.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Identity,
    Index,
    Integer,
    Numeric,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

# 00:00 ~ 23:59 만 허용 ('^\d{2}:\d{2}$' 는 '99:99' 도 통과했음)
SESSION_TIME_REGEX = r"^([01][0-9]|2[0-3]):[0-5][0-9]$"

# 취소된 예약은 슬롯을 비워야 하므로 부분 유니크 인덱스로 중복 예약을 막는다
_ACTIVE_SESSION = text("status <> 'CANCELLED'")


class Member(Base):
    __tablename__ = "member"

    member_id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    gender: Mapped[str] = mapped_column(String(1), nullable=False)
    join_date: Mapped[date] = mapped_column(
        Date, nullable=False, server_default=func.current_date()
    )
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    remaining_pt_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    created_at: Mapped[date | None] = mapped_column(Date, server_default=func.current_date())

    sessions: Mapped[list["PTSession"]] = relationship("PTSession", back_populates="member")
    workout_logs: Mapped[list["WorkoutLog"]] = relationship("WorkoutLog", back_populates="member")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="member")

    __table_args__ = (
        CheckConstraint("gender IN ('M', 'F')", name="ck_member_gender"),
        CheckConstraint("remaining_pt_count >= 0", name="ck_member_pt_count"),
        Index("idx_member_expiry", "expiry_date"),
    )


class Trainer(Base):
    __tablename__ = "trainer"

    trainer_id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    specialty: Mapped[str] = mapped_column(String(50), nullable=False)
    career_year: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[date | None] = mapped_column(Date, server_default=func.current_date())

    sessions: Mapped[list["PTSession"]] = relationship("PTSession", back_populates="trainer")

    __table_args__ = (CheckConstraint("career_year >= 0", name="ck_trainer_career"),)


class Exercise(Base):
    __tablename__ = "exercise"

    exercise_id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    part: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[date | None] = mapped_column(Date, server_default=func.current_date())

    workout_logs: Mapped[list["WorkoutLog"]] = relationship(
        "WorkoutLog", back_populates="exercise"
    )


class PTSession(Base):
    __tablename__ = "pt_session"

    session_id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    member_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("member.member_id", ondelete="CASCADE", name="fk_pt_session_member"),
        nullable=False,
    )
    trainer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("trainer.trainer_id", name="fk_pt_session_trainer"),
        nullable=False,
    )
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    session_time: Mapped[str] = mapped_column(String(5), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="SCHEDULED", server_default="SCHEDULED"
    )
    created_at: Mapped[date | None] = mapped_column(Date, server_default=func.current_date())

    member: Mapped["Member"] = relationship("Member", back_populates="sessions")
    trainer: Mapped["Trainer"] = relationship("Trainer", back_populates="sessions")

    __table_args__ = (
        CheckConstraint(
            "status IN ('SCHEDULED', 'COMPLETED', 'CANCELLED')", name="ck_session_status"
        ),
        CheckConstraint(f"session_time ~ '{SESSION_TIME_REGEX}'", name="ck_session_time_format"),
        Index(
            "uq_trainer_slot",
            "trainer_id",
            "session_date",
            "session_time",
            unique=True,
            postgresql_where=_ACTIVE_SESSION,
        ),
        Index(
            "uq_member_slot",
            "member_id",
            "session_date",
            "session_time",
            unique=True,
            postgresql_where=_ACTIVE_SESSION,
        ),
        Index("idx_pt_session_date", "session_date"),
    )


class WorkoutLog(Base):
    __tablename__ = "workout_log"

    log_id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    member_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("member.member_id", ondelete="CASCADE", name="fk_workout_member"),
        nullable=False,
    )
    exercise_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("exercise.exercise_id", name="fk_workout_exercise"),
        nullable=False,
    )
    log_date: Mapped[date] = mapped_column(
        Date, nullable=False, server_default=func.current_date()
    )
    weight: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    sets: Mapped[int] = mapped_column(Integer, nullable=False)
    reps: Mapped[int] = mapped_column(Integer, nullable=False)
    feedback: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[date | None] = mapped_column(Date, server_default=func.current_date())

    member: Mapped["Member"] = relationship("Member", back_populates="workout_logs")
    exercise: Mapped["Exercise"] = relationship("Exercise", back_populates="workout_logs")

    __table_args__ = (
        CheckConstraint("weight IS NULL OR weight > 0", name="ck_workout_weight"),
        CheckConstraint("sets > 0", name="ck_workout_sets"),
        CheckConstraint("reps > 0", name="ck_workout_reps"),
        Index("idx_workout_member", "member_id"),
        Index("idx_workout_date", "log_date"),
    )


class Payment(Base):
    __tablename__ = "payment"

    payment_id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    member_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("member.member_id", ondelete="CASCADE", name="fk_payment_member"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(
        Date, nullable=False, server_default=func.current_date()
    )
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[date | None] = mapped_column(Date, server_default=func.current_date())

    member: Mapped["Member"] = relationship("Member", back_populates="payments")

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payment_amount"),
        CheckConstraint("method IN ('Card', 'Cash', 'Transfer')", name="ck_payment_method"),
        CheckConstraint(
            "category IN ('PT', 'Membership', 'Visit')", name="ck_payment_category"
        ),
        Index("idx_payment_member", "member_id"),
    )
