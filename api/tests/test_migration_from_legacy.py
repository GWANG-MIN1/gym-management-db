"""예전 스키마로 만들어진 DB 가 현재 버전으로 업그레이드되는지 확인.

다른 테스트는 전부 빈 DB 에서 시작하므로 "기존 DB 위에 새 버전을 배포하는" 경로를
검증하지 못한다. 여기서는 별도 DB 에 예전 스키마(tests/legacy_schema.sql)와 데이터를
만들고, run_migrations() 를 돌린 뒤

  1. 스키마가 현재 ORM 정의와 같아지는지
  2. 기존 데이터가 남고 ID 채번이 이어지는지
  3. 등록·예약·취소 후 재예약 같은 API 동작이 정상인지

를 확인한다.
"""

import contextlib
import pathlib
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import sessionmaker

from database import engine as test_engine
from database import get_db, get_read_db
from main import app
from migrate import run_migrations
from tests.schema_snapshot import SNAPSHOT_QUERIES, diff_message, snapshot

LEGACY_SCHEMA_SQL = (pathlib.Path(__file__).parent / "legacy_schema.sql").read_text()

TODAY = date.today()
TOMORROW = TODAY + timedelta(days=1)


@pytest.fixture
def legacy_engine():
    """예전 스키마와 데이터가 들어 있는 별도 DB 를 만들어 준다."""
    # str(URL) 은 비밀번호를 '***' 로 가린다. 그 문자열로 URL 을 다시 만들면
    # 비밀번호가 '***' 인 접속 정보가 되어 연결에 실패하므로, URL 객체를 그대로 쓴다.
    url = test_engine.url
    legacy_url = url.set(database=f"{url.database}_legacy")

    with test_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        try:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{legacy_url.database}"'))
            conn.execute(text(f'CREATE DATABASE "{legacy_url.database}"'))
        except ProgrammingError as exc:  # CREATEDB 권한이 없는 계정
            pytest.skip(f"업그레이드 테스트에는 DB 생성 권한이 필요합니다: {exc}")

    engine = create_engine(legacy_url)
    with engine.begin() as conn:
        conn.execute(text(LEGACY_SCHEMA_SQL))
        conn.execute(
            text(
                "INSERT INTO member "
                "(name, phone, gender, join_date, expiry_date, remaining_pt_count, created_at) "
                "VALUES ('기존회원', '010-1111-1111', 'M', :today, :expiry, 3, :today)"
            ),
            {"today": TODAY, "expiry": TODAY + timedelta(days=365)},
        )
        conn.execute(
            text(
                "INSERT INTO trainer (name, specialty, career_year, created_at) "
                "VALUES ('기존트레이너', '체형교정', 5, :today)"
            ),
            {"today": TODAY},
        )
        conn.execute(
            text(
                "INSERT INTO pt_session "
                "(member_id, trainer_id, session_date, session_time, status, created_at) "
                "VALUES (1, 1, :when, '09:00', 'SCHEDULED', :today)"
            ),
            {"when": TOMORROW, "today": TODAY},
        )

    yield engine

    engine.dispose()
    with test_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{legacy_url.database}"'))


@contextlib.contextmanager
def api_client_on(engine):
    """FastAPI 앱을 지정한 엔진에 붙여 준다 (lifespan 을 타지 않으므로 마이그레이션은 수동 실행)."""
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    app.dependency_overrides[get_read_db] = override
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _member_payload(phone: str) -> dict:
    return {
        "name": "새회원",
        "phone": phone,
        "gender": "M",
        "join_date": TODAY.isoformat(),
        "expiry_date": (TODAY + timedelta(days=365)).isoformat(),
        "remaining_pt_count": 5,
    }


def test_legacy_schema_without_migration_rejects_writes(legacy_engine):
    """마이그레이션 전에는 등록이 실패한다 — 이 테스트가 마이그레이션의 존재 이유다.

    예전 테이블의 created_at 은 NOT NULL 인데 기본값이 없고, 현재 API 는 그 값을
    보내지 않기 때문에 NOT NULL 위반이 난다.
    """
    with api_client_on(legacy_engine) as client:
        assert client.get("/health").status_code == 200
        assert client.post("/members", json=_member_payload("010-2222-2222")).status_code == 422
        assert (
            client.post(
                "/trainers", json={"name": "새코치", "specialty": "재활", "career_year": 2}
            ).status_code
            == 422
        )


@pytest.mark.parametrize(("label", "query"), list(SNAPSHOT_QUERIES.items()))
def test_migrated_schema_matches_orm(legacy_engine, label, query):
    run_migrations(legacy_engine)

    with legacy_engine.connect() as conn:
        migrated = snapshot(conn, query, "public")
    with test_engine.connect() as conn:
        expected = snapshot(conn, query, "public")

    assert migrated, f"{label} 정보를 읽지 못했습니다"
    assert migrated == expected, diff_message(label, "마이그레이션 결과", migrated, "ORM 모델", expected)


def test_existing_rows_survive_and_ids_continue(legacy_engine):
    run_migrations(legacy_engine)

    with legacy_engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM member")).scalar() == 1
        assert conn.execute(text("SELECT count(*) FROM pt_session")).scalar() == 1
        assert conn.execute(text("SELECT created_at FROM member")).scalar() == TODAY

    with api_client_on(legacy_engine) as client:
        created = client.post("/members", json=_member_payload("010-3333-3333"))
        assert created.status_code == 201, created.text
        # SERIAL → IDENTITY 로 바꾼 뒤에도 채번이 기존 최댓값 다음부터 이어져야 한다
        assert created.json()["member_id"] == 2
        assert created.json()["created_at"] == TODAY.isoformat()


def test_api_works_after_migration(legacy_engine):
    run_migrations(legacy_engine)

    with api_client_on(legacy_engine) as client:
        trainer = client.post(
            "/trainers", json={"name": "새코치", "specialty": "재활", "career_year": 2}
        )
        assert trainer.status_code == 201, trainer.text

        booking = {
            "member_id": 1,
            "trainer_id": 1,
            "session_date": (TODAY + timedelta(days=2)).isoformat(),
            "session_time": "11:00",
        }
        created = client.post("/sessions", json=booking)
        assert created.status_code == 201, created.text

        # 예전 UNIQUE 제약에서는 취소해도 슬롯이 비지 않아 재예약이 409 였다
        assert client.patch(f"/sessions/{created.json()['session_id']}/cancel").status_code == 200
        assert client.post("/sessions", json=booking).status_code == 201

        # 새로 생긴 테이블도 사용할 수 있어야 한다
        exercise = client.post("/exercises", json={"name": "스쿼트", "part": "하체"})
        assert exercise.status_code == 201, exercise.text
        workout = client.post(
            "/workouts",
            json={
                "member_id": 1,
                "exercise_id": exercise.json()["exercise_id"],
                "sets": 3,
                "reps": 10,
            },
        )
        assert workout.status_code == 201, workout.text


def test_migration_is_idempotent(legacy_engine):
    run_migrations(legacy_engine)
    run_migrations(legacy_engine)  # 재배포로 두 번 실행돼도 문제가 없어야 한다

    with api_client_on(legacy_engine) as client:
        assert client.post("/members", json=_member_payload("010-4444-4444")).status_code == 201
