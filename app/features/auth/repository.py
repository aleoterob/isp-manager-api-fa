from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.features.auth.models import RefreshSession, RefreshSessionStatus


class AuthRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_session_by_hash(self, token_hash: str) -> RefreshSession | None:
        return self.db.scalar(
            select(RefreshSession).where(RefreshSession.tokenHash == token_hash)
        )

    def add_session(self, session: RefreshSession) -> RefreshSession:
        self.db.add(session)
        self.db.flush()
        return session

    def revoke_family(self, family_id: str) -> None:
        self.db.execute(
            update(RefreshSession)
            .where(
                RefreshSession.familyId == family_id,
                RefreshSession.status.in_(
                    [RefreshSessionStatus.ACTIVE, RefreshSessionStatus.REPLACED]
                ),
            )
            .values(status=RefreshSessionStatus.REVOKED)
        )

