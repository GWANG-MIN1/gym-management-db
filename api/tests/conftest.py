"""API 테스트 공통 설정.

PostgreSQL 에 붙어서 실행합니다(CHECK 정규식·부분 유니크 인덱스가 PostgreSQL 전용).

  docker compose up -d db
  DATABASE_URL=postgresql://gymadmin:gymadmin123@localhost:5433/gymdb pytest
"""

import os
from datetime import date, timedelta

import pytest

# 인증은 기본 비활성 상태로 테스트 (전용 테스트에서만 API_KEY 를 설정)
os.environ.pop("API_KEY", None)
os.environ.pop("READ_DATABASE_URL", None)

_DB_URL = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
if not _DB_URL:
    raise RuntimeError(
        "테스트에는 PostgreSQL 접속 정보가 필요합니다. "
        "TEST_DATABASE_URL 또는 DATABASE_URL 환경변수를 설정하세요."
    )
os.environ["DATABASE_URL"] = _DB_URL

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from database import Base, engine  # noqa: E402
from main import app  # noqa: E402

_TABLES = "payment, workout_log, pt_session, exercise, trainer, member"


@pytest.fixture(scope="session")
def _database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client(_database):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def _clean_tables(_database):
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {_TABLES} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def today() -> date:
    return date.today()


@pytest.fixture
def make_member(client, today):
    def _make(**overrides):
        payload = {
            "name": "홍길동",
            "phone": "010-0000-0001",
            "gender": "M",
            "join_date": today.isoformat(),
            "expiry_date": (today + timedelta(days=365)).isoformat(),
            "remaining_pt_count": 5,
        }
        payload.update(overrides)
        response = client.post("/members", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture
def make_trainer(client):
    def _make(**overrides):
        payload = {"name": "김트레이너", "specialty": "체형교정", "career_year": 5}
        payload.update(overrides)
        response = client.post("/trainers", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture
def make_exercise(client):
    def _make(**overrides):
        payload = {"name": "스쿼트", "part": "하체"}
        payload.update(overrides)
        response = client.post("/exercises", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture
def make_session(client, make_member, make_trainer, today):
    def _make(member=None, trainer=None, **overrides):
        member = member or make_member()
        trainer = trainer or make_trainer()
        payload = {
            "member_id": member["member_id"],
            "trainer_id": trainer["trainer_id"],
            "session_date": (today + timedelta(days=1)).isoformat(),
            "session_time": "14:00",
        }
        payload.update(overrides)
        response = client.post("/sessions", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _make
