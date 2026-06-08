from sqlalchemy.orm import Session

from app.features.customers.models import Customer
from app.features.customers.repository import CustomerRepository


class CustomerService:
    def __init__(self, db: Session) -> None:
        self.repository = CustomerRepository(db)

    def find_all(self, skip: int = 0, take: int = 50) -> list[Customer]:
        return self.repository.list(skip, take)

    def search(self, q: str, take: int = 10) -> list[Customer]:
        return self.repository.search(q, take)

