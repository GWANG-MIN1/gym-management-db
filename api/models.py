from datetime import date
from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Member(Base):
    __tablename__ = "member"

    member_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    gender: Mapped[str] = mapped_column(String(1), nullable=False)
    join_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    remaining_pt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[date] = mapped_column(Date)

    sessions: Mapped[list["PTSession"]] = relationship("PTSession", back_populates="member")

    __table_args__ = (
        CheckConstraint("gender IN ('M', 'F')", name="ck_member_gender"),
        CheckConstraint("remaining_pt_count >= 0", name="ck_member_pt_count"),
    )


class Trainer(Base):
    __tablename__ = "trainer"

    trainer_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    specialty: Mapped[str] = mapped_column(String(50), nullable=False)
    career_year: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[date] = mapped_column(Date)

    sessions: Mapped[list["PTSession"]] = relationship("PTSession", back_populates="trainer")

    __table_args__ = (
        CheckConstraint("career_year >= 0", name="ck_trainer_career"),
    )


class PTSession(Base):
    __tablename__ = "pt_session"

    session_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    member_id: Mapped[int] = mapped_column(Integer, ForeignKey("member.member_id", ondelete="CASCADE"), nullable=False)
    trainer_id: Mapped[int] = mapped_column(Integer, ForeignKey("trainer.trainer_id"), nullable=False)
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    session_time: Mapped[str] = mapped_column(String(5), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="SCHEDULED")
    created_at: Mapped[date] = mapped_column(Date)

    member: Mapped["Member"] = relationship("Member", back_populates="sessions")
    trainer: Mapped["Trainer"] = relationship("Trainer", back_populates="sessions")

    __table_args__ = (
        CheckConstraint("status IN ('SCHEDULED', 'COMPLETED', 'CANCELLED')", name="ck_session_status"),
        UniqueConstraint("trainer_id", "session_date", "session_time", name="uq_trainer_slot"),
    )
