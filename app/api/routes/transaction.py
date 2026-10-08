import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.transaction import TransactionRepository
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.services.transaction import TransactionCardNotFoundError, TransactionService

router = APIRouter(prefix="/api/v1/cards", tags=["Transações"])
transaction_service = TransactionService(TransactionRepository())


@router.post(
    "/{card_id}/transactions",
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
