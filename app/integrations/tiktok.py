# app/integrations/tiktok.py
"""
TikTok API client for content posting and account management.

Handles:
- Video uploads and publishing
- User profile information
- Content management
- Multi-tenant token management
"""
import httpx
import json
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

from app.core.config import get_settings
from app.core.crypto import load_encryptor


@dataclass
class TikTokVideoUploadResult:
    """Result of a TikTok video upload operation"""
    publish_id: str
    status: str
    video_url: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class TikTokUserInfo:
    """TikTok user profile information"""
    open_id: str
    union_id: str
    username: str
    display_name: str
    avatar_url: Optional[str] = None
    follower_count: Optional[int] = None
    following_count: Optional[int] = None
    likes_count: Optional[int] = None
    video_count: Optional[int] = None


class TikTokAPIError(Exception):
    """TikTok API specific errors"""
    def __init__(self, message: str, error_code: str = None, status_code: int = None):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(message)


class TikTokAPIClient:
    """
    TikTok API client for content creation and account management.

    Supports:
    - Video uploads with various privacy settings
    - User profile retrieval
    - Content posting with captions and hashtags
    - Multi-tenant token management
    """

    BASE_URL = "https://open.tiktokapis.com"
    CREATOR_BASE_URL = "https://open.tiktokapis.com/v2/post"

    def __init__(self, access_token: str, settings=None):
        self.access_token = access_token
        self.settings = settings or get_settings()
        self.encryptor = load_encryptor()

    async def _make_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str] = None,
        data: Any = None,
        files: Dict[str, Any] = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """Make authenticated request to TikTok API"""
        default_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        if headers:
            default_headers.update(headers)

        # Remove Content-Type for file uploads
        if files and "Content-Type" in default_headers:
            del default_headers["Content-Type"]

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=default_headers, params=data)
                elif method.upper() == "POST":
                    if files:
                        response = await client.post(url, headers=default_headers, data=data, files=files)
                    else:
                        response = await client.post(url, headers=default_headers, json=data)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=default_headers, json=data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                try:
                    error_data = e.response.json()
                    error_code = error_data.get("error", {}).get("code", "unknown")
                    error_message = error_data.get("error", {}).get("message", str(e))
                except:
                    error_code = "http_error"
                    error_message = str(e)

                raise TikTokAPIError(
                    message=f"TikTok API error: {error_message}",
                    error_code=error_code,
                    status_code=e.response.status_code
                )
            except httpx.RequestError as e:
                raise TikTokAPIError(f"Request error: {str(e)}")

    async def get_user_info(self, fields: List[str] = None) -> TikTokUserInfo:
        """
        Get user profile information.

        Args:
            fields: List of fields to retrieve. If None, gets basic fields.
                   Available: open_id, union_id, username, display_name, avatar_url,
                            follower_count, following_count, likes_count, video_count
        """
        if fields is None:
            fields = ["open_id", "union_id", "username", "display_name", "avatar_url"]

        url = f"{self.BASE_URL}/v2/user/info/"
        params = {"fields": ",".join(fields)}

        response = await self._make_request("GET", url, data=params)

        user_data = response.get("data", {}).get("user", {})

        return TikTokUserInfo(
            open_id=user_data.get("open_id"),
            union_id=user_data.get("union_id"),
            username=user_data.get("username"),
            display_name=user_data.get("display_name"),
            avatar_url=user_data.get("avatar_url"),
            follower_count=user_data.get("follower_count"),
            following_count=user_data.get("following_count"),
            likes_count=user_data.get("likes_count"),
            video_count=user_data.get("video_count")
        )

    async def upload_video(
        self,
        video_path: str,
        title: str,
        description: str = "",
        privacy_level: str = "PUBLIC_TO_EVERYONE",
        disable_duet: bool = False,
        disable_comment: bool = False,
        disable_stitch: bool = False,
        brand_content_toggle: bool = False,
        brand_organic_toggle: bool = False
    ) -> TikTokVideoUploadResult:
        """
        Upload a video to TikTok.

        Args:
            video_path: Path to the video file
            title: Video title/caption
            description: Additional description
            privacy_level: "PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIENDS", or "SELF_ONLY"
            disable_duet: Whether to disable duet for this video
            disable_comment: Whether to disable comments
            disable_stitch: Whether to disable stitch
            brand_content_toggle: Mark as brand content
            brand_organic_toggle: Mark as brand organic content
        """

        # Step 1: Initialize upload
        post_info = {
            "title": title,
            "privacy_level": privacy_level,
            "disable_duet": disable_duet,
            "disable_comment": disable_comment,
            "disable_stitch": disable_stitch,
            "brand_content_toggle": brand_content_toggle,
            "brand_organic_toggle": brand_organic_toggle
        }

        if description:
            post_info["description"] = description

        init_url = f"{self.CREATOR_BASE_URL}/video/init/"
        init_response = await self._make_request("POST", init_url, data={"post_info": post_info})

        upload_url = init_response.get("data", {}).get("upload_url")
        publish_id = init_response.get("data", {}).get("publish_id")

        if not upload_url or not publish_id:
            raise TikTokAPIError("Failed to initialize video upload")

        # Step 2: Upload video file
        try:
            with open(video_path, "rb") as video_file:
                files = {"video": video_file}

                # Upload to the provided URL (different from API base)
                async with httpx.AsyncClient(timeout=300) as client:  # 5 minute timeout for upload
                    upload_response = await client.put(upload_url, files=files)
                    upload_response.raise_for_status()

        except Exception as e:
            raise TikTokAPIError(f"Video upload failed: {str(e)}")

        # Step 3: Publish the video
        publish_url = f"{self.CREATOR_BASE_URL}/video/publish/"
        publish_data = {"post_id": publish_id}

        try:
            publish_response = await self._make_request("POST", publish_url, data=publish_data)

            return TikTokVideoUploadResult(
                publish_id=publish_id,
                status="success",
                video_url=None  # TikTok doesn't return video URL immediately
            )

        except TikTokAPIError as e:
            return TikTokVideoUploadResult(
                publish_id=publish_id,
                status="failed",
                error_code=e.error_code,
                error_message=e.message
            )

    async def get_video_status(self, publish_id: str) -> Dict[str, Any]:
        """Check the status of a published video"""
        url = f"{self.CREATOR_BASE_URL}/video/query/"
        params = {"filters": json.dumps({"publish_ids": [publish_id]})}

        response = await self._make_request("POST", url, data=params)

        videos = response.get("data", {}).get("videos", [])
        if videos:
            return videos[0]
        return {}

    async def get_creator_info(self) -> Dict[str, Any]:
        """Get creator account information and capabilities"""
        url = f"{self.BASE_URL}/v2/research/creator_info/"

        response = await self._make_request("GET", url)
        return response.get("data", {})

    async def validate_token(self) -> bool:
        """Validate if the current access token is still valid"""
        try:
            await self.get_user_info(fields=["open_id"])
            return True
        except TikTokAPIError:
            return False


class TikTokService:
    """
    Service layer for TikTok integration with multi-tenant support.

    Handles token management and provides high-level operations.
    """

    def __init__(self, db_session=None):
        self.db = db_session
        self.settings = get_settings()
        self.encryptor = load_encryptor()

    def get_client_for_tenant(self, tenant_id: str, account_ref: str = None) -> Optional[TikTokAPIClient]:
        """
        Get TikTok API client for a specific tenant.

        Args:
            tenant_id: Tenant UUID
            account_ref: Optional specific account reference (open_id)
        """
        if not self.db:
            raise ValueError("Database session required for tenant operations")

        from app.repositories.ad_token import AdTokenRepository
        from app.core.models import Platform
        from uuid import UUID

        token_repo = AdTokenRepository(self.db)
        token = token_repo.get_active_token(UUID(tenant_id), Platform.tiktok, account_ref)

        if not token or not token.is_valid:
            return None

        try:
            access_token = self.encryptor.dec(token.access_token_enc)
            return TikTokAPIClient(access_token, self.settings)
        except Exception:
            # Mark token as invalid if decryption fails
            token_repo.invalidate_token(token.id)
            self.db.commit()
            return None

    async def refresh_token_if_needed(self, tenant_id: str, account_ref: str = None) -> bool:
        """
        Refresh token if it's about to expire.

        Returns True if refresh was successful or not needed, False if refresh failed.
        """
        if not self.db:
            return False

        from app.repositories.ad_token import AdTokenRepository
        from app.core.models import Platform
        from uuid import UUID
        from datetime import datetime, timedelta

        token_repo = AdTokenRepository(self.db)
        token = token_repo.get_active_token(UUID(tenant_id), Platform.tiktok, account_ref)

        if not token or not token.refresh_token_enc:
            return False

        # Check if token expires within next 2 hours
        if token.expires_at and token.expires_at <= datetime.utcnow() + timedelta(hours=2):
            try:
                refresh_token = self.encryptor.dec(token.refresh_token_enc)

                form_data = {
                    "client_key": self.settings.TIKTOK_CLIENT_KEY,
                    "client_secret": self.settings.TIKTOK_CLIENT_SECRET.get_secret_value(),
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                }

                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.post(
                        "https://open.tiktokapis.com/v2/oauth/token/",
                        data=form_data,
                        headers={"Content-Type": "application/x-www-form-urlencoded"}
                    )
                    response.raise_for_status()
                    token_data = response.json()

                # Update token
                new_access_token = self.encryptor.enc(token_data["access_token"])
                new_refresh_token = None
                if token_data.get("refresh_token"):
                    new_refresh_token = self.encryptor.enc(token_data["refresh_token"])

                new_expires_at = datetime.utcnow() + timedelta(seconds=int(token_data.get("expires_in", 0)))

                token_repo.update(
                    token.id,
                    access_token_enc=new_access_token,
                    refresh_token_enc=new_refresh_token,
                    expires_at=new_expires_at,
                    scope=token_data.get("scope", token.scope),
                    is_valid=True
                )
                self.db.commit()
                return True

            except Exception:
                # Mark token as invalid if refresh fails
                token_repo.invalidate_token(token.id)
                self.db.commit()
                return False

        return True  # No refresh needed