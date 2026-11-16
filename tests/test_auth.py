def test_health(client) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_user(client, user_data) -> None:
    response = client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == user_data["username"]
    assert body["email"] == user_data["email"]
    assert body["status"] == "active"
    assert "password" not in body
    assert "password_hash" not in body


def test_register_duplicate_username(client, user_data) -> None:
    client.post("/api/v1/auth/register", json=user_data)

    response = client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 409


def test_login_and_read_current_user(client, user_data) -> None:
    client.post("/api/v1/auth/register", json=user_data)

    login = client.post(
        "/api/v1/auth/login",
        json={"username": user_data["username"], "password": user_data["password"]},
    )

    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert me.status_code == 200
    assert me.json()["username"] == user_data["username"]


def test_login_with_wrong_password(client, user_data) -> None:
    client.post("/api/v1/auth/register", json=user_data)

    response = client.post(
        "/api/v1/auth/login",
        json={"username": user_data["username"], "password": "WrongPass123"},
    )

    assert response.status_code == 401


def test_me_without_token(client) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_me_with_invalid_token(client) -> None:
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-token"}
    )

    assert response.status_code == 401
