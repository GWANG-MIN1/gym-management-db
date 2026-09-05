from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import require_api_key
from database import get_db, get_read_db
from errors import safe_commit
from models import Trainer
from pagination import Pagination, pagination
from schemas import TrainerCreate, TrainerResponse

router = APIRouter(prefix="/trainers", tags=["trainers"])


@router.get("", response_model=list[TrainerResponse], summary="트레이너 목록 (페이지네이션)")
def list_trainers(
    page: Pagination = Depends(pagination),
    db: Session = Depends(get_read_db),
):
    stmt = (
        select(Trainer)
        .order_by(Trainer.trainer_id)
        .limit(page.limit)
        .offset(page.offset)
    )
    return db.scalars(stmt).all()


@router.post(
    "",
    response_model=TrainerResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
    summary="트레이너 등록",
)
def create_trainer(body: TrainerCreate, db: Session = Depends(get_db)):
    trainer = Trainer(**body.model_dump())
    db.add(trainer)
    safe_commit(db)
    db.refresh(trainer)
    return trainer


@router.get("/{trainer_id}", response_model=TrainerResponse, summary="트레이너 상세")
def get_trainer(trainer_id: int, db: Session = Depends(get_read_db)):
    trainer = db.get(Trainer, trainer_id)
    if trainer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "트레이너를 찾을 수 없습니다.")
    return trainer
