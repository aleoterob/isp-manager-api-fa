from fastapi.testclient import TestClient

from app.features.customers.models import Customer


def signup(client: TestClient) -> None:
    csrf = client.get("/auth/csrf").json()["data"]["token"]
    client.post(
        "/auth/signup",
        headers={"x-csrf-token": csrf},
        json={
            "name": "E2E Customers",
            "email": "customers@example.com",
            "password": "Password123",
        },
    )


def test_customers_without_auth_returns_401(client: TestClient) -> None:
    assert client.get("/customers").status_code == 401


def test_customers_with_session_returns_paginated_list(client, db_session) -> None:
    signup(client)
    db_session.add(Customer(name="Alice Customer"))
    db_session.commit()

    response = client.get("/customers?skip=0&take=10")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)

