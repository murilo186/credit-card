from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.customer import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerResponse
from app.services.customer import CustomerService

router = APIRouter(prefix="/api/v1/customers", tags=["Clientes"])
customer_service = CustomerService(CustomerRepository())


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar cliente fictício",
    description=(
        "Cria um cliente fictício usando somente o nome informado. "
        "A API não solicita nem armazena dados pessoais reais."
    ),
)
def create_customer(
    customer_data: CustomerCreate,
    db: Annotated[Session, Depends(get_db)],
) -> CustomerResponse:
    """Create a fictional customer."""
    return customer_service.create_customer(db, customer_data)
