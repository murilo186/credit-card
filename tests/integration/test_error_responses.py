import uuid

from fastapi.testclient import TestClient

from app.api.routes import customer as customer_route
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


def assert_error_shape(response, status_code: int, code: str) -> None:
    assert response.status_code == status_code
    assert response.json() == {
        "error": {
            "code": code,
            "message": response.json()["error"]["message"],
            "details": {},
        }
    }


def test_returns_standard_error_for_unknown_customer() -> None:
    response = client.post(
        f"/api/v1/customers/{uuid.uuid4()}/cards",
        json={"last_four_digits": "1234", "total_limit_cents": 100},
    )

    assert_error_shape(response, 404, "CUSTOMER_NOT_FOUND")


def test_returns_standard_error_for_unknown_card() -> None:
    response = client.get(f"/api/v1/cards/{uuid.uuid4()}")

    assert_error_shape(response, 404, "CARD_NOT_FOUND")


def test_returns_standard_error_for_invalid_payload() -> None:
    response = client.post("/api/v1/customers", json={"name": "   "})

    assert_error_shape(response, 422, "VALIDATION_ERROR")


def test_returns_standard_error_for_unknown_route() -> None:
    response = client.get("/api/v1/unknown")

    assert_error_shape(response, 404, "NOT_FOUND")


def test_returns_standard_error_for_idempotency_conflict() -> None:
    customer = client.post("/api/v1/customers", json={"name": "Cliente Fictício"})
    card = client.post(
        f"/api/v1/customers/{customer.json()['id']}/cards",
        json={"last_four_digits": "1234", "total_limit_cents": 1_000},
    )
    idempotency_key = str(uuid.uuid4())
    headers = {"Idempotency-Key": idempotency_key}
    first_response = client.post(
        f"/api/v1/cards/{card.json()['id']}/transactions",
        headers=headers,
        json={"merchant": "Loja Fictícia", "amount_cents": 100},
    )
    conflict_response = client.post(
        f"/api/v1/cards/{card.json()['id']}/transactions",
        headers=headers,
        json={"merchant": "Outra Loja Fictícia", "amount_cents": 100},
    )

    assert first_response.status_code == 201
    assert_error_shape(conflict_response, 409, "IDEMPOTENCY_CONFLICT")


def test_returns_non_sensitive_error_for_unexpected_failure(monkeypatch) -> None:
    def raise_unexpected_error(*args, **kwargs):
        del args, kwargs
        raise RuntimeError("database_password=should_not_be_exposed")

    monkeypatch.setattr(
        customer_route.customer_service,
        "create_customer",
        raise_unexpected_error,
    )

    response = client.post("/api/v1/customers", json={"name": "Cliente Fictício"})

    assert_error_shape(response, 500, "INTERNAL_ERROR")
    assert "database_password" not in response.text
    assert response.headers["X-Request-ID"]
