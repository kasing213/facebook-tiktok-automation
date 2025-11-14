# app/jobs/token_refresh.py
"""
Background jobs for automatic token refresh and validation.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session
from app.core.db import get_db_session
from app.core.models import AdToken, Platform
from app.repositories import AdTokenRepository
from app.services import AuthService
from app.core.crypto import load_encryptor
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class TokenRefreshJob:
    """Background job for refreshing OAuth tokens"""

    def __init__(self):
        self.logger = logger

    async def run_token_validation(self):
        """Run token validation for all tokens nearing expiry"""
        try:
            # Get database session
            with get_db_session() as db:
                # Initialize services
                settings = get_settings()
                encryptor = load_encryptor(settings.MASTER_SECRET_KEY.get_secret_value())
                auth_service = AuthService(db, encryptor)

                # Get tokens expiring in next 24 hours
                expiring_tokens = auth_service.get_expiring_tokens(24)

                self.logger.info(f"Found {len(expiring_tokens)} tokens expiring in next 24 hours")

                # Process Facebook tokens
                facebook_tokens = [t for t in expiring_tokens if t.platform == Platform.facebook]
                for token in facebook_tokens:
                    try:
                        await self._refresh_facebook_token(auth_service, token)
                    except Exception as e:
                        self.logger.error(f"Failed to refresh Facebook token {token.id}: {e}")

                # TikTok tokens would be handled here with their refresh logic
                # tiktok_tokens = [t for t in expiring_tokens if t.platform == Platform.tiktok]

                self.logger.info("Token validation job completed")

        except Exception as e:
            self.logger.error(f"Token validation job failed: {e}")

    async def _refresh_facebook_token(self, auth_service: AuthService, token: AdToken):
        """Refresh a Facebook token"""
        try:
            success = await auth_service.refresh_facebook_token(token.id)
            if success:
                self.logger.info(f"Successfully validated Facebook token {token.id}")
            else:
                self.logger.warning(f"Facebook token {token.id} is invalid and was marked as such")
        except Exception as e:
            self.logger.error(f"Error refreshing Facebook token {token.id}: {e}")

    async def run_daily_cleanup(self):
        """Run daily cleanup of invalid and expired tokens"""
        try:
            with get_db_session() as db:
                token_repo = AdTokenRepository(db)

                # Mark tokens as invalid if they expired more than 7 days ago
                cutoff_date = datetime.utcnow() - timedelta(days=7)
                expired_tokens = (
                    db.query(AdToken)
                    .filter(
                        AdToken.expires_at.isnot(None),
                        AdToken.expires_at < cutoff_date,
                        AdToken.is_valid == True
                    )
                    .all()
                )

                for token in expired_tokens:
                    token_repo.invalidate_token(token.id)
                    self.logger.info(f"Marked expired token {token.id} as invalid")

                db.commit()
                self.logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")

        except Exception as e:
            self.logger.error(f"Daily cleanup job failed: {e}")


# Global job instance
token_refresh_job = TokenRefreshJob()


async def run_token_refresh_scheduler():
    """Run the token refresh scheduler - call this from your main application"""
    while True:
        try:
            # Run token validation every hour
            await token_refresh_job.run_token_validation()

            # Wait 1 hour
            await asyncio.sleep(3600)

        except Exception as e:
            logger.error(f"Token refresh scheduler error: {e}")
            # Wait 5 minutes before retrying on error
            await asyncio.sleep(300)


async def run_daily_cleanup_scheduler():
    """Run daily cleanup scheduler"""
    while True:
        try:
            # Run cleanup once per day
            await token_refresh_job.run_daily_cleanup()

            # Wait 24 hours
            await asyncio.sleep(86400)

        except Exception as e:
            logger.error(f"Daily cleanup scheduler error: {e}")
            # Wait 1 hour before retrying on error
            await asyncio.sleep(3600)