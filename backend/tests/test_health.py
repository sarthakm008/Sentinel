"""Tests for the health endpoint."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_returns_200():
    """GET /api/health returns 200 with status ok."""
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_body():
    """GET /api/health returns expected JSON body."""
    response = client.get("/api/health")
    data = response.json()
    assert data == {"status": "ok"}
