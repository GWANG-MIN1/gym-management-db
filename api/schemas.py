"""API 요청/응답 스키마(Pydantic).

models.py 가 'DB 에 저장하는 구조'라면, 여기는 'API 로 주고받는 데이터 규격'입니다.
DB CHECK 제약과 같은 조건을 여기서 먼저 검사해 422 로 돌려주고,
동시성 때문에 DB 에서만 걸리는 위반(중복 등)은 errors.py 가 409 로 변환합니다.
"""

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# 00:00 ~ 23:59 만 허용 (기존 r"^\d{2}:\d{2}$" 는 "99:99" 도 통과했음)
SESSION_TIME_PATTERN = r"^([01][0-9]|2[0-3]):[0-5][0-9]$"

SessionStatus = Literal["SCHEDULED", "COMPLETED", "CANCELLED"]
PaymentMethod = Literal["Card", "Cash", "Transfer"]
PaymentCategory = Literal["PT", "Membership", "Visit"]


# ── Member ────────────────────────────────────────────────────────────────────

class MemberCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    phone: str = Field(..., min_length=1, max_length=20)
    gender: Literal["M", "F"]
    join_date: date
    expiry_date: date
    remaining_pt_count: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def check_period(self) -> "MemberCreate":
        if self.expiry_date < self.join_date:
            raise ValueError("만료일은 가입일보다 빠를 수 없습니다.")
        return self


class MemberResponse(BaseModel):
    member_id: int
    name: str
    phone: str
    gender: str
    join_date: date
    expiry_date: date
    remaining_pt_count: int
    created_at: date | None

    model_config = ConfigDict(from_attributes=True)


# ── Trainer ───────────────────────────────────────────────────────────────────

class TrainerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    specialty: str = Field(..., min_length=1, max_length=50)
    career_year: int = Field(..., ge=0)


class TrainerResponse(BaseModel):
    trainer_id: int
    name: str
    specialty: str
    career_year: int
    created_at: date | None

    model_config = ConfigDict(from_attributes=True)


# ── Exercise ──────────────────────────────────────────────────────────────────

class ExerciseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    part: str = Field(..., min_length=1, max_length=20)


class ExerciseResponse(BaseModel):
    exercise_id: int
    name: str
    part: str
    created_at: date | None

    model_config = ConfigDict(from_attributes=True)


# ── PT Session ────────────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    """PT 예약 생성 요청.

    status 는 받지 않습니다. 예약은 항상 SCHEDULED 로 만들어지고,
    완료/취소는 PATCH /sessions/{id}/complete · /cancel 로만 바꿉니다.
    (완료 처리는 잔여 PT 횟수 차감을 동반하므로 생성 시점에 허용하면 값이 어긋납니다.)
    """

    member_id: int = Field(..., gt=0)
    trainer_id: int = Field(..., gt=0)
    session_date: date
    session_time: str = Field(..., pattern=SESSION_TIME_PATTERN, examples=["14:00"])


class SessionResponse(BaseModel):
    session_id: int
    member_id: int
    trainer_id: int
    session_date: date
    session_time: str
    status: SessionStatus
    created_at: date | None

    model_config = ConfigDict(from_attributes=True)


# ── Workout Log ───────────────────────────────────────────────────────────────

class WorkoutLogCreate(BaseModel):
    member_id: int = Field(..., gt=0)
    exercise_id: int = Field(..., gt=0)
    log_date: date | None = None  # 생략하면 DB 기본값(CURRENT_DATE)
    weight: Decimal | None = Field(default=None, gt=0, max_digits=6, decimal_places=2)
    sets: int = Field(..., gt=0)
    reps: int = Field(..., gt=0)
    feedback: str | None = Field(default=None, max_length=200)


class WorkoutLogResponse(BaseModel):
    log_id: int
    member_id: int
    exercise_id: int
    log_date: date
    weight: Decimal | None
    sets: int
    reps: int
    feedback: str | None
    created_at: date | None

    model_config = ConfigDict(from_attributes=True)


# ── Payment ───────────────────────────────────────────────────────────────────

class PaymentCreate(BaseModel):
    member_id: int = Field(..., gt=0)
    amount: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    payment_date: date | None = None  # 생략하면 DB 기본값(CURRENT_DATE)
    method: PaymentMethod
    category: PaymentCategory


class PaymentResponse(BaseModel):
    payment_id: int
    member_id: int
    amount: Decimal
    payment_date: date
    method: PaymentMethod
    category: PaymentCategory
    created_at: date | None

    model_config = ConfigDict(from_attributes=True)
