"""PT 예약 API.

예약 시 확인하는 업무 규칙
  1. 회원 / 트레이너 존재 여부
  2. 지난 날짜 예약 불가
  3. 회원권 만료일 이후 예약 불가
  4. 잔여 PT 횟수가 0이면 예약 불가
  5. 같은 트레이너 / 같은 회원의 같은 시간대 중복 예약 불가 (DB 부분 유니크 인덱스 → 409)

잔여 PT 횟수 차감은 Oracle 스키마에서 트리거로 하던 일이며,
PostgreSQL 로 옮기면서 API 의 완료 처리(PATCH /sessions/{id}/complete)로 옮겼습니다.
같은 트랜잭션에서 상태 변경과 차감을 함께 처리해 기록과 잔여 횟수가 어긋나지 않게 합니다.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from auth import require_api_key
from database import get_db, get_read_db
from errors import safe_commit
from models import Member, PTSession, Trainer
from pagination import Pagination, pagination
from schemas import SessionCreate, SessionResponse, SessionStatus

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _get_session_for_update(session_id: int, db: Session) -> PTSession:
    """상태를 바꿀 예약을 잠금과 함께 조회한다(동시 요청 시 중복 처리 방지)."""
    pt_session = db.get(PTSession, session_id, with_for_update=True)
    if pt_session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "예약을 찾을 수 없습니다.")
    return pt_session


@router.get("", response_model=list[SessionResponse], summary="PT 예약 목록 (필터 + 페이지네이션)")
def list_sessions(
    member_id: int | None = Query(None, description="회원 ID 로 필터"),
    trainer_id: int | None = Query(None, description="트레이너 ID 로 필터"),
    session_status: SessionStatus | None = Query(None, alias="status", description="예약 상태"),
    date_from: date | None = Query(None, description="이 날짜 이후(포함)"),
    date_to: date | None = Query(None, description="이 날짜 이전(포함)"),
    page: Pagination = Depends(pagination),
    db: Session = Depends(get_read_db),
):
    stmt = select(PTSession)
    if member_id is not None:
        stmt = stmt.where(PTSession.member_id == member_id)
    if trainer_id is not None:
        stmt = stmt.where(PTSession.trainer_id == trainer_id)
    if session_status is not None:
        stmt = stmt.where(PTSession.status == session_status)
    if date_from is not None:
        stmt = stmt.where(PTSession.session_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(PTSession.session_date <= date_to)

    stmt = (
        stmt.order_by(PTSession.session_date, PTSession.session_time, PTSession.session_id)
        .limit(page.limit)
        .offset(page.offset)
    )
    return db.scalars(stmt).all()


@router.get("/{session_id}", response_model=SessionResponse, summary="PT 예약 상세")
def get_session(session_id: int, db: Session = Depends(get_read_db)):
    pt_session = db.get(PTSession, session_id)
    if pt_session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "예약을 찾을 수 없습니다.")
    return pt_session


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
    summary="PT 예약",
)
def create_session(body: SessionCreate, db: Session = Depends(get_db)):
    member = db.get(Member, body.member_id)
    if member is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "회원을 찾을 수 없습니다.")
    if db.get(Trainer, body.trainer_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "트레이너를 찾을 수 없습니다.")

    if body.session_date < date.today():
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "지난 날짜로는 예약할 수 없습니다."
        )
    if body.session_date > member.expiry_date:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"회원권 만료일({member.expiry_date}) 이후 날짜로는 예약할 수 없습니다.",
        )
    if member.remaining_pt_count <= 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "잔여 PT 횟수가 없습니다.")

    pt_session = PTSession(**body.model_dump())
    db.add(pt_session)
    safe_commit(db)  # 같은 시간대 중복 예약이면 409
    db.refresh(pt_session)
    return pt_session


@router.patch(
    "/{session_id}/complete",
    response_model=SessionResponse,
    dependencies=[Depends(require_api_key)],
    summary="PT 완료 처리 (잔여 횟수 1 차감)",
)
def complete_session(session_id: int, db: Session = Depends(get_db)):
    pt_session = _get_session_for_update(session_id, db)

    if pt_session.status == "COMPLETED":
        raise HTTPException(status.HTTP_409_CONFLICT, "이미 완료 처리된 예약입니다.")
    if pt_session.status == "CANCELLED":
        raise HTTPException(status.HTTP_409_CONFLICT, "취소된 예약은 완료 처리할 수 없습니다.")

    # 잔여 횟수가 남아 있을 때만 차감 — 음수로 내려가지 않도록 조건을 UPDATE 문에 둔다
    result = db.execute(
        update(Member)
        .where(Member.member_id == pt_session.member_id, Member.remaining_pt_count > 0)
        .values(remaining_pt_count=Member.remaining_pt_count - 1)
    )
    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "잔여 PT 횟수가 없어 완료 처리할 수 없습니다."
        )

    pt_session.status = "COMPLETED"
    safe_commit(db)
    db.refresh(pt_session)
    return pt_session


@router.patch(
    "/{session_id}/cancel",
    response_model=SessionResponse,
    dependencies=[Depends(require_api_key)],
    summary="PT 예약 취소",
)
def cancel_session(session_id: int, db: Session = Depends(get_db)):
    pt_session = _get_session_for_update(session_id, db)

    if pt_session.status == "COMPLETED":
        raise HTTPException(status.HTTP_409_CONFLICT, "이미 완료된 예약은 취소할 수 없습니다.")
    if pt_session.status == "CANCELLED":
        raise HTTPException(status.HTTP_409_CONFLICT, "이미 취소된 예약입니다.")

    pt_session.status = "CANCELLED"
    safe_commit(db)
    db.refresh(pt_session)
    return pt_session
