def test_duplicate_email_rejected(client):
    payload = {"email": "dave@test.com", "password": "test1234"}
    first = client.post("/auth/register", json=payload)
    second = client.post("/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_weak_password_rejected(client):
    resp = client.post(
        "/auth/register", json={"email": "erin@test.com", "password": "abc"}
    )
    assert resp.status_code == 422