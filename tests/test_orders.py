from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.features.customers.models import Customer
from app.features.users.models import Role, User


def csrf(client: TestClient) -> str:
    return client.get("/auth/csrf").json()["data"]["token"]


def signup(client: TestClient, email: str) -> tuple[str, str]:
    token = csrf(client)
    response = client.post(
        "/auth/signup",
        headers={"x-csrf-token": token},
        json={"name": "E2E User", "email": email, "password": "Password123"},
    )
    return response.json()["data"]["id"], token


def test_orders_without_auth_returns_401(client: TestClient) -> None:
    assert client.get("/orders").status_code == 401


def test_post_orders_as_installer_returns_403(
    client: TestClient, db_session: Session
) -> None:
    _, token = signup(client, "installer@example.com")
    customer = Customer(
        name="Coords Customer",
        address="Street 123",
        city="CABA",
        province="CABA",
        zipCode="1000",
        lat=-34.6,
        lng=-58.38,
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)

    response = client.post(
        "/orders",
        headers={"x-csrf-token": token},
        json={
            "title": "Forbidden order",
            "type": "INSTALLATION",
            "customerId": customer.id,
        },
    )

    assert response.status_code == 403
    assert response.json()["code"] == "AUTH_FORBIDDEN"


def test_post_orders_as_admin_creates_order(
    client: TestClient, db_session: Session
) -> None:
    user_id, token = signup(client, "admin@example.com")
    user = db_session.get(User, user_id)
    assert user is not None
    user.role = Role.ADMIN
    db_session.commit()

    client.post("/auth/logout", headers={"x-csrf-token": token})
    token = csrf(client)
    client.post(
        "/auth/login",
        headers={"x-csrf-token": token},
        json={"email": "admin@example.com", "password": "Password123"},
    )

    customer = Customer(
        name="Order Customer",
        address="Av. Siempre Viva 742",
        city="Springfield",
        province="BA",
        zipCode="1000",
        lat=-34.6037,
        lng=-58.3816,
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)

    response = client.post(
        "/orders",
        headers={"x-csrf-token": token},
        json={
            "title": "Created order",
            "type": "REPAIR",
            "description": "E2E description",
            "customerId": customer.id,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["title"] == "Created order"
    assert body["data"]["type"] == "REPAIR"
    assert body["data"]["customerId"] == customer.id


def test_get_order_returns_404_when_missing(client: TestClient) -> None:
    signup(client, "orders-404@example.com")
    response = client.get("/orders/00000000-0000-4000-8000-000000000099")

    assert response.status_code == 404
    assert response.json()["code"] == "ORD_NOT_FOUND"

