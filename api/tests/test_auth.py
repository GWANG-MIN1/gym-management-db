"""API_KEY 환경변수를 설정했을 때만 쓰기 엔드포인트가 인증을 요구하는지 확인."""

import pytest


@pytest.fixture
def api_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-secret-key")
    return "test-secret-key"


def _member_payload(today):
    return {
        "name": "홍길동",
        "phone": "010-7777-0001",
        "gender": "M",
        "join_date": today.isoformat(),
        "expiry_date": today.isoformat(),
        "remaining_pt_count": 1,
    }


def test_write_requires_key_when_configured(client, api_key, today):
    assert client.post("/members", json=_member_payload(today)).status_code == 401

    wrong = client.post(
        "/members", json=_member_payload(today), headers={"X-API-Key": "wrong"}
    )
    assert wrong.status_code == 401

    ok = client.post(
        "/members", json=_member_payload(today), headers={"X-API-Key": api_key}
    )
    assert ok.status_code == 201


def test_read_is_open_even_when_key_configured(client, api_key):
    assert client.get("/members").status_code == 200
    assert client.get("/health").status_code == 200


def test_write_is_open_when_key_not_configured(client, today):
    assert client.post("/members", json=_member_payload(today)).status_code == 201
