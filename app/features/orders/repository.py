from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.features.orders.models import Order, OrderEquipment, OrderNote


class OrderRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, order_id: str) -> Order | None:
        return self.db.scalar(
            select(Order)
            .options(joinedload(Order.installer), joinedload(Order.customer))
            .where(Order.id == order_id)
        )

    def list(self, skip: int, take: int) -> list[Order]:
        stmt = (
            select(Order)
            .options(joinedload(Order.installer), joinedload(Order.customer))
            .order_by(Order.createdAt.desc(), Order.id.desc())
            .offset(skip)
            .limit(min(take, 100))
        )
        return list(self.db.scalars(stmt))

    def delete_related(self, order_id: str) -> None:
        self.db.execute(delete(OrderNote).where(OrderNote.orderId == order_id))
        self.db.execute(
            delete(OrderEquipment).where(OrderEquipment.orderId == order_id)
        )
