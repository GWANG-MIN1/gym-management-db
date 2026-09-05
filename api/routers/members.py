from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import require_api_key
from database import get_db, get_read_db
from errors import safe_commit
from models import Member
from pagination import Pagination, pagination
from schemas import MemberCreate, MemberResponse

router = APIRouter(prefix="/members", tags=["members"])


@router.get("", response_model=list[MemberResponse], summary="회원 목록 (페이지네이션)")
def list_members(
    page: Pagination = Depends(pagination),
    db: Session = Depends(get_read_db),
):
    stmt = (
        select(Member)
        .order_by(Member.member_id)
        .limit(page.limit)
        .offset(page.offset)
    )
    return db.scalars(stmt).all()


@router.post(
    "",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
    summary="회원 등록",
)
def create_member(body: MemberCreate, db: Session = Depends(get_db)):
    member = Member(**body.model_dump())
    db.add(member)
    safe_commit(db)  # 전화번호 중복이면 409
    db.refresh(member)
    return member


@router.get("/{member_id}", response_model=MemberResponse, summary="회원 상세")
def get_member(member_id: int, db: Session = Depends(get_read_db)):
    member = db.get(Member, member_id)
    if member is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "회원을 찾을 수 없습니다.")
    return member
