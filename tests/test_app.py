from fastapi.testclient import TestClient


def test_root_returns_health_envelope(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"

