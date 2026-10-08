import uuid

from sqlalchemy.orm import Session

from app.models.card import Card


class CardRepository:
    """Persist card entities without business rules."""

    def create(self, db: Session, card: Card) -> Card:
        db.add(card)
        db.commit()
        db.refresh(card)
        return card

    def get_by_id(self, db: Session, card_id: uuid.UUID) -> Card | None:
        return db.get(Card, card_id)

    def update(self, db: Session, card: Card) -> Card:
        db.commit()
        db.refresh(card)
        return card
