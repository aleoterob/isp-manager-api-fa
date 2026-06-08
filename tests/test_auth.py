from fastapi.testclient import TestClient


def csrf(client: TestClient) -> str:
    response = client.get("/auth/csrf")
    assert response.status_code == 200
    return response.json()["data"]["token"]


def test_signup_creates_user_and_sets_session_cookies(client: TestClient) -> None:
    token = csrf(client)
    response = client.post(
        "/auth/signup",
        headers={"x-csrf-token": token},
        json={
            "name": "E2E Signup",
            "email": "signup@example.com",
            "password": "Password123",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == "signup@example.com"
    assert "access_token" in response.cookies


def test_login_me_refresh_logout_with_cookie_jar(client: TestClient) -> None:
    token = csrf(client)
    client.post(
        "/auth/signup",
        headers={"x-csrf-token": token},
        json={
            "name": "E2E Session",
            "email": "session@example.com",
            "password": "Password123",
        },
    )

    client.post("/auth/logout", headers={"x-csrf-token": token})
    token = csrf(client)
    login = client.post(
        "/auth/login",
        headers={"x-csrf-token": token},
        json={"email": "session@example.com", "password": "Password123"},
    )
    assert login.status_code == 200
    user_id = login.json()["data"]["id"]

    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["data"]["id"] == user_id

    refreshed = client.post("/auth/refresh", headers={"x-csrf-token": token})
    assert refreshed.status_code == 200
    assert refreshed.json()["data"]["id"] == user_id

    logout = client.post("/auth/logout", headers={"x-csrf-token": token})
    assert logout.status_code == 200
    assert client.get("/auth/me").status_code == 401

