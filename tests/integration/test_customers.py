import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.customer import CustomerResponse

client = TestClient(app)


def test_create_customer_returns_trimmed_name_and_response_schema() -> None:
    response = client.post("/api/v1/customers", json={"name": "  Cliente Fictício  "})

    assert response.status_code == 201
    body = response.json()
    assert uuid.UUID(body["id"])
    assert body["name"] == "Cliente Fictício"
    assert body["created_at"]
    assert CustomerResponse.model_validate(body)


def test_create_customer_rejects_empty_name() -> None:
    response = client.post("/api/v1/customers", json={"name": ""})

    assert response.status_code == 422


def test_create_customer_rejects_name_with_only_spaces() -> None:
    response = client.post("/api/v1/customers", json={"name": "   "})

    assert response.status_code == 422
