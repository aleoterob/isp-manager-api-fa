import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RefreshSessionStatus(StrEnum):
    ACTIVE = "ACTIVE"
    REPLACED = "REPLACED"
    REVOKED = "REVOKED"


class RefreshSession(Base):
    __tablename__ = "refresh_sessions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    userId: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    tokenHash: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    familyId: Mapped[str] = mapped_column(String, nullable=False, index=True)
    status: Mapped[RefreshSessionStatus] = mapped_column(
        Enum(RefreshSessionStatus, name="RefreshSessionStatus"),
        default=RefreshSessionStatus.ACTIVE,
        nullable=False,
    )
    expiresAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    user = relationship("User", back_populates="refreshSessions")

    __table_args__ = (
        Index("refresh_sessions_userId_familyId_idx", "userId", "familyId"),
    )
