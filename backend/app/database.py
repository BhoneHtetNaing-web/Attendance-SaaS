
"""Database configuration for ApexiveAI Workforce Payroll SaaS.

Uses synchronous SQLAlchemy with PostgreSQL.
Alembic owns schema changes; this module never creates tables automatically.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


# Project root: backend/
BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BACKEND_DIR / ".env"


def _load_environment() -> None:
    """Load backend/.env without overwriting existing environment variables."""
    try:
        from dotenv import load_dotenv

        load_dotenv(dotenv_path=ENV_FILE, override=False)
        return
    except ImportError:
        # Fallback for environments without python-dotenv installed.
        pass

    if not ENV_FILE.is_file():
        return

    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            continue

        if len(value) >= 2 and value[0] == value[-1]:
            if value[0] in {"'", '"'}:
                value = value[1:-1]

        os.environ.setdefault(key, value)


_load_environment()


def _resolve_database_url() -> str:
    """Get and normalize a synchronous SQLAlchemy database URL."""
    value = os.getenv("DATABASE_URL", "").strip()

    if not value:
        raise RuntimeError(
            "DATABASE_URL is missing. Configure it in backend/.env "
            "or in the process environment."
        )

    # Railway and other providers may supply one of these URL schemes.
    if value.startswith("postgres://"):
        value = "postgresql+psycopg://" + value[len("postgres://") :]
    elif value.startswith("postgresql://"):
        value = "postgresql+psycopg://" + value[len("postgresql://") :]

    if value.startswith("postgresql+asyncpg://"):
        raise RuntimeError(
            "This project uses synchronous SQLAlchemy. "
            "Use a synchronous PostgreSQL URL such as "
            "postgresql+psycopg://..."
        )

    return value


class Base(DeclarativeBase):
    """Shared SQLAlchemy base used by all ORM models."""

    pass


def _create_engine() -> Engine:
    database_url = _resolve_database_url()

    common_options = {
        "pool_pre_ping": True,
    }

    if database_url.startswith(("postgresql://", "postgresql+")):
        return create_engine(
            database_url,
            **common_options,
            pool_recycle=1800,
            pool_size=5,
            max_overflow=5,
            connect_args={"connect_timeout": 10},
        )

    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            **common_options,
            connect_args={"check_same_thread": False},
        )

    return create_engine(database_url, **common_options)


# Shared engine and session factory.
# Existing model imports should continue using: from app.database import Base
engine: Engine = _create_engine()

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_engine() -> Engine:
    """Return the shared database engine."""
    return engine


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides one database session per request."""
    db = SessionLocal()

    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


__all__ = [
    "Base",
    "SessionLocal",
    "engine",
    "get_db",
    "get_engine",
]
