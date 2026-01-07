# app/repositories/auth_token.py
"""
Repository for refresh token and token blacklist operations.
"""
import datetime as dt
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.repositories.base import BaseRepository
from app.core.models import RefreshToken, TokenBlacklist


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Repository for refresh token operations"""

    def __init__(self, db: Session):
        super().__init__(db, RefreshToken)

    def create_token(
        self,
        user_id: UUID,
        tenant_id: UUID,
        token_hash: str,
        family_id: UUID,
        expires_at: dt.datetime,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> RefreshToken:
        """Create a new refresh token record."""
        return self.create(
            user_id=user_id,
            tenant_id=tenant_id,
            token_hash=token_hash,
            family_id=family_id,
            expires_at=expires_at,
            device_info=device_info,
            ip_address=ip_address,
        )

    def get_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Get a refresh token by its hash."""
        return self.find_one_by(token_hash=token_hash)

    def get_active_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Get an active (not revoked, not expired) refresh token by hash."""
        now = dt.datetime.now(dt.timezone.utc)
        return (
            self.db.query(self.model)
            .filter(
                and_(
                    self.model.token_hash == token_hash,
                    self.model.revoked_at.is_(None),
                    self.model.expires_at > now,
                )
            )
            .first()
        )

    def revoke_token(
        self, token_id: UUID, replaced_by_id: Optional[UUID] = None
    ) -> bool:
        """Revoke a refresh token by ID."""
        token = self.get_by_id(token_id)
        if token:
            token.revoked_at = dt.datetime.now(dt.timezone.utc)
            if replaced_by_id:
                token.replaced_by_id = replaced_by_id
            self.db.flush()
            return True
        return False

    def revoke_family(self, family_id: UUID) -> int:
        """
        Revoke all tokens in a family.
        Used when token reuse is detected (potential theft).
        """
        now = dt.datetime.now(dt.timezone.utc)
        result = (
            self.db.query(self.model)
            .filter(
                and_(
                    self.model.family_id == family_id,
                    self.model.revoked_at.is_(None),
                )
            )
            .update({"revoked_at": now})
        )
        self.db.flush()
        return result

    def revoke_user_tokens(self, user_id: UUID) -> int:
        """
        Revoke all refresh tokens for a user.
        Used for logout from all devices, password change, security revocation.
        """
        now = dt.datetime.now(dt.timezone.utc)
        result = (
            self.db.query(self.model)
            .filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.revoked_at.is_(None),
                )
            )
            .update({"revoked_at": now})
        )
        self.db.flush()
        return result

    def get_user_active_sessions(self, user_id: UUID) -> List[RefreshToken]:
        """Get all active sessions for a user."""
        now = dt.datetime.now(dt.timezone.utc)
        return (
            self.db.query(self.model)
            .filter(
                and_(
                    self.model.user_id == user_id,
                    self.model.revoked_at.is_(None),
                    self.model.expires_at > now,
                )
            )
            .order_by(self.model.created_at.desc())
            .all()
        )

    def cleanup_expired(self) -> int:
        """Delete expired refresh tokens. Returns count of deleted tokens."""
        now = dt.datetime.now(dt.timezone.utc)
        result = (
            self.db.query(self.model)
            .filter(self.model.expires_at < now)
            .delete()
        )
        self.db.flush()
        return result


class TokenBlacklistRepository(BaseRepository[TokenBlacklist]):
    """Repository for JWT blacklist operations"""

    def __init__(self, db: Session):
        super().__init__(db, TokenBlacklist)

    def add_to_blacklist(
        self,
        jti: str,
        user_id: UUID,
        expires_at: dt.datetime,
        reason: Optional[str] = None,
    ) -> TokenBlacklist:
        """Add a JWT token to the blacklist."""
        return self.create(
            jti=jti,
            user_id=user_id,
            expires_at=expires_at,
            reason=reason,
        )

    def is_blacklisted(self, jti: str) -> bool:
        """Check if a JWT token is blacklisted."""
        return self.exists(jti=jti)

    def cleanup_expired(self) -> int:
        """
        Delete blacklist entries for tokens that have naturally expired.
        These entries no longer serve any purpose since the tokens
        would be rejected anyway due to expiration.
        """
        now = dt.datetime.now(dt.timezone.utc)
        result = (
            self.db.query(self.model)
            .filter(self.model.expires_at < now)
            .delete()
        )
        self.db.flush()
        return result

    def blacklist_user_tokens(
        self, user_id: UUID, reason: str = "security_revoke"
    ) -> None:
        """
        Note: This doesn't actually blacklist all user tokens because
        we don't track all issued JTIs. This is a limitation of stateless JWTs.
        For full revocation, use refresh token revocation which forces re-auth.
        """
        pass
