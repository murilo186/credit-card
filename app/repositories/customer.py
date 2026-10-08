import uuid

from sqlalchemy.orm import Session

from app.models.customer import Customer


class CustomerRepository:
    """Persist customer entities without business rules."""

    def get_by_id(self, db: Session, customer_id: uuid.UUID) -> Customer | None:
        return db.get(Customer, customer_id)

    def create(self, db: Session, customer: Customer) -> Customer:
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer
