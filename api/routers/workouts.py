"""운동 기록 API (Workout_Log)."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import require_api_key
from database import get_db, get_read_db
from errors import safe_commit
from models import WorkoutLog
from pagination import Pagination, pagination
from schemas import WorkoutLogCreate, WorkoutLogResponse

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.get("", response_model=list[WorkoutLogResponse], summary="운동 기록 목록")
def list_workouts(
    member_id: int | None = Query(None, description="회원 ID 로 필터"),
    exercise_id: int | None = Query(None, description="운동 종목 ID 로 필터"),
    page: Pagination = Depends(pagination),
    db: Session = Depends(get_read_db),
):
    stmt = select(WorkoutLog)
    if member_id is not None:
        stmt = stmt.where(WorkoutLog.member_id == member_id)
    if exercise_id is not None:
        stmt = stmt.where(WorkoutLog.exercise_id == exercise_id)

    stmt = (
        stmt.order_by(WorkoutLog.log_date.desc(), WorkoutLog.log_id.desc())
        .limit(page.limit)
        .offset(page.offset)
    )
    return db.scalars(stmt).all()


@router.post(
    "",
    response_model=WorkoutLogResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
    summary="운동 기록 등록",
)
def create_workout(body: WorkoutLogCreate, db: Session = Depends(get_db)):
    # log_date 를 생략하면 DB 기본값(CURRENT_DATE)이 들어가도록 None 필드는 제외
    workout = WorkoutLog(**body.model_dump(exclude_none=True))
    db.add(workout)
    safe_commit(db)  # 없는 회원/종목이면 FK 위반 → 404
    db.refresh(workout)
    return workout
