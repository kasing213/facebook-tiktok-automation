# app/core/db.py
import os
from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from app.core.config import get_settings
from app.core.models import Tenant

_settings = get_settings()


def _get_psycopg3_url(url: str) -> str:
    """
    Convert postgresql:// to postgresql+psycopg:// for psycopg3 driver.
    Also adds prepare_threshold=0 to disable prepared statements for pgbouncer.
    """
    # First, fix the dialect
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)

    # Add prepare_threshold=0 to URL query string (psycopg3 reads this from URL)
    # This is CRITICAL for pgbouncer Transaction mode compatibility
    if "?" in url:
        if "prepare_threshold" not in url:
            url += "&prepare_threshold=0"
    else:
        url += "?prepare_threshold=0"

    return url


# PRODUCTION PostgreSQL engine configuration for pgbouncer TRANSACTION MODE
#
# KEY INSIGHT: With pgbouncer Transaction mode, let pgbouncer handle ALL pooling.
# Using NullPool means SQLAlchemy doesn't maintain its own connection pool.
# This ELIMINATES the "DuplicatePreparedStatement" errors because:
# - No SQLAlchemy-level connection reuse
# - No pool_pre_ping (which uses prepared statements)
# - Each request gets a fresh connection from pgbouncer
#
# pgbouncer Transaction mode handles:
# - Connection pooling (default_pool_size in pgbouncer config)
# - Connection reuse between transactions
# - Connection limits and queuing
#
# Architecture:
# - SQLAlchemy: NullPool (no application-level pooling)
# - pgbouncer: Handles all connection pooling
# - Supabase Transaction pooler: Port 6543
engine = create_engine(
    _get_psycopg3_url(_settings.DATABASE_URL),

    # CRITICAL: Use NullPool for pgbouncer Transaction mode
    # This prevents "DuplicatePreparedStatement" errors
    poolclass=NullPool,

    # Transaction mode isolation
    isolation_level="AUTOCOMMIT",

    connect_args={
        "connect_timeout": 15,
        "options": "-c timezone=utc -c default_transaction_isolation=read_committed",
        "application_name": f"fastapi_main_{os.getpid()}",
        "client_encoding": "utf8",
        "autocommit": True,
    },

    # Production settings
    future=True,
    echo=_settings.ENV == "dev",
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
)

# NOTE: Event listeners removed for pgbouncer Transaction mode compatibility
# Timezone is set via connect_args options: "-c timezone=utc"
# Per-connection settings don't work reliably with pgbouncer (connections are pooled/shared)

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

    Production-grade initialization with NullPool for pgbouncer Transaction mode.
    """
    import time
    import logging

    logger = logging.getLogger(__name__)

    # Log connection configuration for debugging
    db_host = _settings.DATABASE_URL.split('@')[1].split('/')[0] if '@' in _settings.DATABASE_URL else 'unknown'
    is_transaction_mode = ':6543' in _settings.DATABASE_URL
    mode = "Transaction" if is_transaction_mode else "Session"

    print(f"[INIT] PostgreSQL Connection - Mode: {mode}, Host: {db_host}")
    print(f"[INIT] Pool: NullPool (pgbouncer handles pooling)")
    print(f"[INIT] Process PID: {os.getpid()}, App Name: fastapi_main_{os.getpid()}")

    start_time = time.time()

    try:
        with engine.connect() as conn:
            # Log connection details
            connect_time = time.time() - start_time
            print(f"[CONN] Connected in {connect_time:.2f}s")

            # Get detailed database info
            result = conn.execute(text("SELECT version(), current_database(), current_user, inet_server_addr(), inet_server_port()"))
            row = result.fetchone()
            version, database, user, server_ip, server_port = row

            print(f"[OK] PostgreSQL {version.split()[1]} | DB: {database} | User: {user}")
            print(f"[OK] Server: {server_ip}:{server_port} | Mode: {mode}")

            # Validate core schema with timing
            schema_start = time.time()

            # Check if core tables exist
            result = conn.execute(text("""
                SELECT table_name, table_schema
                FROM information_schema.tables
                WHERE table_schema IN ('public', 'invoice', 'inventory', 'scriptclient', 'audit_sales', 'ads_alert')
                ORDER BY table_schema, table_name
            """))
            tables = result.fetchall()

            if not tables:
                print("[WARNING] No tables found. Run 'alembic upgrade head' to create schema.")
            else:
                # Group by schema
                schemas = {}
                for table_name, schema_name in tables:
                    if schema_name not in schemas:
                        schemas[schema_name] = []
                    schemas[schema_name].append(table_name)

                # Log schema status
                print(f"[SCHEMA] Found {len(tables)} tables across {len(schemas)} schemas:")
                for schema_name, table_list in schemas.items():
                    print(f"[SCHEMA]   {schema_name}: {len(table_list)} tables")

                # Check for critical tables
                has_tenant = any(t[0] == 'tenant' and t[1] == 'public' for t in tables)
                has_user = any(t[0] == 'user' and t[1] == 'public' for t in tables)

                if has_tenant and has_user:
                    print("[OK] Core authentication tables found")
                else:
                    print("[WARNING] Missing core tables (tenant/user). Check alembic migration status.")

            schema_time = time.time() - schema_start
            print(f"[OK] Schema validation completed in {schema_time:.2f}s")

            # Connection health test
            health_start = time.time()
            result = conn.execute(text("SELECT COUNT(*) FROM information_schema.schemata"))
            schema_count = result.fetchone()[0]
            health_time = time.time() - health_start
            print(f"[HEALTH] Query test passed in {health_time:.3f}s | Schemas: {schema_count}")

            total_time = time.time() - start_time
            print(f"[SUCCESS] Database initialization completed in {total_time:.2f}s")

    except Exception as e:
        error_type = type(e).__name__
        error_details = str(e)

        print(f"\n[FATAL] Database initialization failed")
        print(f"[FATAL] Error: {error_type} - {error_details}")
        print(f"[FATAL] Connection: {_settings.database_url_safe}")
        print(f"[FATAL] Mode: {mode} | PID: {os.getpid()}")
        print("\n[DEBUG] Troubleshooting steps:")
        print("  1. Check Supabase dashboard for connection limits")
        print("  2. Verify DATABASE_URL uses port 6543 (Transaction mode)")
        print("  3. Check Railway logs for connection errors")
        raise

def dispose_engine() -> None:
    """Clean shutdown of database connections"""
    print(f"[SHUTDOWN] Disposing database engine (PID: {os.getpid()})")
    engine.dispose()


def get_pool_status() -> dict:
    """
    Get current connection pool status for monitoring.

    With NullPool, there's no application-level pooling - pgbouncer handles it.
    """
    return {
        "pool_type": "NullPool",
        "note": "pgbouncer handles connection pooling",
        "status": "active",
    }


def log_connection_health() -> None:
    """
    Log connection health - simplified for NullPool.

    With NullPool, pgbouncer handles all pooling so we just verify connectivity.
    """
    import logging
    import time

    logger = logging.getLogger(__name__)

    try:
        start = time.time()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency = (time.time() - start) * 1000
        logger.info(f"DB Health: OK (latency={latency:.1f}ms, pool=NullPool/pgbouncer)")
    except Exception as e:
        logger.error(f"DB Health: FAILED - {e}")

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
