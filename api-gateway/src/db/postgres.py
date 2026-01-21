# api-gateway/src/db/postgres.py
"""PostgreSQL database connection for API Gateway."""

import logging
import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from src.config import settings

logger = logging.getLogger(__name__)

# Create engine
engine = None
SessionLocal = None


def _get_psycopg3_url(url: str) -> str:
    """
    Convert postgresql:// to postgresql+psycopg:// for psycopg3 driver.

    NOTE: prepare_threshold is passed via connect_args, not URL.
    URL params are read as strings, causing TypeError with psycopg3.
    """
    # Fix the dialect for psycopg3
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)

    return url


def init_postgres():
    """Initialize PostgreSQL connection with NullPool for pgbouncer Transaction mode."""
    global engine, SessionLocal

    if not settings.DATABASE_URL:
        logger.warning("DATABASE_URL not set - PostgreSQL disabled")
        return

    # PRODUCTION configuration for pgbouncer TRANSACTION MODE
    #
    # KEY INSIGHT: With pgbouncer Transaction mode, let pgbouncer handle ALL pooling.
    # Using NullPool means SQLAlchemy doesn't maintain its own connection pool.
    # This ELIMINATES the "DuplicatePreparedStatement" errors because:
    # - No SQLAlchemy-level connection reuse
    # - No pool_pre_ping (which uses prepared statements)
    # - Each request gets a fresh connection from pgbouncer
    engine = create_engine(
        _get_psycopg3_url(settings.DATABASE_URL),

        # CRITICAL: Use NullPool for pgbouncer Transaction mode
        # This prevents "DuplicatePreparedStatement" errors
        poolclass=NullPool,

        # Transaction mode isolation
        isolation_level="AUTOCOMMIT",

        connect_args={
            "connect_timeout": 15,
            "options": "-c timezone=utc -c default_transaction_isolation=read_committed",
            "application_name": f"api_gateway_{os.getpid()}",
            "client_encoding": "utf8",
            "autocommit": True,
            # CRITICAL: Disable prepared statements for pgbouncer Transaction mode
            # Must be int (not string) - URL params cause TypeError
            "prepare_threshold": 0,
        },
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info(f"PostgreSQL initialized with NullPool (PID: {os.getpid()})")


def close_postgres():
    """Close PostgreSQL connection."""
    global engine
    if engine:
        engine.dispose()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Get a database session context manager.

    Usage:
        with get_db_session() as db:
            db.query(...)
    """
    if SessionLocal is None:
        init_postgres()

    if SessionLocal is None:
        raise RuntimeError("Database not configured - DATABASE_URL not set")

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.

    Usage:
        @app.get("/")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    if SessionLocal is None:
        init_postgres()

    if SessionLocal is None:
        raise RuntimeError("Database not configured - DATABASE_URL not set")

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
