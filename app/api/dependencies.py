from typing import Annotated

import jwt
from fastapi import Depends, Request
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import AppException, ErrorCode
from app.db.session import get_db
from app.features.users.models import Role, User


class CurrentUser:
    def __init__(self, user_id: str, email: str, role: Role) -> None:
        self.user_id = user_id
        self.email = email
        self.role = role


def _bearer_token(request: Request) -> str | None:
    value = request.headers.get("authorization")
    if not value:
        return None
    scheme, _, token = value.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def get_current_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CurrentUser:
    token = request.cookies.get(settings.access_cookie_name) or _bearer_token(request)
    if not token:
        raise AppException(ErrorCode.AUTH_UNAUTHENTICATED)

    try:
        payload = jwt.decode(
            token,
            settings.jwt_access_secret,
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
        )
    except InvalidTokenError as exc:
        raise AppException(ErrorCode.AUTH_UNAUTHENTICATED) from exc

    user = db.get(User, payload.get("sub"))
    if not user or not user.active:
        raise AppException(ErrorCode.AUTH_UNAUTHENTICATED)

    return CurrentUser(user_id=user.id, email=user.email, role=user.role)


def require_roles(*roles: Role):
    def dependency(
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        if current_user.role not in roles:
            raise AppException(ErrorCode.AUTH_FORBIDDEN)
        return current_user

    return dependency


def require_csrf(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    cookie = request.cookies.get(settings.csrf_cookie_name)
    header = request.headers.get(settings.csrf_header_name)
    if not cookie or not header or cookie != header:
        raise AppException(ErrorCode.CSRF_INVALID)
