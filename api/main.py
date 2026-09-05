from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database import READ_REPLICA_ENABLED, Base, engine, get_db
from routers import exercises, members, payments, sessions, trainers, workouts

API_VERSION = "1.1.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 빈 RDS 에서도 기동되도록 시작 시 테이블을 만든다(이미 있으면 건너뜀).
    # models.py 가 sql/01_create_tables_pg.sql 과 같은 6개 테이블을 정의하므로
    # 로컬(SQL 적용)과 AWS(create_all) 스키마가 같아진다.
    Base.metadata.create_all(bind=engine)
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
