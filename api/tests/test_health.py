def test_health_checks_database(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["read_replica"] is False


def test_liveness_does_not_touch_database(client):
    assert client.get("/health/live").status_code == 200
