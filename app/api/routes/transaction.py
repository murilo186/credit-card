import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.transaction import TransactionRepository
from app.schemas.transaction import (
    TransactionCreate,
    TransactionPage,
    TransactionResponse,
)
from app.services.transaction import TransactionService

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
    return transaction_service.authorize_transaction(
        db,
        card_id,
        transaction_data,
        idempotency_key,
    )


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
    transactions = transaction_service.list_transactions(
        db,
        card_id,
        page,
        page_size,
    )
    return TransactionPage(items=transactions, page=page, page_size=page_size)


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
    return transaction_service.cancel_transaction(db, transaction_id)
