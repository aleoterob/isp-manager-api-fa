import uuid
from datetime import UTC, datetime, timedelta

from fastapi import Request, Response
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppException, ErrorCode
from app.core.security import (
    create_access_token,
    generate_csrf_token,
    generate_refresh_token,
    hash_refresh_token,
    verify_password,
)
from app.features.auth.models import RefreshSession, RefreshSessionStatus
from app.features.auth.repository import AuthRepository
from app.features.auth.schemas import SignupRequest
from app.features.users.models import Role, User
from app.features.users.repository import UserRepository
from app.features.users.schemas import UserCreate
from app.features.users.service import UserService


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class AuthService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.auth_repository = AuthRepository(db)
        self.user_repository = UserRepository(db)
        self.user_service = UserService(db)

    def _cookie_options(self, *, http_only: bool = True) -> dict:
        options = {
            "httponly": http_only,
            "secure": self.settings.cookie_secure,
            "samesite": self.settings.cookie_samesite,
            "path": "/",
        }
        if self.settings.cookie_domain:
            options["domain"] = self.settings.cookie_domain
        if self.settings.cookie_samesite == "none":
            options["partitioned"] = True
        return options

    def _attach_auth_cookies(
        self, response: Response, access_token: str, refresh_token: str
    ) -> None:
        response.set_cookie(
            self.settings.access_cookie_name,
            access_token,
            max_age=self.settings.cookie_max_age,
            **self._cookie_options(),
        )
        response.set_cookie(
            self.settings.refresh_cookie_name,
            refresh_token,
            max_age=self.settings.refresh_cookie_max_age,
            **self._cookie_options(),
        )

    def clear_auth_cookies(self, response: Response) -> None:
        response.delete_cookie(self.settings.access_cookie_name, path="/")
        response.delete_cookie(self.settings.refresh_cookie_name, path="/")
        response.delete_cookie(self.settings.csrf_cookie_name, path="/")

    def issue_csrf_cookie(self, response: Response) -> dict[str, str]:
        token = generate_csrf_token()
        response.set_cookie(
            self.settings.csrf_cookie_name,
            token,
            max_age=self.settings.refresh_cookie_max_age,
            **self._cookie_options(http_only=False),
        )
        return {"token": token}

    def _create_session(self, user: User, response: Response) -> User:
        user.lastLoginAt = utc_now()
        family_id = str(uuid.uuid4())
        refresh_plain = generate_refresh_token()
        session = RefreshSession(
            userId=user.id,
            tokenHash=hash_refresh_token(refresh_plain),
            familyId=family_id,
            status=RefreshSessionStatus.ACTIVE,
            expiresAt=utc_now()
            + timedelta(milliseconds=self.settings.refresh_cookie_max_age),
        )
        self.auth_repository.add_session(session)
        self.db.commit()
        self.db.refresh(user)
        access_token = create_access_token(user, self.settings)
        self._attach_auth_cookies(response, access_token, refresh_plain)
        return user

    def signup(self, dto: SignupRequest, response: Response) -> User:
        user = self.user_service.create(
            UserCreate(
                name=dto.name,
                email=dto.email,
                password=dto.password,
                phone=dto.phone,
                role=Role.INSTALLER,
                active=True,
            )
        )
        return self._create_session(user, response)

    def login(self, email: str, password: str, response: Response) -> User:
        user = self.user_repository.get_by_email(email)
        if not user or not user.active or not verify_password(password, user.password):
            raise AppException(ErrorCode.AUTH_INVALID_CREDENTIALS)
        return self._create_session(user, response)

    def refresh(self, request: Request, response: Response) -> User:
        raw = request.cookies.get(self.settings.refresh_cookie_name)
        if not raw:
            raise AppException(ErrorCode.AUTH_REFRESH_INVALID)

        session = self.auth_repository.get_session_by_hash(hash_refresh_token(raw))
        if not session:
            raise AppException(ErrorCode.AUTH_REFRESH_INVALID)

        if session.status == RefreshSessionStatus.REPLACED:
            self.auth_repository.revoke_family(session.familyId)
            self.db.commit()
            raise AppException(ErrorCode.AUTH_REFRESH_REUSE)

        if (
            session.status != RefreshSessionStatus.ACTIVE
            or session.expiresAt < utc_now()
        ):
            raise AppException(ErrorCode.AUTH_REFRESH_INVALID)

        user = self.user_repository.get(session.userId)
        if not user or not user.active:
            raise AppException(ErrorCode.AUTH_REFRESH_INVALID)

        session.status = RefreshSessionStatus.REPLACED
        refresh_plain = generate_refresh_token()
        self.auth_repository.add_session(
            RefreshSession(
                userId=user.id,
                tokenHash=hash_refresh_token(refresh_plain),
                familyId=session.familyId,
                status=RefreshSessionStatus.ACTIVE,
                expiresAt=utc_now()
                + timedelta(milliseconds=self.settings.refresh_cookie_max_age),
            )
        )
        self.db.commit()
        self.db.refresh(user)
        self._attach_auth_cookies(
            response, create_access_token(user, self.settings), refresh_plain
        )
        return user

    def logout(self, request: Request, response: Response) -> None:
        raw = request.cookies.get(self.settings.refresh_cookie_name)
        self.clear_auth_cookies(response)
        if raw:
            session = self.auth_repository.get_session_by_hash(hash_refresh_token(raw))
            if session:
                self.auth_repository.revoke_family(session.familyId)
                self.db.commit()

    def me(self, user_id: str) -> User:
        user = self.user_repository.get(user_id)
        if not user or not user.active:
            raise AppException(ErrorCode.AUTH_UNAUTHENTICATED)
        return user
