import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class NotificationType(StrEnum):
    ORDER_ASSIGNED = "ORDER_ASSIGNED"
    ORDER_UPDATED = "ORDER_UPDATED"
    LOW_STOCK = "LOW_STOCK"
    GENERAL = "GENERAL"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    userId: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="NotificationType"),
        default=NotificationType.GENERAL,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    user = relationship("User", back_populates="notifications")

