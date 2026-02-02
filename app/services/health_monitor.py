# app/services/health_monitor.py
"""
Service health monitoring system with comprehensive health checks.
"""
import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging
import psutil

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.db import get_db_session_with_retry
from app.core.config import get_settings
from app.services.circuit_breaker import CircuitBreakerRegistry
from app.services.cache_service import CacheManager

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: HealthStatus
    message: str
    response_time_ms: float
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "response_time_ms": round(self.response_time_ms, 2),
            "timestamp": self.timestamp.isoformat(),
            "details": self.details or {}
        }


class HealthCheck(ABC):
    """Abstract base class for health checks"""

    def __init__(self, name: str, timeout: float = 5.0):
        self.name = name
        self.timeout = timeout

    @abstractmethod
    async def check(self) -> HealthCheckResult:
        """Perform the health check"""
        pass

    async def execute(self) -> HealthCheckResult:
        """Execute health check with timeout and error handling"""
        start_time = time.time()
        try:
            result = await asyncio.wait_for(self.check(), timeout=self.timeout)
            result.response_time_ms = (time.time() - start_time) * 1000
            return result
        except asyncio.TimeoutError:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.CRITICAL,
                message=f"Health check timed out after {self.timeout}s",
                response_time_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.CRITICAL,
                message=f"Health check failed: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.utcnow(),
                details={"error": str(e)}
            )


class DatabaseHealthCheck(HealthCheck):
    """Database connectivity health check"""

    def __init__(self):
        super().__init__("database", timeout=10.0)

    async def check(self) -> HealthCheckResult:
        """Check database health"""
        try:
            with get_db_session_with_retry() as db:
                # Simple connectivity test
                result = db.execute(text("SELECT 1 as health_check"))
                row = result.fetchone()

                if row and row[0] == 1:
                    # Additional database metrics
                    pool_status = self._get_pool_status(db)

                    return HealthCheckResult(
                        name=self.name,
                        status=HealthStatus.HEALTHY,
                        message="Database connection successful",
                        response_time_ms=0,  # Will be set by execute()
                        timestamp=datetime.utcnow(),
                        details=pool_status
                    )
                else:
                    return HealthCheckResult(
                        name=self.name,
                        status=HealthStatus.UNHEALTHY,
                        message="Database query returned unexpected result",
                        response_time_ms=0,
                        timestamp=datetime.utcnow()
                    )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.CRITICAL,
                message=f"Database connection failed: {str(e)}",
                response_time_ms=0,
                timestamp=datetime.utcnow(),
                details={"error": str(e)}
            )

    def _get_pool_status(self, db: Session) -> Dict[str, Any]:
        """Get database connection pool status"""
        try:
            engine = db.get_bind()
            pool = getattr(engine.pool, '_pool', None)

            if pool:
                return {
                    "pool_size": getattr(pool, 'size', 'unknown'),
                    "checked_in": getattr(pool, 'checkedin', 'unknown'),
                    "checked_out": getattr(pool, 'checkedout', 'unknown'),
                    "overflow": getattr(pool, 'overflow', 'unknown')
                }
        except Exception:
            pass

        return {"pool_info": "unavailable"}


class RedisHealthCheck(HealthCheck):
    """Redis connectivity health check"""

    def __init__(self):
        super().__init__("redis", timeout=5.0)

    async def check(self) -> HealthCheckResult:
        """Check Redis health"""
        try:
            import redis

            settings = get_settings()
            redis_url = getattr(settings, 'REDIS_URL', None)

            if not redis_url:
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.DEGRADED,
                    message="Redis not configured (using in-memory fallback)",
                    response_time_ms=0,
                    timestamp=datetime.utcnow()
                )

            client = redis.from_url(redis_url, socket_timeout=2)
            pong = client.ping()

            if pong:
                # Get Redis info
                info = client.info('server')
                return HealthCheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    message="Redis connection successful",
                    response_time_ms=0,
                    timestamp=datetime.utcnow(),
                    details={
                        "version": info.get('redis_version', 'unknown'),
                        "uptime_days": info.get('uptime_in_days', 'unknown'),
                        "connected_clients": info.get('connected_clients', 'unknown')
                    }
                )

        except ImportError:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.DEGRADED,
                message="Redis client not installed",
                response_time_ms=0,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Redis connection failed: {str(e)}",
                response_time_ms=0,
                timestamp=datetime.utcnow(),
                details={"error": str(e)}
            )


class SystemHealthCheck(HealthCheck):
    """System resources health check"""

    def __init__(self):
        super().__init__("system", timeout=3.0)

    async def check(self) -> HealthCheckResult:
        """Check system health"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()

            # Disk usage
            disk = psutil.disk_usage('/')

            # Determine status based on thresholds
            status = HealthStatus.HEALTHY
            messages = []

            if cpu_percent > 90:
                status = HealthStatus.CRITICAL
                messages.append(f"CPU usage critical: {cpu_percent:.1f}%")
            elif cpu_percent > 75:
                status = HealthStatus.DEGRADED
                messages.append(f"CPU usage high: {cpu_percent:.1f}%")

            if memory.percent > 90:
                status = HealthStatus.CRITICAL
                messages.append(f"Memory usage critical: {memory.percent:.1f}%")
            elif memory.percent > 80:
                status = HealthStatus.DEGRADED
                messages.append(f"Memory usage high: {memory.percent:.1f}%")

            if disk.percent > 95:
                status = HealthStatus.CRITICAL
                messages.append(f"Disk usage critical: {disk.percent:.1f}%")
            elif disk.percent > 85:
                status = HealthStatus.DEGRADED
                messages.append(f"Disk usage high: {disk.percent:.1f}%")

            message = "; ".join(messages) if messages else "System resources normal"

            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                response_time_ms=0,
                timestamp=datetime.utcnow(),
                details={
                    "cpu_percent": round(cpu_percent, 1),
                    "memory_percent": round(memory.percent, 1),
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "disk_percent": round(disk.percent, 1),
                    "disk_free_gb": round(disk.free / (1024**3), 2)
                }
            )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.CRITICAL,
                message=f"System check failed: {str(e)}",
                response_time_ms=0,
                timestamp=datetime.utcnow(),
                details={"error": str(e)}
            )


class ExternalServiceHealthCheck(HealthCheck):
    """Health check for external services"""

    def __init__(self, service_name: str, health_url: str, expected_status: int = 200):
        super().__init__(f"external_{service_name}", timeout=10.0)
        self.service_name = service_name
        self.health_url = health_url
        self.expected_status = expected_status

    async def check(self) -> HealthCheckResult:
        """Check external service health"""
        try:
            import httpx

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.health_url)

                if response.status_code == self.expected_status:
                    return HealthCheckResult(
                        name=self.name,
                        status=HealthStatus.HEALTHY,
                        message=f"{self.service_name} service is healthy",
                        response_time_ms=0,
                        timestamp=datetime.utcnow(),
                        details={
                            "status_code": response.status_code,
                            "url": self.health_url
                        }
                    )
                else:
                    return HealthCheckResult(
                        name=self.name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"{self.service_name} returned status {response.status_code}",
                        response_time_ms=0,
                        timestamp=datetime.utcnow(),
                        details={
                            "status_code": response.status_code,
                            "expected_status": self.expected_status,
                            "url": self.health_url
                        }
                    )

        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.CRITICAL,
                message=f"{self.service_name} health check failed: {str(e)}",
                response_time_ms=0,
                timestamp=datetime.utcnow(),
                details={"error": str(e), "url": self.health_url}
            )


class ServiceHealthMonitor:
    """Comprehensive service health monitoring"""

    def __init__(self):
        self.health_checks: List[HealthCheck] = []
        self.last_check_time: Optional[datetime] = None
        self.last_results: Dict[str, HealthCheckResult] = {}
        self.check_history: List[Dict[str, Any]] = []
        self.max_history_size = 100

        # Initialize default health checks
        self._initialize_default_checks()

    def _initialize_default_checks(self):
        """Initialize default health checks"""
        self.add_health_check(DatabaseHealthCheck())
        self.add_health_check(RedisHealthCheck())
        self.add_health_check(SystemHealthCheck())

        # Add external service checks based on configuration
        settings = get_settings()
        if hasattr(settings, 'OCR_API_URL') and settings.OCR_API_URL:
            self.add_health_check(ExternalServiceHealthCheck(
                "OCR",
                f"{settings.OCR_API_URL}/health"
            ))

    def add_health_check(self, health_check: HealthCheck):
        """Add a health check"""
        self.health_checks.append(health_check)
        logger.info(f"Added health check: {health_check.name}")

    async def check_all(self) -> Dict[str, Any]:
        """Run all health checks"""
        start_time = time.time()
        results = {}
        overall_status = HealthStatus.HEALTHY

        # Run all checks concurrently
        tasks = [check.execute() for check in self.health_checks]
        check_results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in check_results:
            if isinstance(result, Exception):
                logger.error(f"Health check failed with exception: {result}")
                continue

            results[result.name] = result
            self.last_results[result.name] = result

            # Determine overall status (worst status wins)
            if result.status == HealthStatus.CRITICAL:
                overall_status = HealthStatus.CRITICAL
            elif result.status == HealthStatus.UNHEALTHY and overall_status != HealthStatus.CRITICAL:
                overall_status = HealthStatus.UNHEALTHY
            elif result.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED

        # Calculate summary
        total_time = (time.time() - start_time) * 1000
        self.last_check_time = datetime.utcnow()

        # Add circuit breaker information
        circuit_breakers = CircuitBreakerRegistry.get_all_states()
        cache_stats = CacheManager.get_global_cache_stats()

        summary = {
            "status": overall_status.value,
            "timestamp": self.last_check_time.isoformat(),
            "total_checks": len(results),
            "healthy_checks": len([r for r in results.values() if r.status == HealthStatus.HEALTHY]),
            "degraded_checks": len([r for r in results.values() if r.status == HealthStatus.DEGRADED]),
            "unhealthy_checks": len([r for r in results.values() if r.status == HealthStatus.UNHEALTHY]),
            "critical_checks": len([r for r in results.values() if r.status == HealthStatus.CRITICAL]),
            "total_response_time_ms": round(total_time, 2),
            "checks": {name: result.to_dict() for name, result in results.items()},
            "circuit_breakers": circuit_breakers,
            "cache_stats": cache_stats
        }

        # Store in history
        self._add_to_history(summary)

        return summary

    def _add_to_history(self, summary: Dict[str, Any]):
        """Add check results to history"""
        # Remove detailed check results for history (save space)
        history_entry = {
            "timestamp": summary["timestamp"],
            "status": summary["status"],
            "total_checks": summary["total_checks"],
            "healthy_checks": summary["healthy_checks"],
            "degraded_checks": summary["degraded_checks"],
            "unhealthy_checks": summary["unhealthy_checks"],
            "critical_checks": summary["critical_checks"],
            "total_response_time_ms": summary["total_response_time_ms"]
        }

        self.check_history.append(history_entry)

        # Limit history size
        if len(self.check_history) > self.max_history_size:
            self.check_history.pop(0)

    def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health check history"""
        if not hours:
            return self.check_history

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            entry for entry in self.check_history
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
        ]

    def get_service_uptime(self) -> Dict[str, Any]:
        """Calculate service uptime statistics"""
        if len(self.check_history) < 2:
            return {"uptime_percentage": 100.0, "checks_analyzed": len(self.check_history)}

        healthy_checks = len([
            entry for entry in self.check_history
            if entry["status"] in [HealthStatus.HEALTHY.value, HealthStatus.DEGRADED.value]
        ])

        uptime_percentage = (healthy_checks / len(self.check_history)) * 100

        return {
            "uptime_percentage": round(uptime_percentage, 2),
            "checks_analyzed": len(self.check_history),
            "healthy_checks": healthy_checks,
            "total_checks": len(self.check_history)
        }


# Global health monitor instance
health_monitor = ServiceHealthMonitor()


async def get_health_status() -> Dict[str, Any]:
    """Get current health status"""
    return await health_monitor.check_all()


async def get_health_summary() -> Dict[str, Any]:
    """Get health summary with uptime statistics"""
    current_health = await health_monitor.check_all()
    uptime_stats = health_monitor.get_service_uptime()
    history = health_monitor.get_health_history(hours=1)  # Last hour

    return {
        "current_status": current_health,
        "uptime_stats": uptime_stats,
        "recent_history": history[-10:] if history else []  # Last 10 checks
    }