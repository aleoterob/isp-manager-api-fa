from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.core.datetime import to_utc_iso_z
from app.features.orders.models import OrderStatus, OrderType


class OrderInstallerRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str


class OrderCustomerRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str | None = None
    type: OrderType
    status: OrderStatus
    address: str | None = None
    city: str | None = None
    province: str | None = None
    zipCode: str | None = None
    lat: float | None = None
    lng: float | None = None
    scheduledAt: datetime | None = None
    installerId: str | None = None
    customerId: str | None = None
    installer: OrderInstallerRef | None = None
    customer: OrderCustomerRef | None = None
    createdAt: datetime
    updatedAt: datetime

    @field_serializer("scheduledAt", "createdAt", "updatedAt")
    def serialize_datetime_as_utc_z(self, value: datetime | None) -> str | None:
        return to_utc_iso_z(value)


class OrderCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=10_000)
    type: OrderType
    customerId: str
    installerId: str | None = None
    scheduledAt: datetime | None = None


class OrderUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=10_000)
    type: OrderType | None = None
    status: OrderStatus | None = None
    customerId: str | None = None
    installerId: str | None = None
    scheduledAt: datetime | None = None


class DeletedOrderId(BaseModel):
    id: str
