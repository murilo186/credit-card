import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_authorizable_card() -> str:
    customer = client.post(
        "/api/v1/customers", json={"name": f"Cliente Fictício {uuid.uuid4()}"}
    )
    assert customer.status_code == 201

    card = client.post(
        f"/api/v1/customers/{customer.json()['id']}/cards",
        json={"last_four_digits": "8642", "total_limit_cents": 10_000},
    )
    assert card.status_code == 201
    return card.json()["id"]


def authorize(card_id: str, amount_cents: int) -> dict[str, object]:
    response = client.post(
        f"/api/v1/cards/{card_id}/transactions",
        headers={"Idempotency-Key": str(uuid.uuid4())},
        json={"merchant": "Loja Fictícia", "amount_cents": amount_cents},
    )
    assert response.status_code == 201
    return response.json()


def get_available_limit(card_id: str) -> int:
    response = client.get(f"/api/v1/cards/{card_id}")
    assert response.status_code == 200
    return response.json()["available_limit_cents"]


def test_lists_transactions_from_newest_to_oldest_with_pagination() -> None:
    card_id = create_authorizable_card()
    first = authorize(card_id, 100)
    second = authorize(card_id, 200)
    third = authorize(card_id, 300)

    first_page = client.get(f"/api/v1/cards/{card_id}/transactions?page=1&page_size=2")
    second_page = client.get(f"/api/v1/cards/{card_id}/transactions?page=2&page_size=2")

    assert first_page.status_code == second_page.status_code == 200
    assert [item["id"] for item in first_page.json()["items"]] == [
        third["id"],
        second["id"],
    ]
    assert [item["id"] for item in second_page.json()["items"]] == [first["id"]]
    assert first_page.json()["page"] == 1
    assert first_page.json()["page_size"] == 2


def test_list_transactions_rejects_unknown_card() -> None:
    response = client.get(f"/api/v1/cards/{uuid.uuid4()}/transactions")

    assert response.status_code == 404


def test_rn25_cancels_approved_transaction_and_restores_limit() -> None:
    card_id = create_authorizable_card()
    transaction = authorize(card_id, 4_000)
    assert get_available_limit(card_id) == 6_000

    response = client.post(f"/api/v1/transactions/{transaction['id']}/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"
    assert response.json()["cancelled_at"] is not None
    assert response.json()["amount_cents"] == 4_000
    assert get_available_limit(card_id) == 10_000


def test_rn26_rejects_second_cancellation() -> None:
    card_id = create_authorizable_card()
    transaction = authorize(card_id, 4_000)

    first_cancellation = client.post(f"/api/v1/transactions/{transaction['id']}/cancel")
    second_cancellation = client.post(
        f"/api/v1/transactions/{transaction['id']}/cancel"
    )

    assert first_cancellation.status_code == 200
    assert second_cancellation.status_code == 409
    assert get_available_limit(card_id) == 10_000


def test_rn30_rejects_cancellation_of_declined_transaction() -> None:
    card_id = create_authorizable_card()
    transaction = authorize(card_id, 10_001)
    assert transaction["status"] == "DECLINED"

    response = client.post(f"/api/v1/transactions/{transaction['id']}/cancel")

    assert response.status_code == 409
    assert get_available_limit(card_id) == 10_000


def test_rejects_cancellation_of_unknown_transaction() -> None:
    response = client.post(f"/api/v1/transactions/{uuid.uuid4()}/cancel")

    assert response.status_code == 404
