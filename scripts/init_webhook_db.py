#!/usr/bin/env python
"""
Database initialization script for webhook tables.

This script creates the new webhook tables in the existing database.
Run this after deploying the webhook integration.
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.app.models.base import engine
from backend.app.models.risk_case import Base as RiskCaseBase
from backend.app.models.webhook import Base as WebhookBase

def init_webhook_tables():
    """Create webhook tables in the database."""
    print("Creating webhook tables...")
    WebhookBase.metadata.create_all(bind=engine)
    print("Webhook tables created successfully.")

    # Verify tables exist
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    webhook_tables = [t for t in tables if 'webhook' in t.lower()]
    print(f"Webhook-related tables: {webhook_tables}")

if __name__ == "__main__":
    init_webhook_tables()