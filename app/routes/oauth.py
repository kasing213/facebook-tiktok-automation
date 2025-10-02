# app/routes/oauth.py
"""
OAuth routes for Facebook and TikTok integration.

Demonstrates proper dependency injection usage in FastAPI routes.
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.deps import (
    FacebookOAuthProvider, TikTokOAuthProvider,
    AuthSvc, LoggerDep, SettingsDep
)
from app.core.models import Platform

router = APIRouter(prefix="/oauth", tags=["oauth"])


@router.get("/facebook/authorize")
def facebook_authorize(
    tenant_id: str = Query(..., description="Tenant ID for OAuth flow"),
    facebook_oauth: FacebookOAuthProvider = None,
    logger: LoggerDep = None
):
    """Initiate Facebook OAuth authorization flow"""
    try:
        auth_url = facebook_oauth.auth_url(tenant_id)
        logger.info(f"Facebook OAuth initiated for tenant {tenant_id}")
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"Facebook OAuth initiation failed: {e}")
        raise HTTPException(status_code=500, detail="OAuth initiation failed")


@router.get("/facebook/callback")
async def facebook_callback(
    code: str = Query(..., description="OAuth authorization code"),
    state: str = Query(..., description="OAuth state parameter"),
    facebook_oauth: FacebookOAuthProvider = None,
    auth_service: AuthSvc = None,
    logger: LoggerDep = None
):
    """Handle Facebook OAuth callback"""
    try:
        # Validate state and extract tenant info
        state_data = await facebook_oauth.validate_state(state)
        tenant_id = state_data["tenant_id"]

        # Exchange code for tokens
        oauth_result = await facebook_oauth.exchange(code)
        logger.info(f"Facebook OAuth successful for tenant {tenant_id}")

        # Store tokens securely
        token = auth_service.store_oauth_token(tenant_id, oauth_result)

        return {
            "status": "success",
            "platform": "facebook",
            "tenant_id": tenant_id,
            "token_id": str(token.id),
            "expires_at": token.expires_at.isoformat() if token.expires_at else None
        }

    except ValueError as e:
        logger.error(f"Facebook OAuth validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Facebook OAuth callback failed: {e}")
        raise HTTPException(status_code=500, detail="OAuth callback failed")


@router.get("/tiktok/authorize")
def tiktok_authorize(
    tenant_id: str = Query(..., description="Tenant ID for OAuth flow"),
    tiktok_oauth: TikTokOAuthProvider = None,
    logger: LoggerDep = None
):
    """Initiate TikTok OAuth authorization flow"""
    try:
        auth_url = tiktok_oauth.auth_url(tenant_id)
        logger.info(f"TikTok OAuth initiated for tenant {tenant_id}")
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"TikTok OAuth initiation failed: {e}")
        raise HTTPException(status_code=500, detail="OAuth initiation failed")


@router.get("/tiktok/callback")
async def tiktok_callback(
    code: str = Query(..., description="OAuth authorization code"),
    state: str = Query(..., description="OAuth state parameter"),
    tiktok_oauth: TikTokOAuthProvider = None,
    auth_service: AuthSvc = None,
    logger: LoggerDep = None
):
    """Handle TikTok OAuth callback"""
    try:
        # Validate state and extract tenant info
        state_data = await tiktok_oauth.validate_state(state)
        tenant_id = state_data["tenant_id"]

        # Exchange code for tokens
        oauth_result = await tiktok_oauth.exchange(code)
        logger.info(f"TikTok OAuth successful for tenant {tenant_id}")

        # Store tokens securely
        token = auth_service.store_oauth_token(tenant_id, oauth_result)

        return {
            "status": "success",
            "platform": "tiktok",
            "tenant_id": tenant_id,
            "token_id": str(token.id),
            "expires_at": token.expires_at.isoformat() if token.expires_at else None
        }

    except ValueError as e:
        logger.error(f"TikTok OAuth validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"TikTok OAuth callback failed: {e}")
        raise HTTPException(status_code=500, detail="OAuth callback failed")


@router.get("/status/{tenant_id}")
def oauth_status(
    tenant_id: str,
    auth_service: AuthSvc = None,
    logger: LoggerDep = None
):
    """Get OAuth status for a tenant"""
    try:
        facebook_tokens = auth_service.get_tenant_tokens(tenant_id, Platform.facebook)
        tiktok_tokens = auth_service.get_tenant_tokens(tenant_id, Platform.tiktok)

        return {
            "tenant_id": tenant_id,
            "facebook": {
                "connected": len(facebook_tokens) > 0,
                "valid_tokens": len([t for t in facebook_tokens if t.is_valid]),
                "tokens": [
                    {
                        "id": str(token.id),
                        "account_ref": token.account_ref,
                        "is_valid": token.is_valid,
                        "expires_at": token.expires_at.isoformat() if token.expires_at else None
                    }
                    for token in facebook_tokens
                ]
            },
            "tiktok": {
                "connected": len(tiktok_tokens) > 0,
                "valid_tokens": len([t for t in tiktok_tokens if t.is_valid]),
                "tokens": [
                    {
                        "id": str(token.id),
                        "account_ref": token.account_ref,
                        "is_valid": token.is_valid,
                        "expires_at": token.expires_at.isoformat() if token.expires_at else None
                    }
                    for token in tiktok_tokens
                ]
            }
        }

    except Exception as e:
        logger.error(f"OAuth status check failed: {e}")
        raise HTTPException(status_code=500, detail="Status check failed")