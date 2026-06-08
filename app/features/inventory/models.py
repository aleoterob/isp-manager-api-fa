import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MovementType(StrEnum):
    IN = "IN"
    OUT = "OUT"
    ADJUST = "ADJUST"


class EquipmentCategory(Base):
    __tablename__ = "equipment_categories"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    equipment = relationship("Equipment", back_populates="category")


class Unit(Base):
    __tablename__ = "units"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    abbreviation: Mapped[str | None] = mapped_column(String, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    equipment = relationship("Equipment", back_populates="unit")


class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    categoryId: Mapped[str] = mapped_column(
        String, ForeignKey("equipment_categories.id"), nullable=False
    )
    unitId: Mapped[str] = mapped_column(String, ForeignKey("units.id"), nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    category = relationship("EquipmentCategory", back_populates="equipment")
    unit = relationship("Unit", back_populates="equipment")
    stock = relationship("WarehouseStock", back_populates="equipment")
    orders = relationship("OrderEquipment", back_populates="equipment")
    movements = relationship("StockMovement", back_populates="equipment")


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    province: Mapped[str | None] = mapped_column(String, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    stock = relationship("WarehouseStock", back_populates="warehouse")
    movements = relationship("StockMovement", back_populates="warehouse")
    orderEquipment = relationship("OrderEquipment", back_populates="warehouse")


class WarehouseStock(Base):
    __tablename__ = "warehouse_stock"

    warehouseId: Mapped[str] = mapped_column(
        String, ForeignKey("warehouses.id"), primary_key=True
    )
    equipmentId: Mapped[str] = mapped_column(
        String, ForeignKey("equipment.id"), primary_key=True
    )
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    minStock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    warehouse = relationship("Warehouse", back_populates="stock")
    equipment = relationship("Equipment", back_populates="stock")


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    equipmentId: Mapped[str] = mapped_column(
        String, ForeignKey("equipment.id"), nullable=False
    )
    warehouseId: Mapped[str] = mapped_column(
        String, ForeignKey("warehouses.id"), nullable=False
    )
    userId: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    type: Mapped[MovementType] = mapped_column(
        Enum(MovementType, name="MovementType"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    equipment = relationship("Equipment", back_populates="movements")
    warehouse = relationship("Warehouse", back_populates="movements")
    user = relationship("User", back_populates="stockMovements")

