# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.deps import get_logger, get_settings_dep, SettingsDep, TenantSvc, AuthSvc
from app.core.config import get_settings
from app.core.db import init_db, dispose_engine
from app.core.monitoring import collect_monitoring_snapshot, log_monitoring_snapshot
from app.routes import oauth_router
from app.routes.webhooks import router as webhook_router
from app.routes.auth import router as auth_router, get_current_user
from app.core.models import User
from app.routes.data_deletion import router as data_deletion_router
from app.routes.ip_management import router as ip_mgmt_router
from app.routes.telegram import router as telegram_router
from app.routes.integrations.invoice import router as invoice_integration_router
from app.routes.subscriptions import router as subscription_router
from app.routes.billing import router as billing_router
from app.routes.users import router as users_router
from app.routes.subscription import router as subscription_mgmt_router
from app.routes.subscription_payment import router as subscription_payment_router
from app.routes.inventory import router as inventory_router
from app.routes.email_verification import router as email_verification_router
from app.routes.ads_alert import router as ads_alert_router
from app.routes.moderation import router as moderation_router
from app.routes.usage import router as usage_router
from app.routes.dashboard import router as dashboard_router


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
    from app.jobs.ads_alert_scheduler import run_ads_alert_scheduler
    from app.jobs.subscription_trial_checker import run_trial_checker_scheduler

    log = get_logger()
    s = get_settings()

    # Store settings in app state for easy access
    app.state.settings = s

    # Initialize database and validate schema
    init_db()
    log.info("🚀 FB/TikTok Automation API started (env=%s)", s.ENV)
    log_monitoring_snapshot(log, collect_monitoring_snapshot(s), context="startup")

    # NOTE: Mock seeding removed - using real PostgreSQL data
    # To re-enable mock mode for local testing, set INVOICE_MOCK_MODE=True
    # and ensure seed_sample_data() function signature is correct

    # Start background tasks
    token_refresh_task = None
    cleanup_task = None
    automation_task = None
    ads_alert_task = None
    trial_checker_task = None

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

        # Start ads_alert scheduler for scheduled promotions
        ads_alert_task = asyncio.create_task(run_ads_alert_scheduler(check_interval=60))
        log.info("✅ Ads Alert scheduler started (check interval: 60s)")

        # Start trial checker scheduler (checks every hour for expired trials)
        trial_checker_task = asyncio.create_task(run_trial_checker_scheduler(check_interval=3600))
        log.info("✅ Trial checker scheduler started (check interval: 3600s)")

        yield
    finally:
        # Cancel background tasks gracefully
        tasks_to_cancel = [
            ("Token Refresh", token_refresh_task),
            ("Cleanup", cleanup_task),
            ("Automation Scheduler", automation_task),
            ("Ads Alert Scheduler", ads_alert_task),
            ("Trial Checker", trial_checker_task)
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

# Add rate limiting middleware
from app.middleware.rate_limit import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

# Email verification middleware disabled - SMTP not available on Railway
# Users are auto-verified on registration
# from app.middleware.email_verification import email_verification_middleware
# app.middleware("http")(email_verification_middleware)

# Include routers
app.include_router(auth_router)
app.include_router(oauth_router)
app.include_router(webhook_router)
app.include_router(data_deletion_router)
app.include_router(ip_mgmt_router)
app.include_router(telegram_router)
app.include_router(invoice_integration_router)
app.include_router(subscription_router)
app.include_router(billing_router)
app.include_router(users_router)
app.include_router(subscription_mgmt_router)
app.include_router(subscription_payment_router)
app.include_router(inventory_router)
app.include_router(email_verification_router)
app.include_router(ads_alert_router)
app.include_router(moderation_router)
app.include_router(usage_router)
app.include_router(dashboard_router)

# Mount static files for policy pages
app.mount("/policies", StaticFiles(directory="public/policies", html=True), name="policies")

# TikTok verification file endpoint
@app.get("/tiktokfIJT8p1JssnSfzGv35JP2RYDl3O7u5q0.txt", tags=["system"])
def tiktok_verification():
    """TikTok domain verification file"""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse("tiktok-developers-site-verification=fIJT8p1JssnSfzGv35JP2RYDl3O7u5q0")

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
            "webhooks": "/api/webhooks",
            "telegram": "/telegram"
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

class TenantRegistrationRequest(BaseModel):
    """Request for creating a tenant during registration"""
    name: str = Field(..., min_length=1, max_length=100, description="Organization name")


def generate_tenant_slug(name: str) -> str:
    """Generate a unique slug from organization name"""
    import re
    import uuid
    # Convert to lowercase and replace spaces/special chars with hyphens
    base_slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    if not base_slug:
        base_slug = 'org'
    # Add short UUID suffix to ensure uniqueness
    unique_suffix = str(uuid.uuid4())[:8]
    return f"{base_slug}-{unique_suffix}"


@app.post("/api/tenants/register", tags=["tenants"])
def create_tenant_for_registration(
    request: TenantRegistrationRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new tenant for user registration.

    Each new user registration creates their own organization/tenant.
    The registering user will become the owner (admin) of this tenant.
    """
    from app.repositories import TenantRepository

    tenant_repo = TenantRepository(db)

    try:
        # Generate unique slug from organization name
        slug = generate_tenant_slug(request.name)

        # Create tenant (without admin user - user will be created in /auth/register)
        tenant = tenant_repo.create_tenant(request.name, slug, settings={})
        db.commit()

        return {
            "id": str(tenant.id),
            "name": tenant.name,
            "slug": tenant.slug,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create organization: {str(e)}")

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
def get_auth_status(
    tenant_id: str,
    auth_service: AuthSvc,
    tenant_service: TenantSvc,
    current_user: User = Depends(get_current_user)
):
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

    if tenant_uuid != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Tenant mismatch")

    platforms = {
        Platform.facebook: auth_service.get_tenant_tokens(
            tenant_uuid,
            Platform.facebook,
            user_id=current_user.id
        ),
        Platform.tiktok: auth_service.get_tenant_tokens(
            tenant_uuid,
            Platform.tiktok,
            user_id=current_user.id
        ),
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
