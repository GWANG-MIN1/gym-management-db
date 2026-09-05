from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import require_api_key
from database import get_db, get_read_db
from errors import safe_commit
from models import Exercise
from pagination import Pagination, pagination
from schemas import ExerciseCreate, ExerciseResponse

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("", response_model=list[ExerciseResponse], summary="운동 종목 목록")
def list_exercises(
    page: Pagination = Depends(pagination),
    db: Session = Depends(get_read_db),
):
    stmt = (
        select(Exercise)
        .order_by(Exercise.exercise_id)
        .limit(page.limit)
        .offset(page.offset)
    )
    return db.scalars(stmt).all()


@router.post(
    "",
    response_model=ExerciseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
    summary="운동 종목 등록",
)
def create_exercise(body: ExerciseCreate, db: Session = Depends(get_db)):
    exercise = Exercise(**body.model_dump())
    db.add(exercise)
    safe_commit(db)  # 종목명 중복이면 409
    db.refresh(exercise)
    return exercise
