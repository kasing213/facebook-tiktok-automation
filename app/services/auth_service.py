# app/services/auth_service.py
from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.core.models import AdToken, Platform, User, TokenType, SocialIdentity, FacebookPage
from app.repositories import AdTokenRepository, UserRepository
from app.repositories.social_identity import SocialIdentityRepository
from app.repositories.facebook_page import FacebookPageRepository
from app.core.crypto import TokenEncryptor
from app.integrations.oauth import OAuthResult, FacebookAPIClient

logger = logging.getLogger(__name__)

# Scopes recorded for Facebook page tokens (informational - pages inherit from user OAuth)
FB_PAGE_TOKEN_SCOPES = "pages_manage_posts,pages_read_engagement"


class AuthService:
    """Service layer for authentication and token management"""

    def __init__(self, db: Session, encryptor: TokenEncryptor):
        self.db = db
        self.ad_token_repo = AdTokenRepository(db)
        self.user_repo = UserRepository(db)
        self.social_identity_repo = SocialIdentityRepository(db)
        self.facebook_page_repo = FacebookPageRepository(db)
        self.encryptor = encryptor

    def store_oauth_token(
        self,
        tenant_id: UUID,
        oauth_result: OAuthResult,
        user_id: UUID  # NOW REQUIRED - enforces per-user ownership
    ) -> AdToken:
        """
        Store OAuth token with encryption and handle platform-specific data

        CRITICAL: user_id is REQUIRED - enforces per-user token ownership
        """
        if user_id is None:
            raise ValueError("user_id is required and cannot be None")

        encrypted_access_token = self.encryptor.enc(oauth_result.access_token)
        encrypted_refresh_token = None
        if oauth_result.refresh_token:
            encrypted_refresh_token = self.encryptor.enc(oauth_result.refresh_token)

        # Extract user info from platform-specific data
        account_name = None
        email = None
        facebook_user_id = None
        platform_user_id = oauth_result.account_ref

        if oauth_result.platform == Platform.facebook and oauth_result.raw.get("user"):
            user_data = oauth_result.raw["user"]
            account_name = user_data.get("name")
            email = user_data.get("email")
            # CRITICAL: Extract real Facebook user ID (stable anchor)
            facebook_user_id = user_data.get("id")
            platform_user_id = facebook_user_id  # Use FB user ID as platform_user_id
        elif oauth_result.platform == Platform.tiktok and oauth_result.raw.get("user"):
            user_data = oauth_result.raw["user"]
            account_name = user_data.get("display_name") or user_data.get("username")
            platform_user_id = oauth_result.account_ref  # TikTok open_id

        # Step 1: Create or update SocialIdentity
        social_identity = self.social_identity_repo.create_or_update(
            tenant_id=tenant_id,
            user_id=user_id,
            platform=oauth_result.platform,
            platform_user_id=platform_user_id,
            facebook_user_id=facebook_user_id,  # CRITICAL: Store real FB user ID
            display_name=account_name,
            email=email,
            profile_data=oauth_result.raw.get("user")
        )

        # Step 2: Soft delete existing user token (enforces "one active token" per user)
        existing_tokens = self.ad_token_repo.get_user_tokens_by_type(
            tenant_id=tenant_id,
            user_id=user_id,
            token_type=TokenType.user,
            valid_only=True
        )
        for existing_token in existing_tokens:
            if existing_token.platform == oauth_result.platform:
                self.ad_token_repo.soft_delete(existing_token.id)

        # Step 3: Create new token linked to social_identity
        token = self.ad_token_repo.create_token(
            tenant_id=tenant_id,
            user_id=user_id,
            platform=oauth_result.platform,
            social_identity_id=social_identity.id,
            token_type=TokenType.user,
            access_token_enc=encrypted_access_token,
            account_ref=platform_user_id,
            account_name=account_name,
            refresh_token_enc=encrypted_refresh_token,
            scope=oauth_result.scope,
            expires_at=oauth_result.expires_at,
            meta=oauth_result.raw
        )

        # Store Facebook page tokens as separate entries
        if oauth_result.platform == Platform.facebook and oauth_result.raw.get("pages"):
            self._store_facebook_page_tokens(
                tenant_id=tenant_id,
                user_id=user_id,
                social_identity=social_identity,
                pages=oauth_result.raw["pages"]
            )

        self.db.commit()
        return token

    def _store_facebook_page_tokens(
        self,
        tenant_id: UUID,
        user_id: UUID,
        social_identity: SocialIdentity,
        pages: list
    ) -> None:
        """
        Store Facebook page tokens as separate AdToken entries with FacebookPage entities

        CRITICAL: Creates structured FacebookPage entities and links page tokens
        """
        for page in pages:
            if not page.get("access_token"):
                continue

            encrypted_page_token = self.encryptor.enc(page["access_token"])
            page_id = page.get("id")
            page_name = page.get("name")
            page_category = page.get("category")

            # Convert tasks to Python list if it's a JSON string
            page_tasks = page.get("tasks", [])
            if isinstance(page_tasks, str):
                import json
                try:
                    page_tasks = json.loads(page_tasks)
                except (json.JSONDecodeError, ValueError):
                    logger.warning(f"Failed to parse tasks JSON string for page {page_id}, using empty list")
                    page_tasks = []

            # Step 1: Create or update FacebookPage entity
            facebook_page = self.facebook_page_repo.create_or_update(
                social_identity_id=social_identity.id,
                page_id=page_id,
                name=page_name,
                category=page_category,
                tasks=page_tasks,
                page_data=page
            )

            # Step 2: Soft delete existing page token (enforces "one active token" per page)
            logger.info(f"Looking for existing page tokens: page_id={page_id}, facebook_page.id={facebook_page.id}")
            existing_page_tokens = self.ad_token_repo.find_by(
                tenant_id=tenant_id,
                user_id=user_id,
                platform=Platform.facebook,
                facebook_page_id=facebook_page.id,
                deleted_at=None
            )
            logger.info(f"Found {len(existing_page_tokens)} existing page token(s) to soft-delete")
            for existing_token in existing_page_tokens:
                logger.info(f"Soft-deleting existing page token: id={existing_token.id}, token_type={existing_token.token_type}")
                self.ad_token_repo.soft_delete(existing_token.id)

            # Step 3: Create new page token linked to FacebookPage
            logger.info(f"Creating new page token: page_id={page_id}, token_type=TokenType.page")
            new_token = self.ad_token_repo.create_token(
                tenant_id=tenant_id,
                user_id=user_id,
                platform=Platform.facebook,
                social_identity_id=social_identity.id,
                facebook_page_id=facebook_page.id,
                token_type=TokenType.page,
                access_token_enc=encrypted_page_token,
                account_ref=f"page_{page_id}",
                account_name=page_name,
                scope=FB_PAGE_TOKEN_SCOPES,
                expires_at=None,  # Page tokens don't expire unless revoked
                meta=page
            )
            logger.info(f"Created page token: id={new_token.id}, token_type={new_token.token_type}")

    def get_decrypted_token(
        self,
        tenant_id: UUID,
        platform: Platform,
        user_id: UUID,  # NOW REQUIRED
        account_ref: str = None,
        social_identity_id: Optional[UUID] = None,
        facebook_page_id: Optional[UUID] = None
    ) -> Optional[str]:
        """
        Get decrypted access token for a platform

        CRITICAL: user_id is REQUIRED - enforces per-user token access
        """
        if user_id is None:
            raise ValueError("user_id is required and cannot be None")

        token = self.ad_token_repo.get_active_token(
            tenant_id=tenant_id,
            platform=platform,
            user_id=user_id,
            account_ref=account_ref,
            social_identity_id=social_identity_id,
            facebook_page_id=facebook_page_id
        )
        if token and token.is_valid:
            try:
                return self.encryptor.dec(token.access_token_enc)
            except Exception:
                # Token decryption failed, mark as invalid
                self.ad_token_repo.invalidate_token(token.id)
                self.db.commit()
        return None

    def validate_token(
        self,
        token_id: UUID,
        user_id: UUID,
        is_valid: bool = True
    ) -> Optional[AdToken]:
        """
        Update token validation status

        CRITICAL: Verifies user owns token before updating
        """
        if not self.ad_token_repo.verify_user_owns_token(token_id, user_id):
            raise PermissionError(f"User {user_id} does not own token {token_id}")

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
        user_id: UUID,  # NOW REQUIRED
        account_ref: str = None,
        social_identity_id: Optional[UUID] = None,
        facebook_page_id: Optional[UUID] = None
    ) -> Optional[FacebookAPIClient]:
        """
        Get Facebook API client with decrypted token

        CRITICAL: user_id is REQUIRED - enforces per-user token access
        """
        token = self.get_decrypted_token(
            tenant_id=tenant_id,
            platform=Platform.facebook,
            user_id=user_id,
            account_ref=account_ref,
            social_identity_id=social_identity_id,
            facebook_page_id=facebook_page_id
        )
        if token:
            return FacebookAPIClient(token)
        return None

    def get_facebook_page_tokens(
        self,
        tenant_id: UUID,
        user_id: UUID  # NOW REQUIRED
    ) -> list[dict]:
        """
        Get all Facebook page tokens for a user

        CRITICAL: user_id is REQUIRED - returns only user's pages
        """
        if user_id is None:
            raise ValueError("user_id is required and cannot be None")

        # Get user's Facebook pages via repository
        pages = self.facebook_page_repo.get_user_pages(tenant_id, user_id)
        page_tokens = []

        for page in pages:
            # Get the token for this page
            token = self.ad_token_repo.get_active_token(
                tenant_id=tenant_id,
                platform=Platform.facebook,
                user_id=user_id,
                facebook_page_id=page.id
            )

            if token and token.is_valid:
                try:
                    decrypted_token = self.encryptor.dec(token.access_token_enc)
                    page_tokens.append({
                        "id": str(token.id),
                        "page_id": page.page_id,
                        "page_name": page.name,
                        "category": page.category,
                        "tasks": page.tasks,
                        "access_token": decrypted_token,
                        "meta": token.meta
                    })
                except Exception:
                    # Token decryption failed, mark as invalid
                    self.ad_token_repo.invalidate_token(token.id)
                    self.db.commit()

        return page_tokens

    async def refresh_facebook_token(
        self,
        token_id: UUID,
        user_id: UUID  # NOW REQUIRED - ownership verification
    ) -> bool:
        """
        Attempt to refresh Facebook token (limited refresh capabilities)

        CRITICAL: Verifies user owns token before refreshing
        """
        # Verify ownership
        if not self.ad_token_repo.verify_user_owns_token(token_id, user_id):
            raise PermissionError(f"User {user_id} does not own token {token_id}")

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
        user_id: UUID,  # NOW REQUIRED
        account_ref: str = None,
        social_identity_id: Optional[UUID] = None
    ):
        """
        Get TikTok API client with decrypted token

        CRITICAL: user_id is REQUIRED - enforces per-user token access
        """
        from app.integrations.tiktok import TikTokAPIClient

        token = self.get_decrypted_token(
            tenant_id=tenant_id,
            platform=Platform.tiktok,
            user_id=user_id,
            account_ref=account_ref,
            social_identity_id=social_identity_id
        )
        if token:
            return TikTokAPIClient(token)
        return None

    def get_tiktok_creator_info(
        self,
        tenant_id: UUID,
        user_id: UUID,  # NOW REQUIRED
        account_ref: str = None
    ) -> dict:
        """
        Get TikTok creator information for a user

        CRITICAL: user_id is REQUIRED - returns only user's TikTok data
        """
        if user_id is None:
            raise ValueError("user_id is required and cannot be None")

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

    async def validate_tiktok_token(
        self,
        token_id: UUID,
        user_id: UUID  # NOW REQUIRED - ownership verification
    ) -> bool:
        """
        Validate TikTok token by making an API call

        CRITICAL: Verifies user owns token before validating
        """
        # Verify ownership
        if not self.ad_token_repo.verify_user_owns_token(token_id, user_id):
            raise PermissionError(f"User {user_id} does not own token {token_id}")

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
            facebook_user_id: The real Facebook user ID requesting deletion

        Returns:
            dict with deletion status and timestamp
        """
        from datetime import datetime

        try:
            deleted_count = 0

            # Step 1: Find social identity by facebook_user_id
            social_identity = self.social_identity_repo.get_by_facebook_user_id(facebook_user_id)

            if not social_identity:
                # No data found for this Facebook user
                return {
                    "status": "success",
                    "user_id": facebook_user_id,
                    "deleted_count": 0,
                    "message": "No data found",
                    "timestamp": datetime.utcnow().isoformat()
                }

            # Step 2: Soft delete all tokens associated with this social identity
            # This includes both user tokens and page tokens
            tokens = self.db.query(AdToken).filter(
                AdToken.social_identity_id == social_identity.id,
                AdToken.deleted_at == None
            ).all()

            for token in tokens:
                self.ad_token_repo.soft_delete(token.id)
                deleted_count += 1

            # Step 3: Deactivate Facebook pages (soft delete at page level)
            facebook_pages = self.facebook_page_repo.get_identity_pages(social_identity.id)
            for page in facebook_pages:
                self.facebook_page_repo.deactivate(page.id)

            # Step 4: Deactivate social identity (soft delete at identity level)
            self.social_identity_repo.deactivate(social_identity.id)

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
