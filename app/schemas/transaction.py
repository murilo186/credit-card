import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import DeclineReason, TransactionStatus


class TransactionCreate(BaseModel):
    merchant: str = Field(min_length=1, max_length=255)
    amount_cents: int = Field(gt=0)

    @field_validator("merchant", mode="before")
    @classmethod
    def strip_and_validate_merchant(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    card_id: uuid.UUID
    idempotency_key: str
    merchant: str
    amount_cents: int
    status: TransactionStatus
    decline_reason: DeclineReason | None
    created_at: datetime
    cancelled_at: datetime | None


class TransactionPage(BaseModel):
    items: list[TransactionResponse]
    page: int
    page_size: int
