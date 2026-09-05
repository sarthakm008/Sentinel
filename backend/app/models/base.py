"""SQLAlchemy database setup.

Supports both SQLite for development and PostgreSQL for production.
Configure via DATABASE_URL environment variable.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file at project root BEFORE reading DATABASE_URL
# This must happen at import time, before any other modules read env vars
# Using parents[3] because this file is at Sentinel/backend/app/models/base.py
# Only load .env if DATABASE_URL is not already set (preserves test/production env var precedence)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if "DATABASE_URL" not in os.environ:
    load_dotenv(PROJECT_ROOT / ".env")

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sentinel.db")

# SQLite needs check_same_thread=False for FastAPI async usage
# PostgreSQL doesn't need this
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

# For PostgreSQL, disable prepared statements to avoid
# "cached plan must not change result type" errors with psycopg v3
if DATABASE_URL.startswith("postgresql"):
    # Disable prepared statements for psycopg v3 to avoid
    # "cached plan must not change result type" errors
    connect_args["prepare_threshold"] = 0
    # Also pass via URL query string as fallback for psycopg v3
    if "prepare_threshold" not in DATABASE_URL:
        separator = "&" if "?" in DATABASE_URL else "?"
        DATABASE_URL = f"{DATABASE_URL}{separator}prepare_threshold=0"

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=True,  # Verify connections before use
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


def get_db():
    """Dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
