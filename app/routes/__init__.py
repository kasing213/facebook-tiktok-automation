# app/routes/__init__.py
from .oauth import router as oauth_router

__all__ = ["oauth_router"]