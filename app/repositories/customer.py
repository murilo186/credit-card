from sqlalchemy.orm import Session

from app.models.customer import Customer


class CustomerRepository:
    """Persist customer entities without business rules."""

    def create(self, db: Session, customer: Customer) -> Customer:
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer
