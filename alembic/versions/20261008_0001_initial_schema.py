"""initial schema

Revision ID: 20261008_0001
Revises:
Create Date: 2026-10-08 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261008_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("TIMEZONE('utc', now())"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "cards",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("customer_id", sa.UUID(), nullable=False),
        sa.Column("last_four_digits", sa.CHAR(length=4), nullable=False),
        sa.Column("total_limit_cents", sa.BigInteger(), nullable=False),
        sa.Column("available_limit_cents", sa.BigInteger(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "BLOCKED", native_enum=False, length=7),
            server_default="ACTIVE",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("TIMEZONE('utc', now())"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("TIMEZONE('utc', now())"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "available_limit_cents >= 0",
            name="ck_cards_available_limit_cents_non_negative",
        ),
        sa.CheckConstraint(
            "available_limit_cents <= total_limit_cents",
            name="ck_cards_available_limit_cents_within_total",
        ),
        sa.CheckConstraint(
            "total_limit_cents > 0", name="ck_cards_total_limit_cents_positive"
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cards_customer_id", "cards", ["customer_id"], unique=False)
    op.create_table(
        "transactions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("card_id", sa.UUID(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("merchant", sa.String(length=255), nullable=False),
        sa.Column("amount_cents", sa.BigInteger(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("APPROVED", "DECLINED", "CANCELLED", native_enum=False, length=9),
            nullable=False,
        ),
        sa.Column(
            "decline_reason",
            sa.Enum("CARD_BLOCKED", "INSUFFICIENT_LIMIT", native_enum=False, length=18),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("TIMEZONE('utc', now())"),
            nullable=False,
        ),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "amount_cents > 0", name="ck_transactions_amount_cents_positive"
        ),
        sa.ForeignKeyConstraint(["card_id"], ["cards.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "card_id", "idempotency_key", name="uq_transactions_card_id_idempotency_key"
        ),
    )
    op.create_index(
        "ix_transactions_card_id", "transactions", ["card_id"], unique=False
    )
    op.create_index(
        "ix_transactions_card_id_created_at",
        "transactions",
        ["card_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_transactions_card_id_created_at", table_name="transactions")
    op.drop_index("ix_transactions_card_id", table_name="transactions")
    op.drop_table("transactions")
    op.drop_index("ix_cards_customer_id", table_name="cards")
    op.drop_table("cards")
    op.drop_table("customers")
