"""숫자 입력 상한 검증.

상한이 없으면 PostgreSQL INTEGER/BIGINT 범위를 넘는 값이 그대로 DB 까지 내려가
22003(numeric value out of range) 오류가 나고, IntegrityError 가 아니라서
errors.py 가 잡지 못해 500 이 된다. 입력 단계에서 422 로 거른다.
"""

import pytest

from pagination import MAX_OFFSET
from schemas import MAX_CAREER_YEAR, MAX_INT4, MAX_PT_COUNT, MAX_REPS, MAX_SETS

OUT_OF_INT_RANGE = 9_999_999_999
OUT_OF_BIGINT_RANGE = 10**19


def test_remaining_pt_count_upper_bound(client, make_member, today):
    make_member(phone="010-5000-0000", remaining_pt_count=MAX_PT_COUNT)  # 경계값은 통과

    response = client.post(
        "/members",
        json={
            "name": "홍길동",
            "phone": "010-5000-0001",
            "gender": "M",
            "join_date": today.isoformat(),
            "expiry_date": today.isoformat(),
            "remaining_pt_count": OUT_OF_INT_RANGE,
        },
    )
    assert response.status_code == 422


def test_career_year_upper_bound(client, make_trainer):
    make_trainer(name="경력상한", career_year=MAX_CAREER_YEAR)  # 경계값은 통과

    response = client.post(
        "/trainers",
        json={"name": "초과", "specialty": "재활", "career_year": OUT_OF_INT_RANGE},
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("sets", MAX_SETS + 1),
        ("sets", OUT_OF_INT_RANGE),
        ("reps", MAX_REPS + 1),
        ("reps", OUT_OF_INT_RANGE),
    ],
)
def test_workout_sets_and_reps_upper_bound(client, make_member, make_exercise, field, value):
    member, exercise = make_member(), make_exercise()
    payload = {
        "member_id": member["member_id"],
        "exercise_id": exercise["exercise_id"],
        "sets": 3,
        "reps": 10,
    }
    payload[field] = value

    assert client.post("/workouts", json=payload).status_code == 422


@pytest.mark.parametrize("offset", [MAX_OFFSET + 1, OUT_OF_BIGINT_RANGE])
def test_offset_upper_bound(client, offset):
    assert client.get(f"/members?offset={MAX_OFFSET}").status_code == 200  # 경계값은 통과
    assert client.get(f"/members?offset={offset}").status_code == 422


@pytest.mark.parametrize(
    ("path", "payload"),
    [
        (
            "/workouts",
            {"member_id": OUT_OF_INT_RANGE, "exercise_id": 1, "sets": 3, "reps": 10},
        ),
        (
            "/payments",
            {
                "member_id": OUT_OF_INT_RANGE,
                "amount": "10000",
                "method": "Card",
                "category": "PT",
            },
        ),
    ],
)
def test_reference_ids_beyond_integer_range(client, path, payload):
    """INTEGER 범위를 넘는 ID 는 DB 조회 전에 422 로 막는다 (예전에는 INSERT 까지 가서 500)."""
    assert client.post(path, json=payload).status_code == 422


def test_reference_id_at_integer_limit_is_accepted_then_404(client):
    """INTEGER 상한값 자체는 형식상 유효하므로 '없는 회원'(404)으로 처리돼야 한다."""
    response = client.post(
        "/payments",
        json={"member_id": MAX_INT4, "amount": "10000", "method": "Card", "category": "PT"},
    )
    assert response.status_code == 404
