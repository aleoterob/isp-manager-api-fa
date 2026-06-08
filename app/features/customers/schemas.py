from pydantic import BaseModel, ConfigDict, Field


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    province: str | None = None
    zipCode: str | None = None
    lat: float | None = None
    lng: float | None = None


class CustomerSearchQuery(BaseModel):
    q: str = ""
    take: int = Field(default=10)

