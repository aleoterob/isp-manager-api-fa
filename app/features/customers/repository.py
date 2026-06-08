from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.features.customers.models import Customer


class CustomerRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, customer_id: str) -> Customer | None:
        return self.db.get(Customer, customer_id)

    def list(self, skip: int, take: int) -> list[Customer]:
        stmt = (
            select(Customer)
            .order_by(Customer.name.asc())
            .offset(skip)
            .limit(min(take, 100))
        )
        return list(self.db.scalars(stmt))

    def search(self, q: str, take: int) -> list[Customer]:
        term = q.strip()
        if not term:
            return []
        stmt = (
            select(Customer)
            .where(func.lower(Customer.name).contains(term.lower()))
            .order_by(Customer.name.asc())
            .limit(min(take, 20))
        )
        return list(self.db.scalars(stmt))
