from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.features.orders.service import OrderService


def get_order_service(db: Annotated[Session, Depends(get_db)]) -> OrderService:
    return OrderService(db)

