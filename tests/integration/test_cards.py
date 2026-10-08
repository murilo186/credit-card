import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.card import CardResponse

client = TestClient(app)


def create_customer() -> str:
    response = client.post(
        "/api/v1/customers", json={"name": f"Cliente Fictício {uuid.uuid4()}"}
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_card(customer_id: str, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "last_four_digits": "1234",
        "total_limit_cents": 10_000,
    }
    payload.update(overrides)
    response = client.post(f"/api/v1/customers/{customer_id}/cards", json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_card_with_initial_limit_and_active_status() -> None:
    card = create_card(create_customer())

    assert uuid.UUID(str(card["id"]))
    assert card["available_limit_cents"] == card["total_limit_cents"] == 10_000
    assert card["status"] == "ACTIVE"
    assert CardResponse.model_validate(card)


def test_create_card_rejects_unknown_customer() -> None:
    response = client.post(
        f"/api/v1/customers/{uuid.uuid4()}/cards",
        json={"last_four_digits": "1234", "total_limit_cents": 10_000},
    )

    assert response.status_code == 404


@pytest.mark.parametrize("total_limit_cents", [0, -1])
def test_create_card_rejects_non_positive_limit(total_limit_cents: int) -> None:
    response = client.post(
        f"/api/v1/customers/{create_customer()}/cards",
        json={"last_four_digits": "1234", "total_limit_cents": total_limit_cents},
    )

    assert response.status_code == 422


@pytest.mark.parametrize("last_four_digits", ["123", "12345", "12a4"])
def test_create_card_rejects_invalid_last_four_digits(last_four_digits: str) -> None:
    response = client.post(
        f"/api/v1/customers/{create_customer()}/cards",
        json={"last_four_digits": last_four_digits, "total_limit_cents": 10_000},
    )

    assert response.status_code == 422


def test_get_card_returns_existing_card() -> None:
    created_card = create_card(create_customer())

    response = client.get(f"/api/v1/cards/{created_card['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created_card["id"]


@pytest.mark.parametrize(
    ("method", "path_suffix"),
    [("get", ""), ("post", "/block"), ("post", "/unblock")],
)
def test_card_operations_reject_unknown_card(method: str, path_suffix: str) -> None:
    response = getattr(client, method)(f"/api/v1/cards/{uuid.uuid4()}{path_suffix}")

    assert response.status_code == 404


def test_block_and_unblock_preserve_limits() -> None:
    created_card = create_card(create_customer())
    card_id = created_card["id"]
    initial_limit = created_card["available_limit_cents"]

    blocked = client.post(f"/api/v1/cards/{card_id}/block")
    blocked_again = client.post(f"/api/v1/cards/{card_id}/block")
    unblocked = client.post(f"/api/v1/cards/{card_id}/unblock")
    unblocked_again = client.post(f"/api/v1/cards/{card_id}/unblock")

    for response in (blocked, blocked_again, unblocked, unblocked_again):
        assert response.status_code == 200
        assert response.json()["available_limit_cents"] == initial_limit
        assert response.json()["total_limit_cents"] == created_card["total_limit_cents"]

    assert blocked.json()["status"] == blocked_again.json()["status"] == "BLOCKED"
    assert unblocked.json()["status"] == unblocked_again.json()["status"] == "ACTIVE"
