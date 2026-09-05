def test_create_and_list_trainer(client, make_trainer):
    created = make_trainer()
    assert client.get(f"/trainers/{created['trainer_id']}").status_code == 200
    assert len(client.get("/trainers").json()) == 1


def test_missing_trainer_returns_404(client):
    assert client.get("/trainers/12345").status_code == 404


def test_negative_career_returns_422(client):
    response = client.post(
        "/trainers", json={"name": "이코치", "specialty": "재활", "career_year": -1}
    )
    assert response.status_code == 422


def test_duplicate_exercise_name_returns_409(client, make_exercise):
    make_exercise(name="데드리프트")
    response = client.post("/exercises", json={"name": "데드리프트", "part": "등"})
    assert response.status_code == 409
