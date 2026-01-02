# app/routes/oauth.py
"""
OAuth routes for Facebook and TikTok integration.

Demonstrates proper dependency injection usage in FastAPI routes.
"""
from urllib.parse import urlencode
import hmac
import hashlib
import base64
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, Form, Depends
from fastapi.responses import RedirectResponse, JSONResponse

from app.deps import (
    FacebookOAuthProvider, TikTokOAuthProvider, TikTokSvc,
    AuthSvc, LoggerDep, SettingsDep
)
from app.core.models import Platform, User
from app.routes.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["oauth"])


@router.get("/facebook/authorize")
def facebook_authorize(
    facebook_oauth: FacebookOAuthProvider,
    logger: LoggerDep,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Query(None, description="Tenant ID for OAuth flow")
):
    """Initiate Facebook OAuth authorization flow"""
    try:
        if tenant_id and str(current_user.tenant_id) != tenant_id:
            raise HTTPException(status_code=403, detail="Tenant mismatch")

        auth_url = facebook_oauth.auth_url(str(current_user.tenant_id), user_id=str(current_user.id))
        logger.info(f"Facebook OAuth initiated for tenant {current_user.tenant_id}")
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"Facebook OAuth initiation failed: {e}")
        raise HTTPException(status_code=500, detail="OAuth initiation failed")


@router.get("/facebook/authorize-url")
def facebook_authorize_url(
    facebook_oauth: FacebookOAuthProvider,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Query(None, description="Tenant ID for OAuth flow"),
):
    """Get Facebook OAuth authorization URL for the current user"""
    if tenant_id and str(current_user.tenant_id) != tenant_id:
        raise HTTPException(status_code=403, detail="Tenant mismatch")

    auth_url = facebook_oauth.auth_url(str(current_user.tenant_id), user_id=str(current_user.id))
    return {"auth_url": auth_url}


@router.get("/facebook/callback")
async def facebook_callback(
    facebook_oauth: FacebookOAuthProvider,
    auth_service: AuthSvc,
    logger: LoggerDep,
    settings: SettingsDep,
    code: str = Query(..., description="OAuth authorization code"),
    state: str = Query(..., description="OAuth state parameter")
):
    """Handle Facebook OAuth callback"""
    try:
        # Validate state and extract tenant info
        state_data = await facebook_oauth.validate_state(state)
        tenant_id = state_data["tenant_id"]
        user_id = state_data.get("user_id")
        if not user_id:
            raise ValueError("Missing user in OAuth state")
        try:
            user_uuid = UUID(user_id)
            tenant_uuid = UUID(tenant_id)
        except ValueError:
            raise ValueError("Invalid tenant or user in OAuth state")

        # Exchange code for tokens
        oauth_result = await facebook_oauth.exchange(code)
        logger.info(f"Facebook OAuth successful for tenant {tenant_id}")

        # Store tokens securely (including page tokens)
        token = auth_service.store_oauth_token(tenant_uuid, oauth_result, user_id=user_uuid)

        # Get page tokens for response
        page_tokens = auth_service.get_facebook_page_tokens(tenant_uuid, user_id=user_uuid)

        # Redirect to frontend dashboard with success message
        frontend_base = str(settings.FRONTEND_URL).rstrip("/")
        frontend_query = urlencode({"success": "facebook", "tenant_id": tenant_id})
        frontend_url = f"{frontend_base}/dashboard?{frontend_query}"
        return RedirectResponse(url=frontend_url)

    except ValueError as e:
        logger.error(f"Facebook OAuth validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Facebook OAuth callback failed: {e}")
        raise HTTPException(status_code=500, detail="OAuth callback failed")


@router.get("/tiktok/authorize")
def tiktok_authorize(
    tiktok_oauth: TikTokOAuthProvider,
    logger: LoggerDep,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Query(None, description="Tenant ID for OAuth flow")
):
    """Initiate TikTok OAuth authorization flow"""
    try:
        if tenant_id and str(current_user.tenant_id) != tenant_id:
            raise HTTPException(status_code=403, detail="Tenant mismatch")

        auth_url = tiktok_oauth.auth_url(str(current_user.tenant_id), user_id=str(current_user.id))
        logger.info(f"TikTok OAuth initiated for tenant {current_user.tenant_id}")
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"TikTok OAuth initiation failed: {e}")
        raise HTTPException(status_code=500, detail="OAuth initiation failed")


@router.get("/tiktok/authorize-url")
def tiktok_authorize_url(
    tiktok_oauth: TikTokOAuthProvider,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Query(None, description="Tenant ID for OAuth flow"),
):
    """Get TikTok OAuth authorization URL for the current user"""
    if tenant_id and str(current_user.tenant_id) != tenant_id:
        raise HTTPException(status_code=403, detail="Tenant mismatch")

    auth_url = tiktok_oauth.auth_url(str(current_user.tenant_id), user_id=str(current_user.id))
    return {"auth_url": auth_url}


@router.get("/tiktok/callback")
async def tiktok_callback(
    tiktok_oauth: TikTokOAuthProvider,
    auth_service: AuthSvc,
    logger: LoggerDep,
    settings: SettingsDep,
    code: str = Query(..., description="OAuth authorization code"),
    state: str = Query(..., description="OAuth state parameter")
):
    """Handle TikTok OAuth callback"""
    try:
        # Validate state and extract tenant info
        state_data = await tiktok_oauth.validate_state(state)
        tenant_id = state_data["tenant_id"]
        code_verifier = state_data.get("code_verifier")
        if not code_verifier:
            raise ValueError("Missing TikTok PKCE code verifier")
        user_id = state_data.get("user_id")
        if not user_id:
            raise ValueError("Missing user in OAuth state")
        try:
            user_uuid = UUID(user_id)
            tenant_uuid = UUID(tenant_id)
        except ValueError:
            raise ValueError("Invalid tenant or user in OAuth state")

        # Exchange code for tokens
        oauth_result = await tiktok_oauth.exchange(code, code_verifier=code_verifier)
        logger.info(f"TikTok OAuth successful for tenant {tenant_id}")

        # Store tokens securely (including user info)
        token = auth_service.store_oauth_token(tenant_uuid, oauth_result, user_id=user_uuid)

        # Get creator info for response
        creator_info = auth_service.get_tiktok_creator_info(tenant_uuid, user_id=user_uuid)

        # Redirect to frontend dashboard with success message
        frontend_base = str(settings.FRONTEND_URL).rstrip("/")
        frontend_query = urlencode({"success": "tiktok", "tenant_id": tenant_id})
        frontend_url = f"{frontend_base}/dashboard?{frontend_query}"
        return RedirectResponse(url=frontend_url)

    except ValueError as e:
        logger.error(f"TikTok OAuth validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"TikTok OAuth callback failed: {e}")
        raise HTTPException(status_code=500, detail="OAuth callback failed")


@router.get("/status/{tenant_id}")
def oauth_status(
    tenant_id: str,
    auth_service: AuthSvc,
    logger: LoggerDep,
    current_user: User = Depends(get_current_user)
):
    """Get OAuth status for a tenant"""
    try:
        if str(current_user.tenant_id) != tenant_id:
            raise HTTPException(status_code=403, detail="Tenant mismatch")

        facebook_tokens = auth_service.get_tenant_tokens(
            current_user.tenant_id,
            Platform.facebook,
            user_id=current_user.id
        )
        tiktok_tokens = auth_service.get_tenant_tokens(
            current_user.tenant_id,
            Platform.tiktok,
            user_id=current_user.id
        )

        return {
            "tenant_id": tenant_id,
            "facebook": {
                "connected": len(facebook_tokens) > 0,
                "valid_tokens": len([t for t in facebook_tokens if t.is_valid]),
                "accounts": [
                    {
                        "id": str(token.id),
                        "account_ref": token.account_ref,
                        "account_name": token.account_name,
                        "is_valid": token.is_valid,
                        "expires_at": token.expires_at.isoformat() if token.expires_at else None
                    }
                    for token in facebook_tokens
                ]
            },
            "tiktok": {
                "connected": len(tiktok_tokens) > 0,
                "valid_tokens": len([t for t in tiktok_tokens if t.is_valid]),
                "accounts": [
                    {
                        "id": str(token.id),
                        "account_ref": token.account_ref,
                        "account_name": token.account_name,
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


@router.get("/facebook/pages/{tenant_id}")
def get_facebook_pages(
    tenant_id: str,
    auth_service: AuthSvc,
    logger: LoggerDep,
    current_user: User = Depends(get_current_user)
):
    """Get Facebook pages for a tenant"""
    try:
        if str(current_user.tenant_id) != tenant_id:
            raise HTTPException(status_code=403, detail="Tenant mismatch")

        page_tokens = auth_service.get_facebook_page_tokens(
            current_user.tenant_id,
            user_id=current_user.id
        )
        return {
            "tenant_id": tenant_id,
            "pages": [{
                "id": page["page_id"],
                "name": page["page_name"],
                "token_id": page["id"],
                "category": page["meta"].get("category"),
                "tasks": page["meta"].get("tasks", [])
            } for page in page_tokens]
        }
    except Exception as e:
        logger.error(f"Failed to get Facebook pages for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve pages")


@router.post("/facebook/pages/{page_id}/post")
async def post_to_facebook_page(
    page_id: str,
    auth_service: AuthSvc,
    logger: LoggerDep,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Query(..., description="Tenant ID"),
    message: str = Query(..., description="Message to post")
):
    """Post message to Facebook page"""
    try:
        if str(current_user.tenant_id) != tenant_id:
            raise HTTPException(status_code=403, detail="Tenant mismatch")

        # Get Facebook API client for the tenant
        api_client = auth_service.get_facebook_api_client(
            current_user.tenant_id,
            user_id=current_user.id
        )
        if not api_client:
            raise HTTPException(status_code=404, detail="No Facebook token found for tenant")

        # Get page token
        page_tokens = auth_service.get_facebook_page_tokens(
            current_user.tenant_id,
            user_id=current_user.id
        )
        page_token = None
        for page in page_tokens:
            if page["page_id"] == page_id:
                page_token = page["access_token"]
                break

        if not page_token:
            raise HTTPException(status_code=404, detail="Page not found or not authorized")

        # Post to page
        result = await api_client.post_to_page(page_id, message, page_token)
        logger.info(f"Posted to Facebook page {page_id} for tenant {tenant_id}")

        return {
            "status": "success",
            "page_id": page_id,
            "post_id": result.get("id"),
            "message": message
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to post to Facebook page {page_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to post to page")


@router.post("/facebook/token/{token_id}/refresh")
async def refresh_facebook_token(
    token_id: str,
    auth_service: AuthSvc,
    logger: LoggerDep,
    current_user: User = Depends(get_current_user)
):
    """Refresh Facebook token"""
    try:
        token_uuid = UUID(token_id)
        token = auth_service.ad_token_repo.get_by_id(token_uuid)
        if not token or token.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Token not found")

        success = await auth_service.refresh_facebook_token(token_uuid, user_id=current_user.id)

        if success:
            logger.info(f"Facebook token {token_id} refreshed successfully")
            return {"status": "success", "token_id": token_id, "valid": True}
        else:
            logger.warning(f"Facebook token {token_id} refresh failed")
            return {"status": "failed", "token_id": token_id, "valid": False}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid token ID format")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not authorized to refresh this token")
    except Exception as e:
        logger.error(f"Failed to refresh Facebook token {token_id}: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")


@router.get("/facebook/insights/{page_id}")
async def get_facebook_page_insights(
    page_id: str,
    auth_service: AuthSvc,
    logger: LoggerDep,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Query(..., description="Tenant ID")
):
    """Get Facebook page insights"""
    try:
        if str(current_user.tenant_id) != tenant_id:
            raise HTTPException(status_code=403, detail="Tenant mismatch")

        # Get page token
        page_tokens = auth_service.get_facebook_page_tokens(
            current_user.tenant_id,
            user_id=current_user.id
        )
        page_token = None
        for page in page_tokens:
            if page["page_id"] == page_id:
                page_token = page["access_token"]
                break

        if not page_token:
            raise HTTPException(status_code=404, detail="Page not found or not authorized")

        # Get insights using Facebook API client
        api_client = auth_service.get_facebook_api_client(
            current_user.tenant_id,
            user_id=current_user.id
        )
        insights = await api_client.get_page_insights(page_id, page_token)

        return {
            "page_id": page_id,
            "insights": insights
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get insights for Facebook page {page_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve insights")


# TikTok-specific routes
@router.get("/tiktok/creator/{tenant_id}")
def get_tiktok_creator_info(
    tenant_id: str,
    auth_service: AuthSvc,
    logger: LoggerDep,
    current_user: User = Depends(get_current_user)
):
    """Get TikTok creator information for a tenant"""
    try:
        if str(current_user.tenant_id) != tenant_id:
            raise HTTPException(status_code=403, detail="Tenant mismatch")

        creator_info = auth_service.get_tiktok_creator_info(
            current_user.tenant_id,
            user_id=current_user.id
        )
        if not creator_info:
            raise HTTPException(status_code=404, detail="No TikTok account connected for tenant")

        return {
            "tenant_id": tenant_id,
            "creator": creator_info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get TikTok creator info for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve creator information")


@router.post("/tiktok/token/{token_id}/validate")
async def validate_tiktok_token(
    token_id: str,
    auth_service: AuthSvc,
    logger: LoggerDep,
    current_user: User = Depends(get_current_user)
):
    """Validate TikTok token"""
    try:
        token_uuid = UUID(token_id)
        token = auth_service.ad_token_repo.get_by_id(token_uuid)
        if not token or token.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Token not found")

        is_valid = await auth_service.validate_tiktok_token(token_uuid, user_id=current_user.id)

        if is_valid:
            logger.info(f"TikTok token {token_id} is valid")
            return {"status": "success", "token_id": token_id, "valid": True}
        else:
            logger.warning(f"TikTok token {token_id} is invalid")
            return {"status": "failed", "token_id": token_id, "valid": False}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid token ID format")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not authorized to validate this token")
    except Exception as e:
        logger.error(f"Failed to validate TikTok token {token_id}: {e}")
        raise HTTPException(status_code=500, detail="Token validation failed")


@router.post("/tiktok/upload")
async def upload_tiktok_video(
    auth_service: AuthSvc,
    logger: LoggerDep,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Query(..., description="Tenant ID"),
    title: str = Query(..., description="Video title"),
    video_path: str = Query(..., description="Path to video file"),
    description: str = Query("", description="Video description"),
    privacy_level: str = Query("PUBLIC_TO_EVERYONE", description="Privacy level")
):
    """Upload video to TikTok"""
    try:
        if str(current_user.tenant_id) != tenant_id:
            raise HTTPException(status_code=403, detail="Tenant mismatch")

        # Get TikTok API client for the tenant
        api_client = auth_service.get_tiktok_api_client(
            current_user.tenant_id,
            user_id=current_user.id
        )
        if not api_client:
            raise HTTPException(status_code=404, detail="No TikTok token found for tenant")

        # Upload video
        result = await api_client.upload_video(
            video_path=video_path,
            title=title,
            description=description,
            privacy_level=privacy_level
        )

        logger.info(f"Video uploaded to TikTok for tenant {tenant_id}: {result.publish_id}")

        return {
            "status": result.status,
            "publish_id": result.publish_id,
            "video_url": result.video_url,
            "error_code": result.error_code,
            "error_message": result.error_message
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload video to TikTok for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Video upload failed")


@router.get("/tiktok/video/{publish_id}/status")
async def get_tiktok_video_status(
    publish_id: str,
    auth_service: AuthSvc,
    logger: LoggerDep,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Query(..., description="Tenant ID")
):
    """Get TikTok video status"""
    try:
        if str(current_user.tenant_id) != tenant_id:
            raise HTTPException(status_code=403, detail="Tenant mismatch")

        # Get TikTok API client for the tenant
        api_client = auth_service.get_tiktok_api_client(
            current_user.tenant_id,
            user_id=current_user.id
        )
        if not api_client:
            raise HTTPException(status_code=404, detail="No TikTok token found for tenant")

        # Get video status
        status = await api_client.get_video_status(publish_id)

        return {
            "publish_id": publish_id,
            "status": status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get TikTok video status {publish_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve video status")


@router.post("/facebook/data-deletion")
@router.get("/facebook/data-deletion")
async def facebook_data_deletion(
    request: Request,
    auth_service: AuthSvc,
    settings: SettingsDep,
    logger: LoggerDep,
    signed_request: str = Form(None)
):
    """
    Facebook Data Deletion Callback URL endpoint.

    This endpoint is called by Facebook when a user requests data deletion.
    Required for Facebook App Review compliance.

    Facebook sends a POST request with a signed_request parameter containing:
    - user_id: The Facebook user ID
    - issued_at: Unix timestamp

    We must return a confirmation URL and status code.
    """
    try:
        # Handle both POST (from Facebook) and GET (for testing)
        if request.method == "GET":
            return {
                "status": "ok",
                "message": "Facebook Data Deletion endpoint is active",
                "url": f"{settings.BASE_URL}/auth/facebook/data-deletion"
            }

        if not signed_request:
            raise HTTPException(status_code=400, detail="Missing signed_request parameter")

        # Parse signed request from Facebook
        user_data = parse_signed_request(signed_request, settings.FB_APP_SECRET.get_secret_value())

        if not user_data:
            raise HTTPException(status_code=400, detail="Invalid signed_request")

        user_id = user_data.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="Missing user_id in signed_request")

        # Delete or anonymize user data from database
        deletion_result = auth_service.delete_facebook_user_data(user_id)

        logger.info(f"Facebook data deletion request processed for user {user_id}")

        # Generate a confirmation code (you can store this for tracking)
        confirmation_code = base64.urlsafe_b64encode(f"{user_id}:{deletion_result['timestamp']}".encode()).decode()

        # Return the required response format
        return JSONResponse(content={
            "url": f"{settings.BASE_URL}/auth/facebook/data-deletion-status?code={confirmation_code}",
            "confirmation_code": confirmation_code
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Facebook data deletion callback failed: {e}")
        raise HTTPException(status_code=500, detail="Data deletion request failed")


@router.get("/facebook/data-deletion-status")
async def facebook_data_deletion_status(
    logger: LoggerDep,
    code: str = Query(..., description="Confirmation code")
):
    """
    Status page for data deletion confirmation.
    Users can check their data deletion status using the confirmation code.
    """
    try:
        # Decode confirmation code
        decoded = base64.urlsafe_b64decode(code.encode()).decode()
        user_id, timestamp = decoded.split(":", 1)

        return {
            "status": "completed",
            "message": f"Data deletion request for user {user_id} has been processed",
            "timestamp": timestamp,
            "confirmation_code": code
        }
    except Exception as e:
        logger.error(f"Failed to decode confirmation code: {e}")
        raise HTTPException(status_code=400, detail="Invalid confirmation code")


def parse_signed_request(signed_request: str, app_secret: str) -> dict | None:
    """
    Parse and verify Facebook's signed_request parameter.

    Format: base64url(signature).base64url(payload)
    """
    try:
        encoded_sig, payload = signed_request.split('.', 1)

        # Decode signature
        sig = base64.urlsafe_b64decode(encoded_sig + '=' * (4 - len(encoded_sig) % 4))

        # Decode payload
        import json
        data = json.loads(base64.urlsafe_b64decode(payload + '=' * (4 - len(payload) % 4)))

        # Verify signature
        expected_sig = hmac.new(
            app_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).digest()

        if sig != expected_sig:
            return None

        return data
    except Exception:
        return None
