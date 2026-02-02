# app/core/db.py
import os
import time
import logging
from contextlib import contextmanager
from typing import Generator, Optional, Callable, TypeVar, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import OperationalError, DisconnectionError
import psycopg.errors
from app.core.config import get_settings
from app.core.models import Tenant

T = TypeVar('T')

_settings = get_settings()


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
        "connect_timeout": 30,  # Increased from 15 to handle load spikes
        "options": "-c timezone=utc -c default_transaction_isolation=read_committed",
        "application_name": f"fastapi_main_{os.getpid()}",
        "client_encoding": "utf8",
        "autocommit": True,
        # CRITICAL: Disable prepared statements for pgbouncer Transaction mode
        # prepare_threshold=None DISABLES prepared statements entirely
        # prepare_threshold=0 means "prepare immediately" (WRONG - still creates prepared statements!)
        "prepare_threshold": None,
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


def is_connection_error(error: Exception) -> bool:
    """Check if an exception represents a connection-related error"""
    # SQLAlchemy connection errors
    if isinstance(error, (OperationalError, DisconnectionError)):
        return True

    # psycopg connection errors
    if isinstance(error, (psycopg.errors.ConnectionTimeout,
                         psycopg.errors.AdminShutdown,
                         psycopg.errors.CannotConnectNow,
                         psycopg.errors.ConnectionException,
                         psycopg.errors.ConnectionDoesNotExist)):
        return True

    # Check error message for common connection issues
    error_msg = str(error).lower()
    return any(keyword in error_msg for keyword in [
        'connection timeout', 'connection failed', 'connection refused',
        'connection closed', 'server closed', 'connection lost',
        'timeout expired', 'connection reset', 'connection aborted'
    ])


def retry_db_operation(
    operation: Callable[[], T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    operation_name: str = "Database operation"
) -> T:
    """
    Retry a database operation with exponential backoff.

    Args:
        operation: Function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        operation_name: Name of the operation for logging

    Returns:
        Result of the operation

    Raises:
        Last exception if all retries fail
    """
    logger = logging.getLogger(__name__)

    for attempt in range(max_retries + 1):
        try:
            result = operation()
            if attempt > 0:
                logger.info(f"✅ {operation_name} succeeded on attempt {attempt + 1}")
            return result

        except Exception as e:
            is_last_attempt = attempt == max_retries
            is_retryable = is_connection_error(e)

            if is_last_attempt or not is_retryable:
                if is_last_attempt:
                    logger.error(f"❌ {operation_name} failed after {max_retries + 1} attempts: {e}")
                else:
                    logger.error(f"❌ {operation_name} failed with non-retryable error: {e}")
                raise

            # Calculate delay with exponential backoff and jitter
            delay = min(base_delay * (2 ** attempt), max_delay)
            jitter = delay * 0.1  # 10% jitter
            actual_delay = delay + (time.time() % jitter)

            logger.warning(
                f"⚠️  {operation_name} failed on attempt {attempt + 1}: {e}. "
                f"Retrying in {actual_delay:.1f}s..."
            )
            time.sleep(actual_delay)


@contextmanager
def get_db_session_with_retry(
    max_retries: int = 3,
    operation_name: str = "Database session"
) -> Generator[Session, None, None]:
    """
    Context manager for database sessions with built-in retry logic.

    This is the recommended way to handle database operations in background tasks
    that might encounter connection issues.

    Usage:
        with get_db_session_with_retry(max_retries=5, operation_name="Automation check") as db:
            # perform database operations
    """
    def create_session():
        return SessionLocal()

    # Use retry logic to establish the connection
    db = retry_db_operation(
        operation=create_session,
        max_retries=max_retries,
        operation_name=f"{operation_name} - session creation"
    )

    try:
        yield db

        # Commit with retry logic
        def commit_operation():
            db.commit()
            return None

        retry_db_operation(
            operation=commit_operation,
            max_retries=2,  # Fewer retries for commit
            operation_name=f"{operation_name} - commit"
        )

    except Exception:
        try:
            db.rollback()
        except Exception as rollback_error:
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to rollback transaction: {rollback_error}")
        raise
    finally:
        try:
            db.close()
        except Exception as close_error:
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to close database session: {close_error}")

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
