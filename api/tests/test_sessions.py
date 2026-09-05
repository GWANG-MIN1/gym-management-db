"""PT 예약 업무 규칙 테스트."""

from datetime import timedelta


def test_create_session(client, make_session):
    created = make_session()
    assert created["status"] == "SCHEDULED"
    assert client.get(f"/sessions/{created['session_id']}").status_code == 200


def test_unknown_member_or_trainer_returns_404(client, make_member, make_trainer, today):
    member = make_member()
    trainer = make_trainer()
    date_str = (today + timedelta(days=1)).isoformat()

    no_member = client.post(
        "/sessions",
        json={
            "member_id": 99999,
            "trainer_id": trainer["trainer_id"],
            "session_date": date_str,
            "session_time": "10:00",
        },
    )
    assert no_member.status_code == 404

    no_trainer = client.post(
        "/sessions",
        json={
            "member_id": member["member_id"],
            "trainer_id": 99999,
            "session_date": date_str,
            "session_time": "10:00",
        },
    )
    assert no_trainer.status_code == 404


def test_invalid_time_is_rejected(client, make_member, make_trainer, today):
    member, trainer = make_member(), make_trainer()
    for bad_time in ["99:99", "24:00", "7:00", "0700"]:
        response = client.post(
            "/sessions",
            json={
                "member_id": member["member_id"],
                "trainer_id": trainer["trainer_id"],
                "session_date": (today + timedelta(days=1)).isoformat(),
                "session_time": bad_time,
            },
        )
        assert response.status_code == 422, f"{bad_time} 이 통과했습니다"


def test_past_date_is_rejected(client, make_member, make_trainer, today):
    member, trainer = make_member(), make_trainer()
    response = client.post(
        "/sessions",
        json={
            "member_id": member["member_id"],
            "trainer_id": trainer["trainer_id"],
            "session_date": (today - timedelta(days=1)).isoformat(),
            "session_time": "10:00",
        },
    )
    assert response.status_code == 422


def test_after_membership_expiry_is_rejected(client, make_member, make_trainer, today):
    member = make_member(expiry_date=(today + timedelta(days=3)).isoformat())
    trainer = make_trainer()
    response = client.post(
        "/sessions",
        json={
            "member_id": member["member_id"],
            "trainer_id": trainer["trainer_id"],
            "session_date": (today + timedelta(days=10)).isoformat(),
            "session_time": "10:00",
        },
    )
    assert response.status_code == 409
    assert "만료" in response.json()["detail"]


def test_no_remaining_pt_is_rejected(client, make_member, make_trainer, today):
    member = make_member(remaining_pt_count=0)
    trainer = make_trainer()
    response = client.post(
        "/sessions",
        json={
            "member_id": member["member_id"],
            "trainer_id": trainer["trainer_id"],
            "session_date": (today + timedelta(days=1)).isoformat(),
            "session_time": "10:00",
        },
    )
    assert response.status_code == 409
    assert "잔여" in response.json()["detail"]


def test_trainer_slot_conflict_returns_409(client, make_member, make_trainer, make_session, today):
    trainer = make_trainer()
    first = make_member(phone="010-0000-0011")
    second = make_member(phone="010-0000-0012")
    slot = {
        "session_date": (today + timedelta(days=2)).isoformat(),
        "session_time": "11:00",
    }
    make_session(member=first, trainer=trainer, **slot)

    response = client.post(
        "/sessions",
        json={"member_id": second["member_id"], "trainer_id": trainer["trainer_id"], **slot},
    )
    assert response.status_code == 409
    assert "트레이너" in response.json()["detail"]


def test_member_double_booking_returns_409(client, make_member, make_trainer, make_session, today):
    member = make_member()
    first_trainer = make_trainer(name="트레이너A")
    second_trainer = make_trainer(name="트레이너B")
    slot = {
        "session_date": (today + timedelta(days=2)).isoformat(),
        "session_time": "13:00",
    }
    make_session(member=member, trainer=first_trainer, **slot)

    response = client.post(
        "/sessions",
        json={"member_id": member["member_id"], "trainer_id": second_trainer["trainer_id"], **slot},
    )
    assert response.status_code == 409
    assert "회원" in response.json()["detail"]


def test_complete_decrements_remaining_pt_count(client, make_member, make_session):
    member = make_member(remaining_pt_count=3)
    created = make_session(member=member)

    completed = client.patch(f"/sessions/{created['session_id']}/complete")
    assert completed.status_code == 200
    assert completed.json()["status"] == "COMPLETED"

    after = client.get(f"/members/{member['member_id']}").json()
    assert after["remaining_pt_count"] == 2


def test_complete_twice_returns_409(client, make_session):
    created = make_session()
    assert client.patch(f"/sessions/{created['session_id']}/complete").status_code == 200
    assert client.patch(f"/sessions/{created['session_id']}/complete").status_code == 409


def test_complete_without_remaining_count_returns_409(client, make_member, make_session):
    member = make_member(remaining_pt_count=1)
    first = make_session(member=member, session_time="09:00")
    second = make_session(
        member=member,
        trainer={"trainer_id": first["trainer_id"]},
        session_time="10:00",
    )

    assert client.patch(f"/sessions/{first['session_id']}/complete").status_code == 200
    conflict = client.patch(f"/sessions/{second['session_id']}/complete")
    assert conflict.status_code == 409

    # 실패했으면 상태도 그대로여야 한다 (같은 트랜잭션에서 롤백)
    assert client.get(f"/sessions/{second['session_id']}").json()["status"] == "SCHEDULED"
    assert client.get(f"/members/{member['member_id']}").json()["remaining_pt_count"] == 0


def test_cancel_rules(client, make_session):
    created = make_session()
    cancelled = client.patch(f"/sessions/{created['session_id']}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "CANCELLED"

    assert client.patch(f"/sessions/{created['session_id']}/cancel").status_code == 409
    assert client.patch(f"/sessions/{created['session_id']}/complete").status_code == 409


def test_cancelled_slot_can_be_rebooked(client, make_session, make_member, today):
    created = make_session()
    assert client.patch(f"/sessions/{created['session_id']}/cancel").status_code == 200

    rebooked = client.post(
        "/sessions",
        json={
            "member_id": created["member_id"],
            "trainer_id": created["trainer_id"],
            "session_date": created["session_date"],
            "session_time": created["session_time"],
        },
    )
    assert rebooked.status_code == 201


def test_completed_session_cannot_be_cancelled(client, make_session):
    created = make_session()
    client.patch(f"/sessions/{created['session_id']}/complete")
    assert client.patch(f"/sessions/{created['session_id']}/cancel").status_code == 409


def test_list_filters(client, make_member, make_trainer, make_session, today):
    member = make_member(remaining_pt_count=5)
    trainer = make_trainer()
    first = make_session(member=member, trainer=trainer, session_time="09:00")
    make_session(member=member, trainer=trainer, session_time="10:00")
    client.patch(f"/sessions/{first['session_id']}/complete")

    assert len(client.get("/sessions").json()) == 2
    assert len(client.get("/sessions?status=COMPLETED").json()) == 1
    assert len(client.get(f"/sessions?member_id={member['member_id']}").json()) == 2
    assert len(client.get("/sessions?member_id=99999").json()) == 0
    assert len(client.get(f"/sessions?date_from={(today + timedelta(days=5)).isoformat()}").json()) == 0
    assert client.get("/sessions?status=UNKNOWN").status_code == 422
