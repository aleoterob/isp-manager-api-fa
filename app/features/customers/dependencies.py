from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.features.customers.service import CustomerService


def get_customer_service(db: Annotated[Session, Depends(get_db)]) -> CustomerService:
    return CustomerService(db)

