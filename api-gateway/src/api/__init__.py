# api-gateway/src/api/__init__.py
"""REST API proxy routes."""

from . import invoice, scriptclient, audit_sales, ads_alert

__all__ = [
    "invoice",
    "scriptclient",
    "audit_sales",
    "ads_alert",
]
