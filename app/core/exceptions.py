from typing import Any


class DomainError(Exception):
    """Base exception for expected domain failures exposed by the API."""

    status_code = 400
    code = "BAD_REQUEST"
    message = "A requisição é inválida."

    def __init__(self, details: dict[str, Any] | None = None) -> None:
        self.details = details or {}
        super().__init__(self.message)


class CustomerNotFoundError(DomainError):
    status_code = 404
    code = "CUSTOMER_NOT_FOUND"
    message = "Cliente não encontrado."


class CardNotFoundError(DomainError):
    status_code = 404
    code = "CARD_NOT_FOUND"
    message = "Cartão não encontrado."


class TransactionNotFoundError(DomainError):
    status_code = 404
    code = "TRANSACTION_NOT_FOUND"
    message = "Transação não encontrada."


class IdempotencyConflictError(DomainError):
    status_code = 409
    code = "IDEMPOTENCY_CONFLICT"
    message = "A Idempotency-Key foi reutilizada com outro payload."


class TransactionNotCancelableError(DomainError):
    status_code = 409
    code = "TRANSACTION_NOT_CANCELLABLE"
    message = "A transação não pode ser cancelada."
