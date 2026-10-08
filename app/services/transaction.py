import uuid

from sqlalchemy.orm import Session

from app.models.enums import CardStatus, DeclineReason, TransactionStatus
from app.models.transaction import Transaction
from app.repositories.transaction import TransactionRepository
from app.schemas.transaction import TransactionCreate


class TransactionCardNotFoundError(Exception):
    """Raised when a requested card does not exist."""


class TransactionService:
    """Coordinate transaction authorization in a single database transaction."""

    def __init__(self, repository: TransactionRepository) -> None:
        self._repository = repository

    def authorize_transaction(
        self,
        db: Session,
        card_id: uuid.UUID,
        transaction_data: TransactionCreate,
        idempotency_key: str,
    ) -> Transaction:
        """Authorize or decline a purchase, committing both changes together."""
        try:
            card = self._repository.get_card_for_update(db, card_id)
            if card is None:
                raise TransactionCardNotFoundError

            transaction = Transaction(
                card_id=card.id,
                idempotency_key=idempotency_key,
                merchant=transaction_data.merchant,
                amount_cents=transaction_data.amount_cents,
                status=TransactionStatus.DECLINED,
            )

            if card.status is CardStatus.BLOCKED:
                transaction.decline_reason = DeclineReason.CARD_BLOCKED
            elif card.available_limit_cents < transaction_data.amount_cents:
                transaction.decline_reason = DeclineReason.INSUFFICIENT_LIMIT
            else:
                card.available_limit_cents -= transaction_data.amount_cents
                transaction.status = TransactionStatus.APPROVED

            self._repository.add(db, transaction)
            db.commit()
            db.refresh(transaction)
            return transaction
        except Exception:
            db.rollback()
            raise
