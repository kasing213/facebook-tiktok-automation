# app/core/db.py
from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from app.core.config import get_settings
from app.core.models import Tenant

_settings = get_settings()

# Enhanced PostgreSQL engine configuration for multi-tenant application
# NOTE: Pool sizes are kept small because:
# 1. Supabase pooler (Session mode) has connection limits (~25 for free tier)
# 2. Both main backend AND api-gateway share the same database
# 3. Railway instances can scale, each creating new pools
# For Supabase, consider using Transaction mode (port 6543) for better connection reuse
engine = create_engine(
    _settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=1,              # MINIMAL - Supabase pooler has strict limits
    max_overflow=2,           # Total max: 3 connections per instance
    pool_pre_ping=True,       # validate connections before use
    pool_recycle=300,         # recycle connections every 5 min (aggressive)
    pool_timeout=10,          # fail fast if pool exhausted (was 30)
    connect_args={
        "connect_timeout": 10,  # connection timeout in seconds
        "options": "-c timezone=utc",  # set timezone to UTC
    },
    future=True,
    echo=False,  # Disable SQL logging in production (set to True for debugging)
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
)

# Add connection event listeners for better observability
@event.listens_for(engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    """Set connection-level configuration when connection is created"""
    with dbapi_connection.cursor() as cursor:
        # Set timezone to UTC for consistency
        cursor.execute("SET timezone TO 'UTC'")
        # Enable query logging for slow queries in production
        if _settings.ENV == "prod":
            cursor.execute("SET log_min_duration_statement = 1000")

def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI endpoints.

    Provides proper session management with automatic cleanup.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions in non-FastAPI contexts.

    Usage:
        with get_db_session() as db:
            # perform database operations
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_db_sync() -> Generator[Session, None, None]:
    """
    Synchronous database session generator for non-async contexts.

    Usage:
        db = next(get_db_sync())
        try:
            # perform database operations
        finally:
            db.close()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_tenant_by_id(db: Session, tenant_id: str) -> Optional[Tenant]:
    """Get a tenant by ID with proper validation"""
    return db.query(Tenant).filter(
        Tenant.id == tenant_id,
        Tenant.is_active == True
    ).first()

def get_tenant_by_slug(db: Session, slug: str) -> Optional[Tenant]:
    """Get a tenant by slug with proper validation"""
    return db.query(Tenant).filter(
        Tenant.slug == slug,
        Tenant.is_active == True
    ).first()

def init_db() -> None:
    """
    Initialize database connection and validate schema.

    This should be called on application startup to ensure
    database connectivity and run any necessary checks.
    """
    try:
        with engine.connect() as conn:
            # Test basic connectivity
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"[OK] Connected to PostgreSQL: {version}")

            # Check if core tables exist
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'tenant'
            """))

            if not result.fetchone():
                print("[WARNING] Core tables not found. Run 'alembic upgrade head' to create schema.")
            else:
                # Check table count for basic validation
                result = conn.execute(text("""
                    SELECT COUNT(*) as table_count
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                """))
                table_count = result.fetchone()[0]
                print(f"[OK] Database schema validated. Found {table_count} tables.")

    except Exception as e:
        # Avoid Unicode emojis on Windows console
        print(f"[ERROR] Database initialization failed: {e}")
        print(f"   Connection string: {_settings.database_url_safe}")
        print("   Please ensure:")
        print("   1. PostgreSQL is running")
        print("   2. Database exists and is accessible")
        print("   3. Database user exists with correct password")
        print("   4. User has permission to access the database")
        print("   5. pg_hba.conf allows password authentication for the database user")
        raise

def dispose_engine() -> None:
    """Clean shutdown of database connections"""
    engine.dispose()

# Tenant-aware query helpers
class TenantQueryMixin:
    """
    Mixin class to add tenant-aware querying capabilities.

    This ensures all queries are automatically scoped to a specific tenant
    for proper data isolation in multi-tenant scenarios.
    """

    @staticmethod
    def for_tenant(query, tenant_id: str):
        """Filter query results for a specific tenant"""
        return query.filter_by(tenant_id=tenant_id)

    @staticmethod
    def active_only(query):
        """Filter to only active records"""
        return query.filter_by(is_active=True)
