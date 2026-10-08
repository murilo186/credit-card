import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.card import Card
from app.models.enums import CardStatus, DeclineReason, TransactionStatus
from app.models.transaction import Transaction
from app.repositories.transaction import TransactionRepository
from app.schemas.transaction import TransactionCreate


class TransactionCardNotFoundError(Exception):
    """Raised when a requested card does not exist."""


class TransactionIdempotencyConflictError(Exception):
    """Raised when an idempotency key is reused with another payload."""


class TransactionNotFoundError(Exception):
    """Raised when a requested transaction does not exist."""


class TransactionNotCancelableError(Exception):
    """Raised when a transaction is not approved and cannot be cancelled."""


class LimitRestorationError(Exception):
    """Raised when restoring a limit would exceed the configured total."""


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
        """Authorize or return a prior transaction within one database transaction."""
        try:
            with db.begin():
                card = self._repository.get_card_for_update(db, card_id)
                if card is None:
                    raise TransactionCardNotFoundError

                existing_transaction = self._repository.get_by_card_and_idempotency_key(
                    db,
                    card.id,
                    idempotency_key,
                )
                if existing_transaction is not None:
                    self._ensure_matching_payload(
                        existing_transaction,
                        transaction_data,
                    )
                    transaction = existing_transaction
                else:
                    transaction = self._create_transaction(
                        card.id,
                        idempotency_key,
                        transaction_data,
                    )
                    self._authorize_or_decline(card, transaction)
                    self._repository.add(db, transaction)

            db.refresh(transaction)
            return transaction
        except IntegrityError as error:
            db.rollback()
            if not self._is_idempotency_key_violation(error):
                raise

            existing_transaction = self._repository.get_by_card_and_idempotency_key(
                db,
                card_id,
                idempotency_key,
            )
            if existing_transaction is None:
                raise

            self._ensure_matching_payload(existing_transaction, transaction_data)
            db.refresh(existing_transaction)
            return existing_transaction
        except Exception:
            db.rollback()
            raise

    def list_transactions(
        self,
        db: Session,
        card_id: uuid.UUID,
        page: int,
        page_size: int,
    ) -> list[Transaction]:
        if self._repository.get_card(db, card_id) is None:
            raise TransactionCardNotFoundError

        return self._repository.list_by_card(
            db,
            card_id,
            offset=(page - 1) * page_size,
            limit=page_size,
        )

    def cancel_transaction(
        self,
        db: Session,
        transaction_id: uuid.UUID,
    ) -> Transaction:
        """Cancel an approved transaction and restore its limit atomically."""
        initial_transaction = self._repository.get_by_id(db, transaction_id)
        if initial_transaction is None:
            db.rollback()
            raise TransactionNotFoundError

        card_id = initial_transaction.card_id
        db.rollback()

        try:
            with db.begin():
                card = self._repository.get_card_for_update(db, card_id)
                if card is None:
                    raise TransactionCardNotFoundError

                transaction = self._repository.get_by_id_for_update(db, transaction_id)
                if transaction is None:
                    raise TransactionNotFoundError
                if transaction.status is not TransactionStatus.APPROVED:
                    raise TransactionNotCancelableError

                restored_limit = card.available_limit_cents + transaction.amount_cents
                if restored_limit > card.total_limit_cents:
                    raise LimitRestorationError

                transaction.status = TransactionStatus.CANCELLED
                transaction.cancelled_at = datetime.now(UTC)
                card.available_limit_cents = restored_limit

            db.refresh(transaction)
            return transaction
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def _create_transaction(
        card_id: uuid.UUID,
        idempotency_key: str,
        transaction_data: TransactionCreate,
    ) -> Transaction:
        return Transaction(
            card_id=card_id,
            idempotency_key=idempotency_key,
            merchant=transaction_data.merchant,
            amount_cents=transaction_data.amount_cents,
            status=TransactionStatus.DECLINED,
        )

    def _authorize_or_decline(self, card: Card, transaction: Transaction) -> None:
        if card.status is CardStatus.BLOCKED:
            transaction.decline_reason = DeclineReason.CARD_BLOCKED
        elif card.available_limit_cents < transaction.amount_cents:
            transaction.decline_reason = DeclineReason.INSUFFICIENT_LIMIT
        else:
            card.available_limit_cents -= transaction.amount_cents
            transaction.status = TransactionStatus.APPROVED

    @staticmethod
    def _ensure_matching_payload(
        existing_transaction: Transaction,
        transaction_data: TransactionCreate,
    ) -> None:
        if (
            existing_transaction.amount_cents != transaction_data.amount_cents
            or existing_transaction.merchant != transaction_data.merchant
        ):
            raise TransactionIdempotencyConflictError

    @staticmethod
    def _is_idempotency_key_violation(error: IntegrityError) -> bool:
        diagnostic = getattr(error.orig, "diag", None)
        return (
            getattr(diagnostic, "constraint_name", None)
            == "uq_transactions_card_id_idempotency_key"
        )
