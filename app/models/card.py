import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CHAR,
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.database.base import Base
from app.models.enums import CardStatus

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.transaction import Transaction


class Card(Base):
    __tablename__ = "cards"
    __table_args__ = (
        CheckConstraint(
            "total_limit_cents > 0", name="ck_cards_total_limit_cents_positive"
        ),
        CheckConstraint(
            "available_limit_cents >= 0",
            name="ck_cards_available_limit_cents_non_negative",
        ),
        CheckConstraint(
            "available_limit_cents <= total_limit_cents",
            name="ck_cards_available_limit_cents_within_total",
        ),
        Index("ix_cards_customer_id", "customer_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("customers.id"), nullable=False
    )
    last_four_digits: Mapped[str] = mapped_column(CHAR(4), nullable=False)
    total_limit_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    available_limit_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[CardStatus] = mapped_column(
        Enum(CardStatus, native_enum=False, length=7),
        nullable=False,
        default=CardStatus.ACTIVE,
        server_default=CardStatus.ACTIVE.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("TIMEZONE('utc', now())"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("TIMEZONE('utc', now())"),
        onupdate=lambda: datetime.now(UTC),
    )

    customer: Mapped["Customer"] = relationship(back_populates="cards")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="card")
