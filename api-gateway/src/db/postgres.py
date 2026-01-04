# api-gateway/src/db/postgres.py
"""PostgreSQL database connection for API Gateway."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import settings

# Create engine
engine = None
SessionLocal = None


def init_postgres():
    """Initialize PostgreSQL connection."""
    global engine, SessionLocal

    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
