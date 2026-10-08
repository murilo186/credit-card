from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.repositories.customer import CustomerRepository
from app.schemas.customer import CustomerCreate


class CustomerService:
    """Coordinate customer registration."""

    def __init__(self, repository: CustomerRepository) -> None:
        self._repository = repository

    def create_customer(self, db: Session, customer_data: CustomerCreate) -> Customer:
        customer = Customer(name=customer_data.name)
        return self._repository.create(db, customer)
