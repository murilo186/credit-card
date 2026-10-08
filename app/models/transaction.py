import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.database.base import Base
from app.models.enums import DeclineReason, TransactionStatus

if TYPE_CHECKING:
    from app.models.card import Card


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint(
            "amount_cents > 0", name="ck_transactions_amount_cents_positive"
        ),
        UniqueConstraint(
            "card_id", "idempotency_key", name="uq_transactions_card_id_idempotency_key"
        ),
        Index("ix_transactions_card_id", "card_id"),
        Index("ix_transactions_card_id_created_at", "card_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    card_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("cards.id"), nullable=False
    )
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    merchant: Mapped[str] = mapped_column(String(255), nullable=False)
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus, native_enum=False, length=9), nullable=False
    )
    decline_reason: Mapped[DeclineReason | None] = mapped_column(
        Enum(DeclineReason, native_enum=False, length=18), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("TIMEZONE('utc', now())"),
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    card: Mapped["Card"] = relationship(back_populates="transactions")
