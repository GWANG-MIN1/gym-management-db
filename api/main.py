from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database import READ_REPLICA_ENABLED, get_db
from migrate import run_migrations
from routers import exercises, members, payments, sessions, trainers, workouts

API_VERSION = "1.1.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 스키마를 최신으로 올린다.
    # create_all() 은 '없는 테이블'만 만들 뿐 기존 테이블의 기본값·제약·인덱스를
    # 바꾸지 못해, 예전 스키마 위에 새 버전을 올리면 등록 요청이 전부 실패했다.
    run_migrations()
    yield


app = FastAPI(title="Gym Management API", version=API_VERSION, lifespan=lifespan)

app.include_router(members.router)
app.include_router(trainers.router)
app.include_router(exercises.router)
app.include_router(sessions.router)
app.include_router(workouts.router)
app.include_router(payments.router)


@app.get("/health", tags=["health"], summary="헬스체크 (DB 연결 확인)")
def health(db: Session = Depends(get_db)):
    """CD 파이프라인의 배포 성공 판정 기준.

    고정 응답만 돌려주면 DB 접속이 끊긴 상태도 '정상'으로 보이므로 SELECT 1 로 확인한다.
    """
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "database unavailable"
        ) from None

    return {
        "status": "ok",
        "database": "ok",
        "read_replica": READ_REPLICA_ENABLED,
        "version": API_VERSION,
    }


@app.get("/health/live", tags=["health"], summary="라이브니스 (프로세스 응답만 확인)")
def liveness():
    return {"status": "ok", "version": API_VERSION}
