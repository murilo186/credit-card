import uuid
from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.card import CardRepository
from app.repositories.customer import CustomerRepository
from app.schemas.card import CardCreate, CardResponse
from app.services.card import CardNotFoundError, CardService, CustomerNotFoundError

router = APIRouter(prefix="/api/v1", tags=["Cartões"])
card_service = CardService(CardRepository(), CustomerRepository())


def raise_card_not_found() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Cartão não encontrado.",
    )


@router.post(
    "/customers/{customer_id}/cards",
    response_model=CardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Emitir cartão fictício",
    description=(
        "Emite um cartão fictício para um cliente existente usando somente os quatro "
        "dígitos informados e o limite total em centavos."
    ),
)
def create_card(
    customer_id: uuid.UUID,
    card_data: CardCreate,
    db: Annotated[Session, Depends(get_db)],
) -> CardResponse:
    try:
        return card_service.create_card(db, customer_id, card_data)
    except CustomerNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado.",
        ) from error


@router.get(
    "/cards/{card_id}",
    response_model=CardResponse,
    summary="Consultar cartão fictício",
    description="Consulta os dados e o limite atual de um cartão fictício.",
)
def get_card(
    card_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> CardResponse:
    try:
        return card_service.get_card(db, card_id)
    except CardNotFoundError:
        raise_card_not_found()


@router.post(
    "/cards/{card_id}/block",
    response_model=CardResponse,
    summary="Bloquear cartão fictício",
    description=(
        "Altera o status do cartão para BLOCKED sem modificar limites ou transações. "
        "Se já estiver bloqueado, retorna o estado atual."
    ),
)
def block_card(
    card_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> CardResponse:
    try:
        return card_service.block_card(db, card_id)
    except CardNotFoundError:
        raise_card_not_found()


@router.post(
    "/cards/{card_id}/unblock",
    response_model=CardResponse,
    summary="Desbloquear cartão fictício",
    description=(
        "Altera o status do cartão para ACTIVE sem modificar limites ou transações. "
        "Se já estiver ativo, retorna o estado atual."
    ),
)
def unblock_card(
    card_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> CardResponse:
    try:
        return card_service.unblock_card(db, card_id)
    except CardNotFoundError:
        raise_card_not_found()
