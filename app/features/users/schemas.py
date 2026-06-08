from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.features.users.models import Role


def _validate_email(value: str) -> str:
    if "@" not in value:
        raise ValueError("email must be an email")
    return value


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    phone: str | None = None
    role: Role
    active: bool
    lastLoginAt: datetime | None = None
    createdAt: datetime
    updatedAt: datetime


class UserCreate(BaseModel):
    name: str = Field(min_length=1)
    email: str
    password: str = Field(min_length=8)
    phone: str | None = None
    role: Role = Role.INSTALLER
    active: bool = True

    @field_validator("email")
    @classmethod
    def email_is_valid(cls, value: str) -> str:
        return _validate_email(value)


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    password: str | None = Field(default=None, min_length=8)
    phone: str | None = None
    role: Role | None = None
    active: bool | None = None

    @field_validator("email")
    @classmethod
    def email_is_valid(cls, value: str | None) -> str | None:
        return _validate_email(value) if value is not None else value

