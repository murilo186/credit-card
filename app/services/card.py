import uuid

from sqlalchemy.orm import Session

from app.models.card import Card
from app.models.enums import CardStatus
from app.repositories.card import CardRepository
from app.repositories.customer import CustomerRepository
from app.schemas.card import CardCreate


class CustomerNotFoundError(Exception):
    """Raised when a requested customer does not exist."""


class CardNotFoundError(Exception):
    """Raised when a requested card does not exist."""


class CardService:
    """Coordinate card issuance and status changes."""

    def __init__(
        self,
        card_repository: CardRepository,
        customer_repository: CustomerRepository,
    ) -> None:
        self._card_repository = card_repository
        self._customer_repository = customer_repository

    def create_card(
        self,
        db: Session,
        customer_id: uuid.UUID,
        card_data: CardCreate,
    ) -> Card:
        if self._customer_repository.get_by_id(db, customer_id) is None:
            raise CustomerNotFoundError

        card = Card(
            customer_id=customer_id,
            last_four_digits=card_data.last_four_digits,
            total_limit_cents=card_data.total_limit_cents,
            available_limit_cents=card_data.total_limit_cents,
            status=CardStatus.ACTIVE,
        )
        return self._card_repository.create(db, card)

    def get_card(self, db: Session, card_id: uuid.UUID) -> Card:
        card = self._card_repository.get_by_id(db, card_id)
        if card is None:
            raise CardNotFoundError
        return card

    def block_card(self, db: Session, card_id: uuid.UUID) -> Card:
        card = self.get_card(db, card_id)
        if card.status is CardStatus.BLOCKED:
            return card

        card.status = CardStatus.BLOCKED
        return self._card_repository.update(db, card)

    def unblock_card(self, db: Session, card_id: uuid.UUID) -> Card:
        card = self.get_card(db, card_id)
        if card.status is CardStatus.ACTIVE:
            return card

        card.status = CardStatus.ACTIVE
        return self._card_repository.update(db, card)
