import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.transaction import TransactionRepository
from app.schemas.transaction import (
    TransactionCreate,
    TransactionPage,
    TransactionResponse,
)
from app.services.transaction import (
    LimitRestorationError,
    TransactionCardNotFoundError,
    TransactionIdempotencyConflictError,
    TransactionNotCancelableError,
    TransactionNotFoundError,
    TransactionService,
)

router = APIRouter(prefix="/api/v1", tags=["Transações"])
transaction_service = TransactionService(TransactionRepository())


@router.post(
    "/cards/{card_id}/transactions",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Autorizar tentativa de compra",
    description=(
        "Autoriza ou recusa uma compra fictícia. A redução de limite e o registro de "
        "uma compra aprovada ocorrem na mesma transação de banco."
    ),
)
def authorize_transaction(
    card_id: uuid.UUID,
    transaction_data: TransactionCreate,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    db: Annotated[Session, Depends(get_db)],
) -> TransactionResponse:
    try:
        return transaction_service.authorize_transaction(
            db,
            card_id,
            transaction_data,
            idempotency_key,
        )
    except TransactionCardNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cartão não encontrado.",
        ) from error
    except TransactionIdempotencyConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A Idempotency-Key foi reutilizada com outro payload.",
        ) from error


@router.get(
    "/cards/{card_id}/transactions",
    response_model=TransactionPage,
    summary="Consultar histórico de transações",
    description=(
        "Retorna as transações do cartão da mais recente para a mais antiga, com "
        "paginação simples."
    ),
)
def list_transactions(
    card_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> TransactionPage:
    try:
        transactions = transaction_service.list_transactions(
            db,
            card_id,
            page,
            page_size,
        )
        return TransactionPage(items=transactions, page=page, page_size=page_size)
    except TransactionCardNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cartão não encontrado.",
        ) from error


@router.post(
    "/transactions/{transaction_id}/cancel",
    response_model=TransactionResponse,
    summary="Cancelar transação aprovada",
    description=(
        "Cancela uma transação APPROVED e devolve o limite no mesmo commit. "
        "Transações recusadas ou já canceladas não podem ser canceladas."
    ),
)
def cancel_transaction(
    transaction_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> TransactionResponse:
    try:
        return transaction_service.cancel_transaction(db, transaction_id)
    except TransactionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transação não encontrada.",
        ) from error
    except (TransactionNotCancelableError, LimitRestorationError) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A transação não pode ser cancelada.",
        ) from error
