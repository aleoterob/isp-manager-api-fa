import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OrderType(StrEnum):
    INSTALLATION = "INSTALLATION"
    RELOCATION = "RELOCATION"
    REPAIR = "REPAIR"
    UNINSTALL = "UNINSTALL"
    UPGRADE = "UPGRADE"


class OrderStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    type: Mapped[OrderType] = mapped_column(
        Enum(OrderType, name="OrderType"), nullable=False
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="OrderStatus"),
        default=OrderStatus.PENDING,
        nullable=False,
    )
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    province: Mapped[str | None] = mapped_column(String, nullable=True)
    zipCode: Mapped[str | None] = mapped_column(String, nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    scheduledAt: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    installerId: Mapped[str | None] = mapped_column(
        String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    customerId: Mapped[str | None] = mapped_column(
        String, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    installer = relationship("User", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")
    equipment = relationship("OrderEquipment", back_populates="order")
    notes = relationship("OrderNote", back_populates="order")


class OrderEquipment(Base):
    __tablename__ = "order_equipment"

    orderId: Mapped[str] = mapped_column(
        String, ForeignKey("orders.id"), primary_key=True
    )
    equipmentId: Mapped[str] = mapped_column(
        String, ForeignKey("equipment.id"), primary_key=True
    )
    warehouseId: Mapped[str] = mapped_column(
        String, ForeignKey("warehouses.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    order = relationship("Order", back_populates="equipment")
    equipment = relationship("Equipment", back_populates="orders")
    warehouse = relationship("Warehouse", back_populates="orderEquipment")


class OrderNote(Base):
    __tablename__ = "order_notes"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    orderId: Mapped[str] = mapped_column(
        String, ForeignKey("orders.id"), nullable=False
    )
    userId: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    order = relationship("Order", back_populates="notes")
    user = relationship("User", back_populates="notes")
