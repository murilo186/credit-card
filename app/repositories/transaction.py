import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.card import Card
from app.models.transaction import Transaction


class TransactionRepository:
    """Persist transactions and retrieve cards for authorization."""

    def get_card_for_update(self, db: Session, card_id: uuid.UUID) -> Card | None:
        statement = select(Card).where(Card.id == card_id).with_for_update()
        return db.scalar(statement)

    def get_by_card_and_idempotency_key(
        self,
        db: Session,
        card_id: uuid.UUID,
        idempotency_key: str,
    ) -> Transaction | None:
        statement = select(Transaction).where(
            Transaction.card_id == card_id,
            Transaction.idempotency_key == idempotency_key,
        )
        return db.scalar(statement)

    def add(self, db: Session, transaction: Transaction) -> None:
        db.add(transaction)
