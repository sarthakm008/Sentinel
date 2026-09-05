"""Pytest configuration for Sentinel backend tests.

This module configures the test environment to use an in-memory SQLite database
instead of the production PostgreSQL database.
"""

import os

# Set DATABASE_URL to in-memory SQLite BEFORE any backend modules are imported
# This must happen before any backend modules are imported
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Now import the rest
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.base import get_db, SessionLocal, engine, Base
from backend.app.models.risk_case import RefundEventQueue, RiskCase
from backend.app.models.webhook import ProcessedWebhookEvent


@pytest.fixture(scope="function")
def client():
    """Create a test client with lifespan support for each test."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test using in-memory SQLite."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def test_secret():
    """Test webhook secret."""
    secret = "test_webhook_secret_12345678901234567890123456789012"
    os.environ["RAZORPAY_WEBHOOK_SECRET"] = secret
    return secret