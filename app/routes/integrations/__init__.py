# app/routes/integrations/__init__.py
"""
Integration routes for external services.

This package contains proxy routes that forward authenticated requests
to external APIs while handling JWT validation internally.
"""

from app.routes.integrations.invoice import router as invoice_router

__all__ = ["invoice_router"]
