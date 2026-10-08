import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi.testclient import TestClient

from app.database.session import SessionLocal
from app.main import app
from app.repositories.transaction import TransactionRepository
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.services.transaction import TransactionService

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


def authorize(
    card_id: str,
    amount_cents: int,
    merchant: str = "Loja Fictícia",
    idempotency_key: str | None = None,
):
    return client.post(
        f"/api/v1/cards/{card_id}/transactions",
        headers={"Idempotency-Key": idempotency_key or str(uuid.uuid4())},
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


def test_rn23_returns_original_approved_transaction_for_repeated_request() -> None:
    card_id = create_authorizable_card()
    idempotency_key = str(uuid.uuid4())

    first_response = authorize(card_id, 4_000, idempotency_key=idempotency_key)
    retry_response = authorize(card_id, 4_000, idempotency_key=idempotency_key)

    assert first_response.status_code == retry_response.status_code == 201
    assert retry_response.json()["id"] == first_response.json()["id"]
    assert retry_response.json()["status"] == "APPROVED"
    assert get_available_limit(card_id) == 6_000


def test_rn23_returns_original_declined_transaction_for_repeated_request() -> None:
    card_id = create_authorizable_card()
    idempotency_key = str(uuid.uuid4())

    first_response = authorize(card_id, 10_001, idempotency_key=idempotency_key)
    retry_response = authorize(card_id, 10_001, idempotency_key=idempotency_key)

    assert first_response.status_code == retry_response.status_code == 201
    assert retry_response.json()["id"] == first_response.json()["id"]
    assert retry_response.json()["status"] == "DECLINED"
    assert get_available_limit(card_id) == 10_000


@pytest.mark.parametrize(
    ("amount_cents", "merchant"),
    [(4_001, "Loja Fictícia"), (4_000, "Outra Loja Fictícia")],
)
def test_rn24_rejects_reused_key_with_different_payload(
    amount_cents: int,
    merchant: str,
) -> None:
    card_id = create_authorizable_card()
    idempotency_key = str(uuid.uuid4())
    first_response = authorize(card_id, 4_000, idempotency_key=idempotency_key)

    conflict_response = authorize(
        card_id,
        amount_cents,
        merchant,
        idempotency_key,
    )

    assert first_response.status_code == 201
    assert conflict_response.status_code == 409
    assert get_available_limit(card_id) == 6_000


def test_concurrent_transactions_do_not_overdraw_available_limit() -> None:
    card_id = create_authorizable_card()
    transaction_service = TransactionService(TransactionRepository())
    start_barrier = Barrier(2)

    def authorize_in_own_session(idempotency_key: str) -> str:
        with SessionLocal() as db:
            start_barrier.wait()
            transaction = transaction_service.authorize_transaction(
                db,
                uuid.UUID(card_id),
                TransactionCreate(merchant="Loja Fictícia", amount_cents=7_000),
                idempotency_key,
            )
            return transaction.status.value

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(
            executor.map(
                authorize_in_own_session,
                [str(uuid.uuid4()), str(uuid.uuid4())],
            )
        )

    assert sorted(outcomes) == ["APPROVED", "DECLINED"]
    assert get_available_limit(card_id) == 3_000
