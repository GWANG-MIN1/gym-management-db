"""결제 기록 API (Payment).

결제 '기록'을 저장하는 API 입니다. 카드 승인 등 실제 결제 처리는 하지 않습니다.
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import require_api_key
from database import get_db, get_read_db
from errors import safe_commit
from models import Payment
from pagination import Pagination, pagination
from schemas import PaymentCategory, PaymentCreate, PaymentResponse

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("", response_model=list[PaymentResponse], summary="결제 기록 목록")
def list_payments(
    member_id: int | None = Query(None, description="회원 ID 로 필터"),
    category: PaymentCategory | None = Query(None, description="결제 구분"),
    page: Pagination = Depends(pagination),
    db: Session = Depends(get_read_db),
):
    stmt = select(Payment)
    if member_id is not None:
        stmt = stmt.where(Payment.member_id == member_id)
    if category is not None:
        stmt = stmt.where(Payment.category == category)

    stmt = (
        stmt.order_by(Payment.payment_date.desc(), Payment.payment_id.desc())
        .limit(page.limit)
        .offset(page.offset)
    )
    return db.scalars(stmt).all()


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
    summary="결제 기록 등록",
)
def create_payment(body: PaymentCreate, db: Session = Depends(get_db)):
    payment = Payment(**body.model_dump(exclude_none=True))
    db.add(payment)
    safe_commit(db)  # 없는 회원이면 FK 위반 → 404
    db.refresh(payment)
    return payment
