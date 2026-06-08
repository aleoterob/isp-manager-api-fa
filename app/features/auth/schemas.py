from pydantic import BaseModel, Field, field_validator


def _validate_email(value: str) -> str:
    if "@" not in value:
        raise ValueError("email must be an email")
    return value


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1)

    @field_validator("email")
    @classmethod
    def email_is_valid(cls, value: str) -> str:
        return _validate_email(value)


class SignupRequest(BaseModel):
    name: str = Field(min_length=1)
    email: str
    password: str = Field(min_length=8)
    phone: str | None = None

    @field_validator("email")
    @classmethod
    def email_is_valid(cls, value: str) -> str:
        return _validate_email(value)


class CsrfResponse(BaseModel):
    token: str


class LogoutResponse(BaseModel):
    ok: bool

