from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.features.users.models import Role, User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user: User) -> User:
        self.db.add(user)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise
        self.db.refresh(user)
        return user

    def get(self, user_id: str) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def list(
        self, skip: int, take: int, active_only: bool, role: Role | None
    ) -> list[User]:
        stmt = select(User)
        if active_only:
            stmt = stmt.where(User.active.is_(True))
        if role is not None:
            stmt = stmt.where(User.role == role)
        stmt = stmt.order_by(User.createdAt.desc()).offset(skip).limit(min(take, 100))
        return list(self.db.scalars(stmt))

