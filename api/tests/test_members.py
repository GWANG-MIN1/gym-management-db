from datetime import timedelta


def test_create_and_get_member(client, make_member):
    created = make_member()
    assert created["member_id"] > 0
    assert created["created_at"] is not None  # DB 기본값(CURRENT_DATE)

    fetched = client.get(f"/members/{created['member_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["phone"] == created["phone"]


def test_get_missing_member_returns_404(client):
    assert client.get("/members/99999").status_code == 404


def test_duplicate_phone_returns_409(client, make_member):
    make_member(phone="010-1234-5678")
    response = client.post(
        "/members",
        json={
            "name": "다른사람",
            "phone": "010-1234-5678",
            "gender": "F",
            "join_date": "2026-01-01",
            "expiry_date": "2026-12-31",
            "remaining_pt_count": 0,
        },
    )
    assert response.status_code == 409
    assert "전화번호" in response.json()["detail"]


def test_invalid_gender_returns_422(client, today):
    response = client.post(
        "/members",
        json={
            "name": "홍길동",
            "phone": "010-9999-9999",
            "gender": "X",
            "join_date": today.isoformat(),
            "expiry_date": (today + timedelta(days=30)).isoformat(),
        },
    )
    assert response.status_code == 422


def test_expiry_before_join_returns_422(client, today):
    response = client.post(
        "/members",
        json={
            "name": "홍길동",
            "phone": "010-8888-8888",
            "gender": "M",
            "join_date": today.isoformat(),
            "expiry_date": (today - timedelta(days=1)).isoformat(),
        },
    )
    assert response.status_code == 422


def test_list_is_paginated(client, make_member):
    for i in range(5):
        make_member(phone=f"010-0000-10{i:02d}")

    assert len(client.get("/members").json()) == 5
    assert len(client.get("/members?limit=2").json()) == 2

    second_page = client.get("/members?limit=2&offset=2").json()
    assert [m["phone"] for m in second_page] == ["010-0000-1002", "010-0000-1003"]

    # limit 상한을 넘기면 422 (전체 스캔 유도 방지)
    assert client.get("/members?limit=9999").status_code == 422
