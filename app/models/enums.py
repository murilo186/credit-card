from enum import Enum


class CardStatus(str, Enum):
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"


class TransactionStatus(str, Enum):
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    CANCELLED = "CANCELLED"


class DeclineReason(str, Enum):
    CARD_BLOCKED = "CARD_BLOCKED"
    INSUFFICIENT_LIMIT = "INSUFFICIENT_LIMIT"
