def test_register_success(client):
    resp = client.post(
        "/auth/register", json={"email": "alice@test.com", "password": "test1234"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "alice@test.com"
    assert "hashed_password" not in body
    assert "password" not in body


def test_login_success(client, register_and_login):
    headers = register_and_login("bob@test.com")
    assert "Authorization" in headers
    assert headers["Authorization"].startswith("Bearer ")


def test_login_wrong_password_rejected(client):
    client.post(
        "/auth/register", json={"email": "carol@test.com", "password": "test1234"}
    )
    resp = client.post(
        "/auth/login",
        data={"username": "carol@test.com", "password": "wrongpass"},
    )
    assert resp.status_code == 401