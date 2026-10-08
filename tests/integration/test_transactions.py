import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.transaction import TransactionResponse

client = TestClient(app)


def create_authorizable_card(total_limit_cents: int = 10_000) -> str:
    customer = client.post(
        "/api/v1/customers", json={"name": f"Cliente Fictício {uuid.uuid4()}"}
    )
    assert customer.status_code == 201

    card = client.post(
        f"/api/v1/customers/{customer.json()['id']}/cards",
        json={"last_four_digits": "4321", "total_limit_cents": total_limit_cents},
    )
    assert card.status_code == 201
    return card.json()["id"]


def authorize(card_id: str, amount_cents: int, merchant: str = "Loja Fictícia"):
    return client.post(
        f"/api/v1/cards/{card_id}/transactions",
        headers={"Idempotency-Key": str(uuid.uuid4())},
        json={"merchant": merchant, "amount_cents": amount_cents},
    )


def get_available_limit(card_id: str) -> int:
    response = client.get(f"/api/v1/cards/{card_id}")
    assert response.status_code == 200
    return response.json()["available_limit_cents"]


def test_rn15_approves_transaction_with_sufficient_limit() -> None:
    card_id = create_authorizable_card()

    response = authorize(card_id, 4_000)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "APPROVED"
    assert body["decline_reason"] is None
    assert get_available_limit(card_id) == 6_000
    assert TransactionResponse.model_validate(body)


def test_rn15_approves_transaction_equal_to_available_limit() -> None:
    card_id = create_authorizable_card()

    response = authorize(card_id, 10_000)

    assert response.status_code == 201
    assert response.json()["status"] == "APPROVED"
    assert get_available_limit(card_id) == 0


def test_rn17_declines_transaction_with_insufficient_limit() -> None:
    card_id = create_authorizable_card()

    response = authorize(card_id, 10_001)

    assert response.status_code == 201
    assert response.json()["status"] == "DECLINED"
    assert response.json()["decline_reason"] == "INSUFFICIENT_LIMIT"
    assert get_available_limit(card_id) == 10_000


def test_rn17_declines_transaction_for_blocked_card_without_limit_change() -> None:
    card_id = create_authorizable_card()
    blocked = client.post(f"/api/v1/cards/{card_id}/block")
    assert blocked.status_code == 200

    response = authorize(card_id, 4_000)

    assert response.status_code == 201
    assert response.json()["status"] == "DECLINED"
    assert response.json()["decline_reason"] == "CARD_BLOCKED"
    assert get_available_limit(card_id) == 10_000


@pytest.mark.parametrize("amount_cents", [0, -1])
def test_rn13_rejects_non_positive_amount(amount_cents: int) -> None:
    response = authorize(create_authorizable_card(), amount_cents)

    assert response.status_code == 422


@pytest.mark.parametrize("merchant", ["", "   "])
def test_rn14_rejects_empty_merchant(merchant: str) -> None:
    response = authorize(create_authorizable_card(), 100, merchant)

    assert response.status_code == 422
