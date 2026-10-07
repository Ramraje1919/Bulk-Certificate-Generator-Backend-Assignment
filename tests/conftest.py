from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.database.session import Base, get_db
import app.services.job_service as job_service_module
from app.main import app

# Create in-memory SQLite engine for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(tmp_path_factory):
    # Override storage directory to temporary path
    test_storage = tmp_path_factory.mktemp("test_generated")
    settings.STORAGE_DIR = test_storage
    # Monkeypatch job_service SessionLocal for background tasks in tests
    job_service_module.SessionLocal = TestingSessionLocal
    yield
    settings.STORAGE_DIR = Path("generated")


@pytest.fixture(scope="function")
def db_session() -> Generator:
    """
    Creates fresh database tables for each test and drops them after.
    """
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    """
    FastAPI TestClient with overridden get_db dependency.
    """
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
def sample_job_payload():
    return {
        "job_name": "Full Stack Cloud Architecture Cohort",
        "event_name": "Distributed Systems & Cloud Engineering",
        "issued_by": "DeepMind Academy",
        "issue_date": "2026-10-07",
        "recipients": [
            {
                "recipient_name": "Ada Lovelace",
                "recipient_email": "ada@example.com"
            },
            {
                "recipient_name": "Alan Turing",
                "recipient_email": "alan@example.com"
            },
            {
                "recipient_name": "Grace Hopper",
                "recipient_email": "grace@example.com"
            }
        ]
    }
