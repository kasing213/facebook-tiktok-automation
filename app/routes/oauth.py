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
from app.core.dependencies import get_current_user
from app.core.authorization import get_current_owner, require_owner
from app.core.exceptions import (
    OAuthInitiationFailed, OAuthStateMismatch, OAuthCodeExchangeFailed,
    TokenNotFound, TokenRefreshFailed, TokenValidationFailed, NoTokenConnected,
    PageNotFound, PostToPageFailed, InsightsRetrievalFailed, VideoUploadFailed,
    TenantMismatch, InvalidUUIDFormat, TokenOwnershipError, DatabaseError,
    InvalidSignedRequest, DataDeletionFailed, InvalidConfirmationCode
)

router = APIRouter(prefix="/auth", tags=["oauth"])


@router.get("/facebook/authorize")
def facebook_authorize(
    facebook_oauth: FacebookOAuthProvider,
    logger: LoggerDep,
    current_user: User = Depends(get_current_owner),
    tenant_id: str = Query(None, description="Tenant ID for OAuth flow")
):
    """Initiate Facebook OAuth authorization flow"""
    try:
        if tenant_id and str(current_user.tenant_id) != tenant_id:
            logger.warning(f"Facebook OAuth tenant mismatch: user {current_user.email} tried to access tenant {tenant_id}")
            raise TenantMismatch()

        auth_url = facebook_oauth.auth_url(str(current_user.tenant_id), user_id=str(current_user.id))
        logger.info(f"Facebook OAuth initiated for user {current_user.email} in tenant {current_user.tenant_id}")
        return RedirectResponse(url=auth_url)
    except TenantMismatch:
        raise
    except Exception as e:
        logger.error(f"Facebook OAuth initiation failed for user {current_user.email}: {str(e)}")
        raise OAuthInitiationFailed(platform="Facebook", reason=str(e))


@router.get("/facebook/authorize-url")
def facebook_authorize_url(
    facebook_oauth: FacebookOAuthProvider,
    logger: LoggerDep,
    current_user: User = Depends(get_current_owner),
    tenant_id: str = Query(None, description="Tenant ID for OAuth flow"),
):
    """Get Facebook OAuth authorization URL for the current user"""
    if tenant_id and str(current_user.tenant_id) != tenant_id:
        logger.warning(f"Facebook OAuth URL tenant mismatch: user {current_user.email} tried to access tenant {tenant_id}")
        raise TenantMismatch()

    auth_url = facebook_oauth.auth_url(str(current_user.tenant_id), user_id=str(current_user.id))
    logger.info(f"Facebook OAuth URL generated for user {current_user.email}")
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
    import httpx
    import traceback

    try:
        logger.info(f"Facebook OAuth callback received: code_length={len(code)}, state_length={len(state)}")

        # Validate state and extract tenant info
        try:
            state_data = await facebook_oauth.validate_state(state)
        except ValueError as ve:
            logger.error(f"Facebook OAuth state validation failed: {str(ve)}")
            raise OAuthStateMismatch(platform="Facebook")

        if not state_data:
            logger.warning("Facebook OAuth callback received with invalid state")
            raise OAuthStateMismatch(platform="Facebook")

        tenant_id = state_data.get("tenant_id")
        user_id = state_data.get("user_id")
        logger.info(f"Facebook OAuth state validated: tenant_id={tenant_id}, user_id={user_id}")

        if not tenant_id or not user_id:
            logger.warning("Facebook OAuth state missing tenant_id or user_id")
            raise OAuthStateMismatch(platform="Facebook")

        try:
            user_uuid = UUID(user_id)
            tenant_uuid = UUID(tenant_id)
        except ValueError:
            logger.error(f"Invalid UUID format in OAuth state: tenant={tenant_id}, user={user_id}")
            raise InvalidUUIDFormat(field_name="OAuth state", value=f"tenant={tenant_id}, user={user_id}")

        # Exchange code for tokens
        try:
            oauth_result = await facebook_oauth.exchange(code)
            logger.info(f"Facebook OAuth code exchange successful for user {user_id} in tenant {tenant_id}")
        except httpx.HTTPStatusError as http_err:
            error_body = http_err.response.text if http_err.response else "No response body"
            logger.error(f"Facebook API error during code exchange: status={http_err.response.status_code}, body={error_body}")
            raise OAuthCodeExchangeFailed(platform="Facebook", reason=f"Facebook API returned {http_err.response.status_code}: {error_body[:200]}")

        # Store tokens securely (including page tokens)
        try:
            token = auth_service.store_oauth_token(tenant_uuid, oauth_result, user_id=user_uuid)
            logger.info(f"Facebook OAuth token stored: token_id={token.id}")
        except Exception as db_err:
            logger.error(f"Database error storing OAuth token: {str(db_err)}\n{traceback.format_exc()}")
            raise OAuthCodeExchangeFailed(platform="Facebook", reason=f"Failed to store token: {str(db_err)}")

        # Get page tokens for response
        page_tokens = auth_service.get_facebook_page_tokens(tenant_uuid, user_id=user_uuid)

        logger.info(f"Facebook OAuth completed: stored token {token.id}, found {len(page_tokens)} pages")

        # Redirect to frontend dashboard with success message
        frontend_base = str(settings.FRONTEND_URL).rstrip("/")
        frontend_query = urlencode({"success": "facebook", "tenant_id": tenant_id})
        frontend_url = f"{frontend_base}/dashboard?{frontend_query}"
        return RedirectResponse(url=frontend_url)

    except (OAuthStateMismatch, InvalidUUIDFormat, OAuthCodeExchangeFailed):
        raise
    except httpx.HTTPStatusError as http_err:
        error_body = http_err.response.text if http_err.response else "No response body"
        logger.error(f"Facebook API HTTP error: status={http_err.response.status_code}, body={error_body}")
        raise OAuthCodeExchangeFailed(platform="Facebook", reason=f"Facebook API error: {error_body[:200]}")
    except Exception as e:
        logger.error(f"Facebook OAuth callback failed: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}")
        raise OAuthCodeExchangeFailed(platform="Facebook", reason=str(e))


@router.get("/tiktok/authorize")
def tiktok_authorize(
    tiktok_oauth: TikTokOAuthProvider,
    logger: LoggerDep,
    current_user: User = Depends(get_current_owner),
    tenant_id: str = Query(None, description="Tenant ID for OAuth flow")
):
    """Initiate TikTok OAuth authorization flow"""
    try:
        if tenant_id and str(current_user.tenant_id) != tenant_id:
            logger.warning(f"TikTok OAuth tenant mismatch: user {current_user.email} tried to access tenant {tenant_id}")
            raise TenantMismatch()

        auth_url = tiktok_oauth.auth_url(str(current_user.tenant_id), user_id=str(current_user.id))
        logger.info(f"TikTok OAuth initiated for user {current_user.email} in tenant {current_user.tenant_id}")
        return RedirectResponse(url=auth_url)
    except TenantMismatch:
        raise
    except Exception as e:
        logger.error(f"TikTok OAuth initiation failed for user {current_user.email}: {str(e)}")
        raise OAuthInitiationFailed(platform="TikTok", reason=str(e))


@router.get("/tiktok/authorize-url")
def tiktok_authorize_url(
    tiktok_oauth: TikTokOAuthProvider,
    logger: LoggerDep,
    current_user: User = Depends(get_current_owner),
    tenant_id: str = Query(None, description="Tenant ID for OAuth flow"),
):
    """Get TikTok OAuth authorization URL for the current user"""
    if tenant_id and str(current_user.tenant_id) != tenant_id:
        logger.warning(f"TikTok OAuth URL tenant mismatch: user {current_user.email} tried to access tenant {tenant_id}")
        raise TenantMismatch()

    auth_url = tiktok_oauth.auth_url(str(current_user.tenant_id), user_id=str(current_user.id))
    logger.info(f"TikTok OAuth URL generated for user {current_user.email}")
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
        if not state_data:
            logger.warning("TikTok OAuth callback received with invalid state")
            raise OAuthStateMismatch(platform="TikTok")

        tenant_id = state_data.get("tenant_id")
        code_verifier = state_data.get("code_verifier")
        user_id = state_data.get("user_id")

        if not code_verifier:
            logger.error("TikTok OAuth state missing PKCE code verifier")
            raise OAuthStateMismatch(platform="TikTok")

        if not tenant_id or not user_id:
            logger.warning("TikTok OAuth state missing tenant_id or user_id")
            raise OAuthStateMismatch(platform="TikTok")

        try:
            user_uuid = UUID(user_id)
            tenant_uuid = UUID(tenant_id)
        except ValueError:
            logger.error(f"Invalid UUID format in TikTok OAuth state: tenant={tenant_id}, user={user_id}")
            raise InvalidUUIDFormat(field_name="OAuth state", value=f"tenant={tenant_id}, user={user_id}")

        # Exchange code for tokens
        oauth_result = await tiktok_oauth.exchange(code, code_verifier=code_verifier)
        logger.info(f"TikTok OAuth code exchange successful for user {user_id} in tenant {tenant_id}")

        # Store tokens securely (including user info)
        token = auth_service.store_oauth_token(tenant_uuid, oauth_result, user_id=user_uuid)

        # Get creator info for response
        creator_info = auth_service.get_tiktok_creator_info(tenant_uuid, user_id=user_uuid)

        logger.info(f"TikTok OAuth completed: stored token {token.id}, creator: {creator_info.get('display_name', 'unknown') if creator_info else 'none'}")

        # Redirect to frontend dashboard with success message
        frontend_base = str(settings.FRONTEND_URL).rstrip("/")
        frontend_query = urlencode({"success": "tiktok", "tenant_id": tenant_id})
        frontend_url = f"{frontend_base}/dashboard?{frontend_query}"
        return RedirectResponse(url=frontend_url)

    except (OAuthStateMismatch, InvalidUUIDFormat):
        raise
    except Exception as e:
        logger.error(f"TikTok OAuth callback failed: {str(e)}")
        raise OAuthCodeExchangeFailed(platform="TikTok", reason=str(e))


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
            logger.warning(f"OAuth status tenant mismatch: user {current_user.email} tried to access tenant {tenant_id}")
            raise TenantMismatch()

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

        logger.info(f"OAuth status retrieved for user {current_user.email}: {len(facebook_tokens)} Facebook, {len(tiktok_tokens)} TikTok tokens")

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

    except TenantMismatch:
        raise
    except Exception as e:
        logger.error(f"OAuth status check failed for user {current_user.email}: {str(e)}")
        raise DatabaseError(operation="retrieve OAuth connection status")


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
            logger.warning(f"Facebook pages tenant mismatch: user {current_user.email} tried to access tenant {tenant_id}")
            raise TenantMismatch()

        page_tokens = auth_service.get_facebook_page_tokens(
            current_user.tenant_id,
            user_id=current_user.id
        )

        logger.info(f"Retrieved {len(page_tokens)} Facebook pages for user {current_user.email}")

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
    except TenantMismatch:
        raise
    except Exception as e:
        logger.error(f"Failed to get Facebook pages for user {current_user.email}: {str(e)}")
        raise DatabaseError(operation="retrieve your Facebook pages")


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
            logger.warning(f"Facebook post tenant mismatch: user {current_user.email} tried to access tenant {tenant_id}")
            raise TenantMismatch()

        # Get Facebook API client for the tenant
        api_client = auth_service.get_facebook_api_client(
            current_user.tenant_id,
            user_id=current_user.id
        )
        if not api_client:
            logger.warning(f"No Facebook token found for user {current_user.email}")
            raise NoTokenConnected(platform="Facebook", tenant_id=tenant_id)

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
            logger.warning(f"Page {page_id} not found for user {current_user.email}")
            raise PageNotFound(page_id=page_id)

        # Post to page
        result = await api_client.post_to_page(page_id, message, page_token)
        logger.info(f"Successfully posted to Facebook page {page_id} for user {current_user.email}")

        return {
            "status": "success",
            "message": "Your post has been published successfully.",
            "page_id": page_id,
            "post_id": result.get("id"),
            "content": message
        }

    except (TenantMismatch, NoTokenConnected, PageNotFound):
        raise
    except Exception as e:
        logger.error(f"Failed to post to Facebook page {page_id} for user {current_user.email}: {str(e)}")
        raise PostToPageFailed(page_id=page_id, reason=str(e))


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
    except ValueError:
        logger.warning(f"Invalid token ID format: {token_id} by user {current_user.email}")
        raise InvalidUUIDFormat(field_name="token ID", value=token_id)

    try:
        token = auth_service.ad_token_repo.get_by_id(token_uuid)
        if not token:
            logger.warning(f"Facebook token {token_id} not found for user {current_user.email}")
            raise TokenNotFound(token_id=token_id, platform="Facebook")

        if token.user_id != current_user.id:
            logger.warning(f"User {current_user.email} tried to refresh token {token_id} owned by another user")
            raise TokenOwnershipError(token_id=token_id)

        success = await auth_service.refresh_facebook_token(token_uuid, user_id=current_user.id)

        if success:
            logger.info(f"Facebook token {token_id} refreshed successfully for user {current_user.email}")
            return {
                "status": "success",
                "message": "Your Facebook connection has been refreshed successfully.",
                "token_id": token_id,
                "valid": True
            }
        else:
            logger.warning(f"Facebook token {token_id} refresh failed for user {current_user.email}")
            raise TokenRefreshFailed(platform="Facebook", reason="The token could not be refreshed")

    except (InvalidUUIDFormat, TokenNotFound, TokenOwnershipError, TokenRefreshFailed):
        raise
    except Exception as e:
        logger.error(f"Failed to refresh Facebook token {token_id} for user {current_user.email}: {str(e)}")
        raise TokenRefreshFailed(platform="Facebook", reason=str(e))


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
            logger.warning(f"Facebook insights tenant mismatch: user {current_user.email} tried to access tenant {tenant_id}")
            raise TenantMismatch()

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
            logger.warning(f"Page {page_id} not found for insights request by user {current_user.email}")
            raise PageNotFound(page_id=page_id)

        # Get insights using Facebook API client
        api_client = auth_service.get_facebook_api_client(
            current_user.tenant_id,
            user_id=current_user.id
        )
        insights = await api_client.get_page_insights(page_id, page_token)

        logger.info(f"Retrieved insights for Facebook page {page_id} for user {current_user.email}")

        return {
            "page_id": page_id,
            "insights": insights
        }

    except (TenantMismatch, PageNotFound):
        raise
    except Exception as e:
        logger.error(f"Failed to get insights for Facebook page {page_id} for user {current_user.email}: {str(e)}")
        raise InsightsRetrievalFailed(page_id=page_id, reason=str(e))


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
            logger.warning(f"TikTok creator info tenant mismatch: user {current_user.email} tried to access tenant {tenant_id}")
            raise TenantMismatch()

        creator_info = auth_service.get_tiktok_creator_info(
            current_user.tenant_id,
            user_id=current_user.id
        )
        if not creator_info:
            logger.info(f"No TikTok account connected for user {current_user.email}")
            raise NoTokenConnected(platform="TikTok", tenant_id=tenant_id)

        logger.info(f"Retrieved TikTok creator info for user {current_user.email}")

        return {
            "tenant_id": tenant_id,
            "creator": creator_info
        }
    except (TenantMismatch, NoTokenConnected):
        raise
    except Exception as e:
        logger.error(f"Failed to get TikTok creator info for user {current_user.email}: {str(e)}")
        raise DatabaseError(operation="retrieve your TikTok creator information")


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
    except ValueError:
        logger.warning(f"Invalid token ID format: {token_id} by user {current_user.email}")
        raise InvalidUUIDFormat(field_name="token ID", value=token_id)

    try:
        token = auth_service.ad_token_repo.get_by_id(token_uuid)
        if not token:
            logger.warning(f"TikTok token {token_id} not found for user {current_user.email}")
            raise TokenNotFound(token_id=token_id, platform="TikTok")

        if token.user_id != current_user.id:
            logger.warning(f"User {current_user.email} tried to validate token {token_id} owned by another user")
            raise TokenOwnershipError(token_id=token_id)

        is_valid = await auth_service.validate_tiktok_token(token_uuid, user_id=current_user.id)

        if is_valid:
            logger.info(f"TikTok token {token_id} validated successfully for user {current_user.email}")
            return {
                "status": "success",
                "message": "Your TikTok connection is valid and working.",
                "token_id": token_id,
                "valid": True
            }
        else:
            logger.warning(f"TikTok token {token_id} is invalid for user {current_user.email}")
            return {
                "status": "invalid",
                "message": "Your TikTok connection is no longer valid. Please reconnect your account.",
                "token_id": token_id,
                "valid": False
            }

    except (InvalidUUIDFormat, TokenNotFound, TokenOwnershipError):
        raise
    except Exception as e:
        logger.error(f"Failed to validate TikTok token {token_id} for user {current_user.email}: {str(e)}")
        raise TokenValidationFailed(platform="TikTok", reason=str(e))


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
            logger.warning(f"TikTok upload tenant mismatch: user {current_user.email} tried to access tenant {tenant_id}")
            raise TenantMismatch()

        # Get TikTok API client for the tenant
        api_client = auth_service.get_tiktok_api_client(
            current_user.tenant_id,
            user_id=current_user.id
        )
        if not api_client:
            logger.warning(f"No TikTok token found for user {current_user.email}")
            raise NoTokenConnected(platform="TikTok", tenant_id=tenant_id)

        # Upload video
        result = await api_client.upload_video(
            video_path=video_path,
            title=title,
            description=description,
            privacy_level=privacy_level
        )

        logger.info(f"Video uploaded to TikTok for user {current_user.email}: publish_id={result.publish_id}")

        return {
            "status": result.status,
            "message": "Your video has been submitted for publishing.",
            "publish_id": result.publish_id,
            "video_url": result.video_url,
            "error_code": result.error_code,
            "error_message": result.error_message
        }

    except (TenantMismatch, NoTokenConnected):
        raise
    except Exception as e:
        logger.error(f"Failed to upload video to TikTok for user {current_user.email}: {str(e)}")
        raise VideoUploadFailed(reason=str(e))


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
            logger.warning(f"TikTok video status tenant mismatch: user {current_user.email} tried to access tenant {tenant_id}")
            raise TenantMismatch()

        # Get TikTok API client for the tenant
        api_client = auth_service.get_tiktok_api_client(
            current_user.tenant_id,
            user_id=current_user.id
        )
        if not api_client:
            logger.warning(f"No TikTok token found for user {current_user.email}")
            raise NoTokenConnected(platform="TikTok", tenant_id=tenant_id)

        # Get video status
        status = await api_client.get_video_status(publish_id)

        logger.info(f"Retrieved TikTok video status for publish_id={publish_id} for user {current_user.email}")

        return {
            "publish_id": publish_id,
            "status": status
        }

    except (TenantMismatch, NoTokenConnected):
        raise
    except Exception as e:
        logger.error(f"Failed to get TikTok video status {publish_id} for user {current_user.email}: {str(e)}")
        raise DatabaseError(operation="retrieve your video status")


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
            logger.info("Facebook data deletion endpoint health check")
            return {
                "status": "ok",
                "message": "Facebook Data Deletion endpoint is active and ready to process requests.",
                "url": f"{settings.BASE_URL}/auth/facebook/data-deletion"
            }

        if not signed_request:
            logger.warning("Facebook data deletion request missing signed_request parameter")
            raise InvalidSignedRequest()

        # Parse signed request from Facebook
        user_data = parse_signed_request(signed_request, settings.FB_APP_SECRET.get_secret_value())

        if not user_data:
            logger.warning("Facebook data deletion request has invalid signed_request")
            raise InvalidSignedRequest()

        user_id = user_data.get("user_id")
        if not user_id:
            logger.warning("Facebook data deletion request missing user_id")
            raise InvalidSignedRequest()

        # Delete or anonymize user data from database
        deletion_result = auth_service.delete_facebook_user_data(user_id)

        logger.info(f"Facebook data deletion request processed successfully for Facebook user {user_id}")

        # Generate a confirmation code (you can store this for tracking)
        confirmation_code = base64.urlsafe_b64encode(f"{user_id}:{deletion_result['timestamp']}".encode()).decode()

        # Return the required response format
        return JSONResponse(content={
            "url": f"{settings.BASE_URL}/auth/facebook/data-deletion-status?code={confirmation_code}",
            "confirmation_code": confirmation_code
        })

    except InvalidSignedRequest:
        raise
    except Exception as e:
        logger.error(f"Facebook data deletion callback failed: {str(e)}")
        raise DataDeletionFailed(user_id=user_id if 'user_id' in dir() else "unknown")


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


@router.get("/debug/state-store")
async def debug_state_store(
    facebook_oauth: FacebookOAuthProvider,
    logger: LoggerDep,
    settings: SettingsDep
):
    """
    Debug endpoint to check OAuth state store health.
    Only enabled in non-production environments.
    """
    if settings.ENV == "production":
        raise HTTPException(status_code=404, detail="Not found")

    logger.info("Debug state store endpoint accessed")
    state_store = facebook_oauth.state_store
    store_type = type(state_store).__name__

    # Check Redis connection if using Redis
    redis_status = "not_configured"
    if settings.REDIS_URL:
        try:
            from app.integrations.oauth import RedisState
            if RedisState and isinstance(state_store, RedisState):
                # Test Redis connection
                test_key = "debug_test"
                await state_store.put(test_key, "test_value", 10)
                result = await state_store.get(test_key)
                redis_status = "connected" if result == "test_value" else "error"
            else:
                redis_status = "redis_unavailable_using_memory"
        except Exception as e:
            redis_status = f"error: {str(e)}"
    else:
        redis_status = "not_configured_using_memory"

    return {
        "state_store_type": store_type,
        "redis_url_configured": bool(settings.REDIS_URL),
        "redis_status": redis_status,
        "base_url": facebook_oauth.base_url,
        "fb_app_id_configured": bool(settings.FB_APP_ID),
        "environment": settings.ENV
    }
