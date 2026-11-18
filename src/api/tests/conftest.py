"""Pytest fixtures and configuration for Pizzaria API tests.

Provides isolated SQLite in-memory database with StaticPool and pre-configured JWT headers.
"""

from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.database import Base, get_db, seed_db
from src.api.main import app
from src.api.security import create_access_token

# SQLite in-memory engine with StaticPool to ensure all connections share the same memory instance
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a fresh database schema for each test function and seed initial data."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    seed_db(db=session)

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """TestClient fixture overriding get_db to point to the isolated test database."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def admin_headers() -> dict:
    """Authorization headers for an ADMIN user."""
    token = create_access_token({
        "sub": "1",
        "email": "admin@pizzaria.com",
        "role": "ADMIN",
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def funcionario_headers() -> dict:
    """Authorization headers for a FUNCIONARIO user."""
    token = create_access_token({
        "sub": "2",
        "email": "func@pizzaria.com",
        "role": "FUNCIONARIO",
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def cliente_headers() -> dict:
    """Authorization headers for a CLIENTE user."""
    token = create_access_token({
        "sub": "3",
        "email": "cliente@pizzaria.com",
        "role": "CLIENTE",
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def invalid_token_headers() -> dict:
    """Authorization headers with a corrupted/malformed token."""
    return {"Authorization": "Bearer malformed.jwt.token"}
