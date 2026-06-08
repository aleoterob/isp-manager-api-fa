from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppException, ErrorCode
from app.core.security import hash_password
from app.features.users.models import Role, User
from app.features.users.repository import UserRepository
from app.features.users.schemas import UserCreate, UserUpdate


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = UserRepository(db)

    def create(self, dto: UserCreate) -> User:
        user = User(
            name=dto.name,
            email=dto.email,
            password=hash_password(dto.password),
            phone=dto.phone,
            role=dto.role,
            active=dto.active,
        )
        try:
            return self.repository.create(user)
        except IntegrityError as exc:
            raise AppException(ErrorCode.USR_EMAIL_TAKEN) from exc

    def find_all(
        self,
        skip: int = 0,
        take: int = 50,
        active_only: bool = False,
        role: Role | None = None,
    ) -> list[User]:
        return self.repository.list(skip, take, active_only, role)

    def find_one(self, user_id: str) -> User:
        user = self.repository.get(user_id)
        if not user:
            raise AppException(ErrorCode.USR_NOT_FOUND)
        return user

    def update(self, user_id: str, dto: UserUpdate) -> User:
        user = self.find_one(user_id)
        patch = dto.model_dump(exclude_unset=True)
        if "password" in patch and patch["password"] is not None:
            patch["password"] = hash_password(patch["password"])
        for key, value in patch.items():
            setattr(user, key, value)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise AppException(ErrorCode.USR_EMAIL_TAKEN) from exc
        self.db.refresh(user)
        return user

    def remove(self, user_id: str) -> User:
        user = self.find_one(user_id)
        user.active = False
        self.db.commit()
        self.db.refresh(user)
        return user

