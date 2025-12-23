# app/services/auth_service.py
from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.models import AdToken, Platform, User
from app.repositories import AdTokenRepository, UserRepository
from app.core.crypto import TokenEncryptor
from app.integrations.oauth import OAuthResult, FacebookAPIClient


class AuthService:
    """Service layer for authentication and token management"""

    def __init__(self, db: Session, encryptor: TokenEncryptor):
        self.db = db
        self.ad_token_repo = AdTokenRepository(db)
        self.user_repo = UserRepository(db)
        self.encryptor = encryptor

    def store_oauth_token(
        self,
        tenant_id: UUID,
        oauth_result: OAuthResult,
        user_id: Optional[UUID] = None
    ) -> AdToken:
        """Store OAuth token with encryption and handle platform-specific data"""
        encrypted_access_token = self.encryptor.enc(oauth_result.access_token)
        encrypted_refresh_token = None
        if oauth_result.refresh_token:
            encrypted_refresh_token = self.encryptor.enc(oauth_result.refresh_token)

        # Extract account name from platform-specific data
        account_name = None
        if oauth_result.platform == Platform.facebook and oauth_result.raw.get("user"):
            account_name = oauth_result.raw["user"].get("name")
        elif oauth_result.platform == Platform.tiktok and oauth_result.raw.get("user"):
            account_name = oauth_result.raw["user"].get("display_name") or oauth_result.raw["user"].get("username")

        # Check if token already exists for this platform/account
        existing_token = None
        if oauth_result.account_ref:
            existing_token = self.ad_token_repo.get_active_token(
                tenant_id, oauth_result.platform, oauth_result.account_ref, user_id=user_id
            )

        if existing_token:
            # Update existing token
            token = self.ad_token_repo.update(
                existing_token.id,
                access_token_enc=encrypted_access_token,
                refresh_token_enc=encrypted_refresh_token,
                account_name=account_name,
                scope=oauth_result.scope,
                expires_at=oauth_result.expires_at,
                is_valid=True,
                meta=oauth_result.raw
            )
        else:
            # Create new token
            token = self.ad_token_repo.create_token(
                tenant_id=tenant_id,
                user_id=user_id,
                platform=oauth_result.platform,
                access_token_enc=encrypted_access_token,
                account_ref=oauth_result.account_ref,
                account_name=account_name,
                refresh_token_enc=encrypted_refresh_token,
                scope=oauth_result.scope,
                expires_at=oauth_result.expires_at,
                meta=oauth_result.raw
            )

        # Store Facebook page tokens as separate entries
        if oauth_result.platform == Platform.facebook and oauth_result.raw.get("pages"):
            self._store_facebook_page_tokens(tenant_id, oauth_result.raw["pages"], user_id=user_id)

        self.db.commit()
        return token

    def _store_facebook_page_tokens(
        self,
        tenant_id: UUID,
        pages: list,
        user_id: Optional[UUID] = None
    ) -> None:
        """Store Facebook page tokens as separate AdToken entries"""
        for page in pages:
            if not page.get("access_token"):
                continue

            encrypted_page_token = self.encryptor.enc(page["access_token"])
            page_id = page.get("id")
            page_name = page.get("name")

            # Check if page token already exists
            existing_page_token = self.ad_token_repo.get_active_token(
                tenant_id, Platform.facebook, f"page_{page_id}", user_id=user_id
            )

            if existing_page_token:
                # Update existing page token
                self.ad_token_repo.update(
                    existing_page_token.id,
                    access_token_enc=encrypted_page_token,
                    account_name=page_name,
                    is_valid=True,
                    meta=page
                )
            else:
                # Create new page token
                self.ad_token_repo.create_token(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    platform=Platform.facebook,
                    access_token_enc=encrypted_page_token,
                    account_ref=f"page_{page_id}",
                    account_name=page_name,
                    scope="pages_manage_posts,pages_read_engagement",
                    expires_at=None,  # Page tokens don't expire unless revoked
                    meta=page
                )

    def get_decrypted_token(
        self,
        tenant_id: UUID,
        platform: Platform,
        account_ref: str = None,
        user_id: Optional[UUID] = None
    ) -> Optional[str]:
        """Get decrypted access token for a platform"""
        token = self.ad_token_repo.get_active_token(tenant_id, platform, account_ref, user_id=user_id)
        if token and token.is_valid:
            try:
                return self.encryptor.dec(token.access_token_enc)
            except Exception:
                # Token decryption failed, mark as invalid
                self.ad_token_repo.invalidate_token(token.id)
                self.db.commit()
        return None

    def validate_token(self, token_id: UUID, is_valid: bool = True) -> Optional[AdToken]:
        """Update token validation status"""
        token = self.ad_token_repo.update_validation(token_id, is_valid)
        if token:
            self.db.commit()
        return token

    def get_expiring_tokens(self, hours_ahead: int = 24) -> list[AdToken]:
        """Get tokens that will expire soon"""
        return self.ad_token_repo.get_expiring_tokens(hours_ahead)

    def get_tenant_tokens(
        self,
        tenant_id: UUID,
        platform: Platform = None,
        user_id: Optional[UUID] = None
    ) -> list[AdToken]:
        """Get all tokens for a tenant, optionally filtered by platform"""
        if platform:
            return self.ad_token_repo.get_by_platform(tenant_id, platform, user_id=user_id)
        return self.ad_token_repo.get_tenant_tokens(tenant_id, user_id=user_id)

    def authenticate_user(self, tenant_id: UUID, telegram_user_id: str) -> Optional[User]:
        """Authenticate a user and update last login"""
        user = self.user_repo.get_by_telegram_id(tenant_id, telegram_user_id)
        if user and user.is_active:
            self.user_repo.update_last_login(user.id)
            self.db.commit()
        return user

    def get_or_create_user(
        self,
        tenant_id: UUID,
        telegram_user_id: str,
        username: str = None
    ) -> User:
        """Get existing user or create new one"""
        user = self.user_repo.get_by_telegram_id(tenant_id, telegram_user_id)
        if not user:
            user = self.user_repo.create_user(
                tenant_id=tenant_id,
                telegram_user_id=telegram_user_id,
                username=username
            )
            self.db.commit()
        return user

    def get_facebook_api_client(
        self,
        tenant_id: UUID,
        account_ref: str = None,
        user_id: Optional[UUID] = None
    ) -> Optional[FacebookAPIClient]:
        """Get Facebook API client with decrypted token"""
        token = self.get_decrypted_token(tenant_id, Platform.facebook, account_ref, user_id=user_id)
        if token:
            return FacebookAPIClient(token)
        return None

    def get_facebook_page_tokens(
        self,
        tenant_id: UUID,
        user_id: Optional[UUID] = None
    ) -> list[dict]:
        """Get all Facebook page tokens for a tenant"""
        tokens = self.ad_token_repo.get_by_platform(tenant_id, Platform.facebook, user_id=user_id)
        page_tokens = []

        for token in tokens:
            if token.account_ref and token.account_ref.startswith("page_") and token.is_valid:
                try:
                    decrypted_token = self.encryptor.dec(token.access_token_enc)
                    page_tokens.append({
                        "id": str(token.id),
                        "page_id": token.account_ref.replace("page_", ""),
                        "page_name": token.account_name,
                        "access_token": decrypted_token,
                        "meta": token.meta
                    })
                except Exception:
                    # Token decryption failed, mark as invalid
                    self.ad_token_repo.invalidate_token(token.id)
                    self.db.commit()

        return page_tokens

    async def refresh_facebook_token(self, token_id: UUID) -> bool:
        """Attempt to refresh Facebook token (limited refresh capabilities)"""
        token = self.ad_token_repo.get_by_id(token_id)
        if not token or token.platform != Platform.facebook:
            return False

        try:
            # Facebook doesn't provide refresh tokens, so we validate the existing token
            decrypted_token = self.encryptor.dec(token.access_token_enc)

            # Use Facebook API to validate token
            from app.integrations.oauth import FacebookOAuth
            from app.core.config import get_settings

            fb_oauth = FacebookOAuth(get_settings())
            validation_result = await fb_oauth.validate_token(decrypted_token)

            if validation_result["valid"]:
                # Token is still valid, update validation timestamp
                self.ad_token_repo.update_validation(token_id, True)
                self.db.commit()
                return True
            else:
                # Token is invalid, mark it
                self.ad_token_repo.invalidate_token(token_id)
                self.db.commit()
                return False

        except Exception:
            # Any error means token is invalid
            self.ad_token_repo.invalidate_token(token_id)
            self.db.commit()
            return False

    def get_tiktok_api_client(
        self,
        tenant_id: UUID,
        account_ref: str = None,
        user_id: Optional[UUID] = None
    ):
        """Get TikTok API client with decrypted token"""
        from app.integrations.tiktok import TikTokAPIClient

        token = self.get_decrypted_token(tenant_id, Platform.tiktok, account_ref, user_id=user_id)
        if token:
            return TikTokAPIClient(token)
        return None

    def get_tiktok_creator_info(
        self,
        tenant_id: UUID,
        account_ref: str = None,
        user_id: Optional[UUID] = None
    ) -> dict:
        """Get TikTok creator information for a tenant"""
        tokens = self.ad_token_repo.get_by_platform(tenant_id, Platform.tiktok, user_id=user_id)

        for token in tokens:
            if (not account_ref or token.account_ref == account_ref) and token.is_valid:
                user_info = token.meta.get("user", {}) if token.meta else {}
                return {
                    "id": str(token.id),
                    "open_id": token.account_ref,
                    "username": user_info.get("username"),
                    "display_name": user_info.get("display_name"),
                    "avatar_url": user_info.get("avatar_url"),
                    "follower_count": user_info.get("follower_count"),
                    "following_count": user_info.get("following_count"),
                    "likes_count": user_info.get("likes_count"),
                    "video_count": user_info.get("video_count"),
                    "expires_at": token.expires_at.isoformat() if token.expires_at else None,
                    "meta": user_info
                }
        return {}

    async def validate_tiktok_token(self, token_id: UUID) -> bool:
        """Validate TikTok token by making an API call"""
        token = self.ad_token_repo.get_by_id(token_id)
        if not token or token.platform != Platform.tiktok:
            return False

        try:
            from app.integrations.tiktok import TikTokAPIClient

            decrypted_token = self.encryptor.dec(token.access_token_enc)
            client = TikTokAPIClient(decrypted_token)

            is_valid = await client.validate_token()

            if is_valid:
                self.ad_token_repo.update_validation(token_id, True)
                self.db.commit()
                return True
            else:
                self.ad_token_repo.invalidate_token(token_id)
                self.db.commit()
                return False

        except Exception:
            self.ad_token_repo.invalidate_token(token_id)
            self.db.commit()
            return False

    def delete_facebook_user_data(self, facebook_user_id: str) -> dict:
        """
        Delete or anonymize all data associated with a Facebook user.

        This is called by Facebook's data deletion callback when a user
        requests data deletion through Facebook's settings.

        Args:
            facebook_user_id: The Facebook user ID requesting deletion

        Returns:
            dict with deletion status and timestamp
        """
        from datetime import datetime

        try:
            # Find all tokens associated with this Facebook user ID
            # Note: account_ref stores the Facebook user ID for user tokens
            # and "page_{page_id}" for page tokens

            # Get all Facebook tokens across all tenants
            deleted_count = 0

            # Query for tokens with matching account_ref (Facebook user ID)
            tokens = self.db.query(AdToken).filter(
                AdToken.platform == Platform.facebook,
                AdToken.account_ref == facebook_user_id
            ).all()

            for token in tokens:
                # Option 1: Delete the token entirely
                self.db.delete(token)
                deleted_count += 1

                # Option 2: Anonymize instead (uncomment if preferred)
                # token.account_ref = f"deleted_{facebook_user_id}"
                # token.account_name = "Deleted User"
                # token.is_valid = False
                # token.access_token_enc = None
                # token.refresh_token_enc = None
                # deleted_count += 1

            # Also delete any page tokens associated with this user
            # (if they were stored with the user's ID in metadata)
            page_tokens = self.db.query(AdToken).filter(
                AdToken.platform == Platform.facebook,
                AdToken.account_ref.like("page_%")
            ).all()

            for token in page_tokens:
                # Check if this page token's metadata links to the deleted user
                if token.meta and token.meta.get("user_id") == facebook_user_id:
                    self.db.delete(token)
                    deleted_count += 1

            self.db.commit()

            return {
                "status": "success",
                "user_id": facebook_user_id,
                "deleted_count": deleted_count,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.db.rollback()
            return {
                "status": "error",
                "user_id": facebook_user_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
