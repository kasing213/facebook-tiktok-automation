# app/core/db_monitor.py
"""
Database connection monitoring and optimization service.

Monitors database performance and provides optimizations to reduce connection pressure:
- Connection pool monitoring
- Query performance tracking
- Slow query detection
- Connection leak detection
- Performance recommendations
"""
import time
import threading
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from contextlib import contextmanager
from sqlalchemy import text, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.db import engine, SessionLocal

logger = logging.getLogger(__name__)

@dataclass
class QueryMetrics:
    """Metrics for a database query"""
    sql: str
    duration_ms: float
    timestamp: datetime
    tenant_id: Optional[str] = None
    endpoint: Optional[str] = None
    connection_id: Optional[str] = None

@dataclass
class ConnectionMetrics:
    """Metrics for database connection usage"""
    connection_id: str
    created_at: datetime
    last_used: datetime
    query_count: int = 0
    total_time_ms: float = 0
    is_active: bool = True

class DatabaseMonitor:
    """
    Monitor database performance and connection usage.
    Helps identify optimization opportunities and potential issues.
    """

    def __init__(self, slow_query_threshold_ms: float = 100):
        self.slow_query_threshold = slow_query_threshold_ms
        self._queries: List[QueryMetrics] = []
        self._connections: Dict[str, ConnectionMetrics] = {}
        self._stats = {
            'total_queries': 0,
            'slow_queries': 0,
            'total_time_ms': 0,
            'active_connections': 0,
            'peak_connections': 0,
            'connection_leaks': 0
        }
        self._lock = threading.RLock()
        self._monitoring_enabled = True

        # Setup SQLAlchemy event listeners
        self._setup_event_listeners()

    def _setup_event_listeners(self):
        """Setup SQLAlchemy event listeners for monitoring"""

        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()

        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            if not self._monitoring_enabled:
                return

            duration_ms = (time.time() - context._query_start_time) * 1000

            with self._lock:
                # Record query metrics
                query_metric = QueryMetrics(
                    sql=statement[:500],  # Truncate long queries
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow(),
                    connection_id=str(id(conn))
                )

                self._queries.append(query_metric)
                self._stats['total_queries'] += 1
                self._stats['total_time_ms'] += duration_ms

                if duration_ms > self.slow_query_threshold:
                    self._stats['slow_queries'] += 1
                    logger.warning(f"Slow query detected: {duration_ms:.1f}ms - {statement[:100]}")

                # Keep only recent queries (last 1000 or 1 hour)
                cutoff_time = datetime.utcnow() - timedelta(hours=1)
                self._queries = [q for q in self._queries[-1000:] if q.timestamp > cutoff_time]

                # Update connection metrics
                self._update_connection_metrics(str(id(conn)), duration_ms)

    def _update_connection_metrics(self, connection_id: str, duration_ms: float):
        """Update metrics for a specific connection"""
        now = datetime.utcnow()

        if connection_id not in self._connections:
            self._connections[connection_id] = ConnectionMetrics(
                connection_id=connection_id,
                created_at=now,
                last_used=now
            )
            self._stats['active_connections'] += 1
            self._stats['peak_connections'] = max(
                self._stats['peak_connections'],
                self._stats['active_connections']
            )

        conn_metrics = self._connections[connection_id]
        conn_metrics.last_used = now
        conn_metrics.query_count += 1
        conn_metrics.total_time_ms += duration_ms

    @contextmanager
    def monitored_session(self, endpoint: str = None, tenant_id: str = None):
        """
        Context manager for monitored database sessions.
        Tracks session lifecycle and detects potential leaks.
        """
        session_start = time.time()
        db = SessionLocal()
        connection_id = str(id(db.connection()))

        try:
            yield db
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Database session error in {endpoint}: {e}")
            raise
        finally:
            session_duration = (time.time() - session_start) * 1000
            db.close()

            # Log long-running sessions
            if session_duration > 5000:  # 5 seconds
                logger.warning(f"Long session duration: {session_duration:.1f}ms in {endpoint}")

            # Mark connection as closed
            with self._lock:
                if connection_id in self._connections:
                    self._connections[connection_id].is_active = False
                    self._stats['active_connections'] -= 1

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        with self._lock:
            recent_queries = [q for q in self._queries if q.timestamp > datetime.utcnow() - timedelta(minutes=5)]

            avg_query_time = (
                sum(q.duration_ms for q in recent_queries) / len(recent_queries)
                if recent_queries else 0
            )

            return {
                'query_stats': {
                    'total_queries': self._stats['total_queries'],
                    'slow_queries': self._stats['slow_queries'],
                    'slow_query_rate': (
                        self._stats['slow_queries'] / max(self._stats['total_queries'], 1) * 100
                    ),
                    'avg_query_time_ms': round(avg_query_time, 2),
                    'recent_query_count': len(recent_queries)
                },
                'connection_stats': {
                    'active_connections': self._stats['active_connections'],
                    'peak_connections': self._stats['peak_connections'],
                    'total_connections': len(self._connections),
                    'connection_leaks': self._detect_connection_leaks()
                },
                'performance_score': self._calculate_performance_score()
            }

    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent slow queries for analysis"""
        with self._lock:
            slow_queries = [
                q for q in self._queries
                if q.duration_ms > self.slow_query_threshold
            ]

            # Sort by duration, most recent first
            slow_queries.sort(key=lambda x: (x.duration_ms, x.timestamp), reverse=True)

            return [
                {
                    'sql': query.sql,
                    'duration_ms': query.duration_ms,
                    'timestamp': query.timestamp.isoformat(),
                    'tenant_id': query.tenant_id,
                    'endpoint': query.endpoint
                }
                for query in slow_queries[:limit]
            ]

    def _detect_connection_leaks(self) -> int:
        """Detect potential connection leaks"""
        leak_threshold = timedelta(minutes=10)
        now = datetime.utcnow()
        leak_count = 0

        for conn_id, metrics in self._connections.items():
            if metrics.is_active and (now - metrics.last_used) > leak_threshold:
                leak_count += 1
                logger.warning(f"Potential connection leak detected: {conn_id}")

        return leak_count

    def _calculate_performance_score(self) -> int:
        """Calculate overall performance score (0-100)"""
        if self._stats['total_queries'] == 0:
            return 100

        # Base score
        score = 100

        # Penalty for slow queries
        slow_query_rate = self._stats['slow_queries'] / self._stats['total_queries']
        score -= min(50, slow_query_rate * 100)

        # Penalty for connection leaks
        leak_count = self._detect_connection_leaks()
        score -= min(30, leak_count * 10)

        # Penalty for high connection usage
        if self._stats['active_connections'] > 20:
            score -= 20

        return max(0, int(score))

    def get_optimization_recommendations(self) -> List[Dict[str, str]]:
        """Get performance optimization recommendations"""
        recommendations = []
        stats = self.get_performance_stats()

        # Slow query recommendations
        if stats['query_stats']['slow_query_rate'] > 10:
            recommendations.append({
                'type': 'query_optimization',
                'priority': 'high',
                'issue': 'High slow query rate',
                'recommendation': 'Add database indexes, optimize queries, or implement caching'
            })

        # Connection recommendations
        if stats['connection_stats']['active_connections'] > 15:
            recommendations.append({
                'type': 'connection_pooling',
                'priority': 'medium',
                'issue': 'High connection count',
                'recommendation': 'Review connection pooling settings or implement connection batching'
            })

        # Leak detection
        if stats['connection_stats']['connection_leaks'] > 0:
            recommendations.append({
                'type': 'connection_management',
                'priority': 'high',
                'issue': 'Connection leaks detected',
                'recommendation': 'Review database session management and ensure proper cleanup'
            })

        return recommendations

    def reset_stats(self):
        """Reset monitoring statistics"""
        with self._lock:
            self._queries.clear()
            self._connections.clear()
            self._stats = {
                'total_queries': 0,
                'slow_queries': 0,
                'total_time_ms': 0,
                'active_connections': 0,
                'peak_connections': 0,
                'connection_leaks': 0
            }

    def enable_monitoring(self):
        """Enable monitoring"""
        self._monitoring_enabled = True
        logger.info("Database monitoring enabled")

    def disable_monitoring(self):
        """Disable monitoring"""
        self._monitoring_enabled = False
        logger.info("Database monitoring disabled")

# Global monitor instance
db_monitor = DatabaseMonitor()

def get_db_monitored(endpoint: str = None, tenant_id: str = None):
    """
    Get monitored database session for FastAPI endpoints.
    Drop-in replacement for the standard get_db dependency.
    """
    with db_monitor.monitored_session(endpoint=endpoint, tenant_id=tenant_id) as db:
        yield db

# Health check queries
def run_health_check() -> Dict[str, Any]:
    """Run comprehensive database health check"""
    health_start = time.time()

    try:
        with db_monitor.monitored_session(endpoint="health_check") as db:
            # Basic connectivity
            result = db.execute(text("SELECT 1 as status")).fetchone()
            basic_check = result[0] == 1

            # Connection info
            result = db.execute(text("""
                SELECT
                    current_database(),
                    current_user,
                    version(),
                    now()
            """)).fetchone()

            db_name, user, version, server_time = result

            # Performance test
            perf_start = time.time()
            db.execute(text("SELECT COUNT(*) FROM information_schema.tables"))
            perf_time_ms = (time.time() - perf_start) * 1000

        health_duration = (time.time() - health_start) * 1000
        stats = db_monitor.get_performance_stats()

        return {
            'status': 'healthy' if basic_check else 'unhealthy',
            'database': db_name,
            'user': user,
            'version': version.split()[0:2],  # PostgreSQL version
            'server_time': server_time.isoformat(),
            'health_check_duration_ms': round(health_duration, 2),
            'performance_test_ms': round(perf_time_ms, 2),
            'performance_score': stats['performance_score'],
            'recommendations': db_monitor.get_optimization_recommendations()
        }

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'performance_score': 0
        }