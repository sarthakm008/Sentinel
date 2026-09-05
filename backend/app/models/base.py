"""SQLAlchemy database setup.

Supports both SQLite for development and PostgreSQL for production.
Configure via DATABASE_URL environment variable.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sentinel.db")

# SQLite needs check_same_thread=False for FastAPI async usage
# PostgreSQL doesn't need this
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

# For PostgreSQL, we can add pool settings
if DATABASE_URL.startswith("postgresql"):
    # Pool settings for PostgreSQL
    connect_args = {}
    # Pool settings can be passed to create_engine directly

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
