def test_create_and_filter_workout_log(client, make_member, make_exercise):
    member = make_member()
    exercise = make_exercise()

    created = client.post(
        "/workouts",
        json={
            "member_id": member["member_id"],
            "exercise_id": exercise["exercise_id"],
            "weight": "80.00",
            "sets": 3,
            "reps": 10,
            "feedback": "자세 좋음",
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["log_date"] is not None  # DB 기본값

    assert len(client.get(f"/workouts?member_id={member['member_id']}").json()) == 1
    assert len(client.get("/workouts?member_id=99999").json()) == 0


def test_workout_requires_existing_member(client, make_exercise):
    exercise = make_exercise()
    response = client.post(
        "/workouts",
        json={"member_id": 99999, "exercise_id": exercise["exercise_id"], "sets": 3, "reps": 10},
    )
    assert response.status_code == 404


def test_workout_rejects_non_positive_sets(client, make_member, make_exercise):
    member, exercise = make_member(), make_exercise()
    response = client.post(
        "/workouts",
        json={
            "member_id": member["member_id"],
            "exercise_id": exercise["exercise_id"],
            "sets": 0,
            "reps": 10,
        },
    )
    assert response.status_code == 422


def test_create_and_filter_payment(client, make_member):
    member = make_member()
    created = client.post(
        "/payments",
        json={
            "member_id": member["member_id"],
            "amount": "300000.00",
            "method": "Card",
            "category": "PT",
        },
    )
    assert created.status_code == 201, created.text

    assert len(client.get("/payments?category=PT").json()) == 1
    assert len(client.get("/payments?category=Visit").json()) == 0


def test_payment_rejects_invalid_method_and_amount(client, make_member):
    member = make_member()
    bad_method = client.post(
        "/payments",
        json={
            "member_id": member["member_id"],
            "amount": "10000",
            "method": "Bitcoin",
            "category": "PT",
        },
    )
    assert bad_method.status_code == 422

    bad_amount = client.post(
        "/payments",
        json={
            "member_id": member["member_id"],
            "amount": "-1",
            "method": "Card",
            "category": "PT",
        },
    )
    assert bad_amount.status_code == 422
