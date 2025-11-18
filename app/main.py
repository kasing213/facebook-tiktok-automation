# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.deps import get_logger, get_settings_dep, SettingsDep, TenantSvc, AuthSvc
from app.core.config import get_settings
from app.core.db import init_db, dispose_engine
from app.core.monitoring import collect_monitoring_snapshot, log_monitoring_snapshot
from app.routes import oauth_router
from app.routes.webhooks import router as webhook_router
from app.routes.auth import router as auth_router


# Request/Response models
class CreateTenantRequest(BaseModel):
    name: str = Field(..., description="Organization/tenant name", min_length=2, max_length=100)
    slug: str = Field(..., description="Unique URL-safe identifier", min_length=2, max_length=50, pattern=r'^[a-z0-9-]+$')
    admin_telegram_id: str | None = Field(None, description="Admin Telegram user ID")
    admin_email: str | None = Field(None, description="Admin email address")
    admin_username: str | None = Field(None, description="Admin username")
    settings: dict | None = Field(None, description="Optional tenant settings")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Acme Corporation",
                    "slug": "acme-corp",
                    "admin_email": "admin@acme.com",
                    "admin_username": "acme_admin"
                }
            ]
        }
    }

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    import asyncio
    from app.jobs.token_refresh import run_token_refresh_scheduler, run_daily_cleanup_scheduler
    from app.jobs.automation_scheduler import run_automation_scheduler

    log = get_logger()
    s = get_settings()

    # Store settings in app state for easy access
    app.state.settings = s

    # Initialize database and validate schema
    init_db()
    log.info("🚀 FB/TikTok Automation API started (env=%s)", s.ENV)
    log_monitoring_snapshot(log, collect_monitoring_snapshot(s), context="startup")

    # Start background tasks
    token_refresh_task = None
    cleanup_task = None
    automation_task = None

    try:
        # Start token refresh and cleanup tasks
        token_refresh_task = asyncio.create_task(run_token_refresh_scheduler())
        cleanup_task = asyncio.create_task(run_daily_cleanup_scheduler())
        log.info("✅ Background token refresh and cleanup tasks started")

        # Start automation scheduler with configurable interval
        automation_task = asyncio.create_task(
            run_automation_scheduler(check_interval=s.AUTOMATION_CHECK_INTERVAL)
        )
        log.info(f"✅ Automation scheduler started (check interval: {s.AUTOMATION_CHECK_INTERVAL}s)")

        yield
    finally:
        # Cancel background tasks gracefully
        tasks_to_cancel = [
            ("Token Refresh", token_refresh_task),
            ("Cleanup", cleanup_task),
            ("Automation Scheduler", automation_task)
        ]

        for task_name, task in tasks_to_cancel:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    log.info(f"✅ {task_name} task stopped")

        dispose_engine()
        log.info("🛑 API shutting down")

# Create FastAPI application
app = FastAPI(
    title="Facebook/TikTok Automation API",
    description="Multi-tenant social media automation platform with FastAPI and Telegram bot integration",
    version="0.2.0",
    lifespan=lifespan,
)

# Add CORS middleware
# Allow localhost for development and production domains from environment
settings = get_settings()
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
# Add frontend URL from environment if configured
if settings.FRONTEND_URL:
    frontend_url = str(settings.FRONTEND_URL).strip().rstrip('/')
    if frontend_url not in allowed_origins:
        allowed_origins.append(frontend_url)
    print(f"[CORS] Frontend URL loaded: {frontend_url}")
else:
    print("[CORS] WARNING: FRONTEND_URL not set in environment!")

print(f"[CORS] Allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(oauth_router)
app.include_router(webhook_router)

# Mount static files for policy pages
app.mount("/policies", StaticFiles(directory="public/policies", html=True), name="policies")

# Root endpoint
@app.get("/", tags=["system"])
def root():
    """API root endpoint with links to documentation"""
    return {
        "message": "Facebook/TikTok Automation API",
        "version": "0.2.0",
        "status": "running",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json"
        },
        "endpoints": {
            "health": "/health",
            "auth": "/auth",
            "oauth": "/oauth",
            "tenants": "/api/tenants",
            "webhooks": "/api/webhooks"
        }
    }

# Health check endpoint with enhanced information
@app.get("/health", tags=["system"])
def health_check(settings: SettingsDep):
    """System health check endpoint"""
    snapshot = collect_monitoring_snapshot(settings)

    if settings.ENV == "dev":
        log_monitoring_snapshot(get_logger(), snapshot, context="health")

    return {
        "status": snapshot["overall_status"],
        "environment": settings.ENV,
        "version": "0.2.0",
        "timestamp": snapshot["timestamp"],
        "services": snapshot["services"],
    }

# Tenant management endpoints
@app.post("/api/tenants", tags=["tenants"])
def create_tenant(request: CreateTenantRequest, tenant_service: TenantSvc):
    """Create a new tenant"""
    try:
        tenant, admin_user = tenant_service.create_tenant_with_admin(
            name=request.name,
            slug=request.slug,
            admin_telegram_id=request.admin_telegram_id,
            admin_email=request.admin_email,
            admin_username=request.admin_username,
            settings=request.settings or {}
        )
        return {
            "id": str(tenant.id),
            "name": tenant.name,
            "slug": tenant.slug,
            "is_active": tenant.is_active,
            "created_at": tenant.created_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create tenant")

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
def get_auth_status(tenant_id: str, auth_service: AuthSvc, tenant_service: TenantSvc):
    """Get authentication status for a tenant (accepts UUID or slug)"""
    from app.core.models import Platform
    from uuid import UUID

    # Try to resolve tenant_id (could be UUID or slug)
    try:
        # First try as UUID
        tenant_uuid = UUID(tenant_id)
        tenant = tenant_service.get_tenant_by_id(tenant_uuid)
    except ValueError:
        # If not a valid UUID, try as slug
        tenant = tenant_service.get_tenant_by_slug(tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail=f"Tenant not found: {tenant_id}")
        tenant_uuid = tenant.id

    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant not found: {tenant_id}")

    platforms = {
        Platform.facebook: auth_service.get_tenant_tokens(str(tenant_uuid), Platform.facebook),
        Platform.tiktok: auth_service.get_tenant_tokens(str(tenant_uuid), Platform.tiktok),
    }

    return {
        "tenant_id": str(tenant_uuid),
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
