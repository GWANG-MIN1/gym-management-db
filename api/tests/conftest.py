"""API 테스트 공통 설정.

PostgreSQL 에 붙어서 실행합니다(CHECK 정규식·부분 유니크 인덱스가 PostgreSQL 전용).

**테스트는 테이블을 삭제·재생성합니다.** 개발용 DB 를 지우지 않도록
접속 정보는 TEST_DATABASE_URL 로만 받고, DB 이름이 `_test` 로 끝나지 않으면 실행을 거부합니다.

  docker compose up -d db
  docker compose exec -T db psql -U gymadmin -d gymdb -c "CREATE DATABASE gymdb_test"
  cd api && TEST_DATABASE_URL=postgresql://gymadmin:gymadmin123@localhost:5433/gymdb_test pytest -q
"""

import os
from datetime import date, timedelta
from urllib.parse import urlsplit

import pytest

# 인증은 기본 비활성 상태로 테스트 (전용 테스트에서만 API_KEY 를 설정)
os.environ.pop("API_KEY", None)
os.environ.pop("READ_DATABASE_URL", None)

_TEST_DB_SUFFIX = "_test"
_USAGE = (
    "  docker compose exec -T db psql -U gymadmin -d gymdb -c \"CREATE DATABASE gymdb_test\"\n"
    "  cd api && TEST_DATABASE_URL=postgresql://gymadmin:gymadmin123@localhost:5433/gymdb_test pytest"
)

# DATABASE_URL 은 일부러 쓰지 않는다 — 개발용 DB 를 가리키고 있을 때
# drop_all() 로 데이터를 지우는 사고를 막기 위해서다.
_DB_URL = os.environ.get("TEST_DATABASE_URL")
if not _DB_URL:
    raise RuntimeError(
        "테스트는 전용 DB 에서만 실행합니다. TEST_DATABASE_URL 을 설정하세요.\n" + _USAGE
    )

_DB_NAME = urlsplit(_DB_URL).path.lstrip("/")
if not _DB_NAME.endswith(_TEST_DB_SUFFIX):
    raise RuntimeError(
        f"테스트는 테이블을 삭제·재생성하므로 '{_TEST_DB_SUFFIX}' 로 끝나는 전용 DB 에서만 "
        f"실행합니다. 지정된 DB: '{_DB_NAME}'\n" + _USAGE
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
