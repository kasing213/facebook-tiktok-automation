# app/core/monitoring.py
"""
Helpers for collecting lightweight diagnostic snapshots that are useful while
testing locally before pushing a deployment.
"""
from __future__ import annotations

from datetime import datetime
from time import perf_counter
from typing import Any, Dict

from sqlalchemy import text

from app.core.config import Settings
from app.core.db import engine


ServiceStatus = Dict[str, Any]


def _bool_secret(value: Any) -> bool:
    """Return True if the provided SecretStr/optional value contains data."""
    if value is None:
        return False
    try:
        return bool(value.get_secret_value())
    except AttributeError:
        return bool(value)


def collect_monitoring_snapshot(settings: Settings) -> Dict[str, Any]:
    """
    Collect runtime diagnostics that we can log/return from the health check.
    """
    services: Dict[str, ServiceStatus] = {}

    # Database connectivity check
    db_status: ServiceStatus = {"status": "unknown", "latency_ms": None, "detail": None}
    started = perf_counter()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status["status"] = "ok"
        db_status["latency_ms"] = round((perf_counter() - started) * 1000, 2)
    except Exception as exc:  # pragma: no cover - log helper
        db_status["status"] = "error"
        db_status["detail"] = str(exc)
    services["database"] = db_status

    # Third-party configuration checks
    services["telegram_bot"] = {
        "status": "configured" if _bool_secret(settings.TELEGRAM_BOT_TOKEN) else "missing"
    }
    services["facebook_integration"] = {
        "status": "configured" if settings.FB_APP_ID else "missing"
    }
    services["tiktok_integration"] = {
        "status": "configured" if settings.TIKTOK_CLIENT_KEY else "missing"
    }

    overall_status = "healthy"
    for service in services.values():
        if service["status"] not in ("ok", "configured"):
            overall_status = "degraded"
            break

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENV,
        "services": services,
        "overall_status": overall_status,
    }


def log_monitoring_snapshot(logger, snapshot: Dict[str, Any], context: str = "health"):
    """
    Emit a concise log line for local monitoring.
    """
    db = snapshot["services"]["database"]
    logger.info(
        "MONITOR[%s] status=%s env=%s db=%s latency=%sms telegram=%s facebook=%s tiktok=%s",
        context,
        snapshot["overall_status"],
        snapshot["environment"],
        db["status"],
        db.get("latency_ms"),
        snapshot["services"]["telegram_bot"]["status"],
        snapshot["services"]["facebook_integration"]["status"],
        snapshot["services"]["tiktok_integration"]["status"],
    )
