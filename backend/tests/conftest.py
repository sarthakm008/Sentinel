"""Pytest configuration for Sentinel backend tests.

This module configures the test environment to use a file-based SQLite database
for test isolation. The database file is created and destroyed per test session.
"""

import os
import tempfile
import atexit

# Create a temporary database file for the test session
_test_db_fd, _test_db_path = tempfile.mkstemp(suffix='.db', prefix='sentinel_test_')
os.close(_test_db_fd)

# Set DATABASE_URL to the temporary file BEFORE any backend modules are imported
os.environ["DATABASE_URL"] = f"sqlite:///{_test_db_path}"

# Clean up the temp file on exit
def _cleanup_test_db():
    try:
        os.unlink(_test_db_path)
    except OSError:
        pass
atexit.register(_cleanup_test_db)

# Now import the rest
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.models.base import get_db, Base
from backend.app.models.risk_case import RefundEventQueue, RiskCase
from backend.app.models.webhook import ProcessedWebhookEvent


# Create engine for the test database file
_test_engine = create_engine(
    f"sqlite:///{_test_db_path}",
    connect_args={"check_same_thread": False},
)
_TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


def override_get_db():
    """Override the get_db dependency to use the test session."""
    db = _TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Apply the override before creating the TestClient
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables once per test session."""
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture(scope="function")
def client():
    """Create a test client with lifespan support for each test."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test.
    
    Clears all data before and after each test for isolation.
    """
    db = _TestSessionLocal()
    try:
        # Clear all tables before test
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
        yield db
    finally:
        # Clear all tables after test
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
        db.close()


@pytest.fixture(scope="session")
def test_secret():
    """Test webhook secret."""
    secret = "test_webhook_secret_12345678901234567890123456789012"
    os.environ["RAZORPAY_WEBHOOK_SECRET"] = secret
    return secret