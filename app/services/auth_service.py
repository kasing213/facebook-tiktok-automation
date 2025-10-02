# app/services/auth_service.py
from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.models import AdToken, Platform, User
from app.repositories import AdTokenRepository, UserRepository
from app.core.crypto import load_encryptor
from app.integrations.oauth import OAuthResult


class AuthService:
    """Service layer for authentication and token management"""

    def __init__(self, db: Session):
        self.db = db
        self.ad_token_repo = AdTokenRepository(db)
        self.user_repo = UserRepository(db)
        self.encryptor = load_encryptor()

    def store_oauth_token(self, tenant_id: UUID, oauth_result: OAuthResult) -> AdToken:
        """Store OAuth token with encryption"""
        encrypted_access_token = self.encryptor.enc(oauth_result.access_token)
        encrypted_refresh_token = None
        if oauth_result.refresh_token:
            encrypted_refresh_token = self.encryptor.enc(oauth_result.refresh_token)

        # Check if token already exists for this platform/account
        existing_token = None
        if oauth_result.account_ref:
            existing_token = self.ad_token_repo.get_active_token(
                tenant_id, oauth_result.platform, oauth_result.account_ref
            )

        if existing_token:
            # Update existing token
            token = self.ad_token_repo.update(
                existing_token.id,
                access_token_enc=encrypted_access_token,
                refresh_token_enc=encrypted_refresh_token,
                scope=oauth_result.scope,
                expires_at=oauth_result.expires_at,
                is_valid=True,
                meta=oauth_result.raw
            )
        else:
            # Create new token
            token = self.ad_token_repo.create_token(
                tenant_id=tenant_id,
                platform=oauth_result.platform,
                access_token_enc=encrypted_access_token,
                account_ref=oauth_result.account_ref,
                refresh_token_enc=encrypted_refresh_token,
                scope=oauth_result.scope,
                expires_at=oauth_result.expires_at,
                meta=oauth_result.raw
            )

        self.db.commit()
        return token

    def get_decrypted_token(self, tenant_id: UUID, platform: Platform, account_ref: str = None) -> Optional[str]:
        """Get decrypted access token for a platform"""
        token = self.ad_token_repo.get_active_token(tenant_id, platform, account_ref)
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

    def get_tenant_tokens(self, tenant_id: UUID, platform: Platform = None) -> list[AdToken]:
        """Get all tokens for a tenant, optionally filtered by platform"""
        if platform:
            return self.ad_token_repo.get_by_platform(tenant_id, platform)
        return self.ad_token_repo.get_tenant_tokens(tenant_id)

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