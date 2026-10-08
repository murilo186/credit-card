import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CardStatus


class CardCreate(BaseModel):
    last_four_digits: str = Field(pattern=r"^[0-9]{4}$")
    total_limit_cents: int = Field(gt=0)


class CardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID
    last_four_digits: str
    total_limit_cents: int
    available_limit_cents: int
    status: CardStatus
    created_at: datetime
    updated_at: datetime
