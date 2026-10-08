import pytest
from sqlalchemy.exc import IntegrityError

from app.database.session import SessionLocal
from app.models.card import Card
from app.models.customer import Customer
from app.models.enums import CardStatus, TransactionStatus
from app.models.transaction import Transaction


def build_card(db, total_limit_cents: int, available_limit_cents: int) -> Card:
    customer = Customer(name="Cliente Fictício")
    db.add(customer)
    db.flush()
    return Card(
        customer_id=customer.id,
        last_four_digits="1234",
        total_limit_cents=total_limit_cents,
        available_limit_cents=available_limit_cents,
        status=CardStatus.ACTIVE,
    )


@pytest.mark.parametrize(
    ("total_limit_cents", "available_limit_cents"),
    [(0, 0), (100, -1), (100, 101)],
)
def test_database_enforces_card_limit_invariants(
    total_limit_cents: int,
    available_limit_cents: int,
) -> None:
    with SessionLocal() as db:
        db.add(build_card(db, total_limit_cents, available_limit_cents))

        with pytest.raises(IntegrityError):
            db.flush()

        db.rollback()


def test_database_enforces_positive_transaction_amount() -> None:
    with SessionLocal() as db:
        card = build_card(db, 100, 100)
        db.add(card)
        db.flush()
        db.add(
            Transaction(
                card_id=card.id,
                idempotency_key="constraint-test",
                merchant="Loja Fictícia",
                amount_cents=0,
                status=TransactionStatus.DECLINED,
            )
        )

        with pytest.raises(IntegrityError):
            db.flush()

        db.rollback()
