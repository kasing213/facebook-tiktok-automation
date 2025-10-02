# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.deps import get_logger, get_settings_dep, SettingsDep, TenantSvc, AuthSvc
from app.core.config import get_settings
from app.core.db import init_db, dispose_engine
from app.routes import oauth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    log = get_logger()
    s = get_settings()

    # Store settings in app state for easy access
    app.state.settings = s

    # Initialize database and validate schema
    init_db()
    log.info("🚀 FB/TikTok Automation API started (env=%s)", s.ENV)

    try:
        yield
    finally:
        dispose_engine()
        log.info("🛑 API shutting down")

# Create FastAPI application
app = FastAPI(
    title="Facebook/TikTok Automation API",
    description="Multi-tenant social media automation platform with FastAPI and Telegram bot integration",
    version="0.2.0",
    lifespan=lifespan,
)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(oauth_router)

# Health check endpoint with enhanced information
@app.get("/health", tags=["system"])
def health_check(settings: SettingsDep):
    """System health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENV,
        "version": "0.2.0",
        "services": {
            "database": "connected",
            "telegram_bot": "configured" if settings.TELEGRAM_BOT_TOKEN else "not_configured",
            "facebook_integration": "configured" if settings.FB_APP_ID else "not_configured",
            "tiktok_integration": "configured" if settings.TIKTOK_CLIENT_KEY else "not_configured",
        }
    }

# Tenant management endpoints
@app.get("/api/tenants", tags=["tenants"])
def list_tenants(tenant_service: TenantSvc):
    """List all active tenants"""
    tenants = tenant_service.get_active_tenants()
    return [
        {
            "id": str(tenant.id),
            "name": tenant.name,
            "slug": tenant.slug,
            "is_active": tenant.is_active,
            "created_at": tenant.created_at.isoformat(),
        }
        for tenant in tenants
    ]

@app.get("/api/tenants/{tenant_id}", tags=["tenants"])
def get_tenant(tenant_id: str, tenant_service: TenantSvc):
    """Get tenant details by ID"""
    tenant = tenant_service.get_tenant_by_id(tenant_id)
    if not tenant:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Tenant not found")

    users = tenant_service.get_tenant_users(tenant.id)

    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "slug": tenant.slug,
        "is_active": tenant.is_active,
        "settings": tenant.settings,
        "created_at": tenant.created_at.isoformat(),
        "updated_at": tenant.updated_at.isoformat(),
        "user_count": len(users),
    }

# Authentication status endpoint
@app.get("/api/tenants/{tenant_id}/auth-status", tags=["authentication"])
def get_auth_status(tenant_id: str, auth_service: AuthSvc):
    """Get authentication status for a tenant"""
    from app.core.models import Platform

    platforms = {
        Platform.facebook: auth_service.get_tenant_tokens(tenant_id, Platform.facebook),
        Platform.tiktok: auth_service.get_tenant_tokens(tenant_id, Platform.tiktok),
    }

    return {
        "tenant_id": tenant_id,
        "platforms": {
            platform.value: {
                "connected": len(tokens) > 0,
                "valid_tokens": len([t for t in tokens if t.is_valid]),
                "accounts": [
                    {
                        "account_ref": token.account_ref,
                        "account_name": token.account_name,
                        "is_valid": token.is_valid,
                        "expires_at": token.expires_at.isoformat() if token.expires_at else None,
                    }
                    for token in tokens
                ]
            }
            for platform, tokens in platforms.items()
        }
    }
