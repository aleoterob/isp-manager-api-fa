from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.db.models  # noqa: F401
from app.core.config import Settings, get_settings
from app.core.rate_limit import RateLimitMiddleware
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app


class TestSettings(Settings):
    def __init__(self) -> None:
        super().__init__()
        self.database_url = "sqlite://"
        self.jwt_access_secret = "test-secret-with-at-least-32-characters"
        self.swagger_enabled = True
        self.cookie_secure = False


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    RateLimitMiddleware._hits.clear()
    settings = TestSettings()
    app = create_app(settings)

    def override_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as test_client:
        yield test_client
