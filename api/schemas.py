from datetime import date
from typing import Literal
from pydantic import BaseModel, Field


# ── Member ────────────────────────────────────────────────────────────────────

class MemberCreate(BaseModel):
    name: str = Field(..., max_length=50)
    phone: str = Field(..., max_length=20)
    gender: Literal["M", "F"]
    join_date: date
    expiry_date: date
    remaining_pt_count: int = Field(default=0, ge=0)


class MemberResponse(MemberCreate):
    member_id: int
    created_at: date | None

    model_config = {"from_attributes": True}


# ── Trainer ───────────────────────────────────────────────────────────────────

class TrainerResponse(BaseModel):
    trainer_id: int
    name: str
    specialty: str
    career_year: int
    created_at: date | None

    model_config = {"from_attributes": True}


# ── PT Session ────────────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    member_id: int
    trainer_id: int
    session_date: date
    session_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    status: Literal["SCHEDULED", "COMPLETED", "CANCELLED"] = "SCHEDULED"


class SessionResponse(SessionCreate):
    session_id: int
    created_at: date | None

    model_config = {"from_attributes": True}
