# app/services/email_verification_service.py
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.models import User, EmailVerificationToken

class EmailVerificationService:
    """Service for generating and validating secure email verification tokens"""

    def __init__(self):
        self.settings = get_settings()
        # Use master secret key for itsdangerous serializer
        self.serializer = URLSafeTimedSerializer(
            secret_key=self.settings.MASTER_SECRET_KEY.get_secret_value(),
            salt="email-verification"
        )

    def generate_token(self, db: Session, user: User) -> str:
        """
        Generate a secure verification token for the user.

        Returns:
            str: URL-safe verification token
        """
        # Clean up any existing tokens for this user
        self._cleanup_user_tokens(db, user.id)

        # Generate secure random token
        raw_token = secrets.token_urlsafe(32)

        # Create URL-safe signed token with user email and timestamp
        signed_token = self.serializer.dumps({
            "user_id": str(user.id),
            "email": user.email,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Store hashed token in database (security best practice)
        token_hash = hashlib.sha256(signed_token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=self.settings.EMAIL_VERIFICATION_EXPIRE_HOURS
        )

        verification_token = EmailVerificationToken(
            user_id=user.id,
            token=token_hash,
            expires_at=expires_at
        )
        db.add(verification_token)
        db.commit()

        return signed_token

    def verify_token(self, db: Session, token: str) -> Optional[User]:
        """
        Verify email verification token and mark user as verified.

        Args:
            db: Database session
            token: The verification token to validate

        Returns:
            User: The verified user if token is valid, None otherwise
        """
        try:
            # Verify signed token and extract payload
            data = self.serializer.loads(
                token,
                max_age=self.settings.EMAIL_VERIFICATION_EXPIRE_HOURS * 3600
            )

            user_id = data.get("user_id")
            email = data.get("email")

            if not user_id or not email:
                return None

            # Hash the token to match database storage
            token_hash = hashlib.sha256(token.encode()).hexdigest()

            # Find the token in database
            verification_token = db.query(EmailVerificationToken).filter(
                EmailVerificationToken.token == token_hash,
                EmailVerificationToken.used_at.is_(None),
                EmailVerificationToken.expires_at > datetime.now(timezone.utc)
            ).first()

            if not verification_token:
                return None

            # Get the user
            user = db.query(User).filter(
                User.id == verification_token.user_id,
                User.email == email,
                User.is_active == True
            ).first()

            if not user:
                return None

            # Mark user as verified
            user.email_verified = True
            user.email_verified_at = datetime.now(timezone.utc)

            # Mark token as used
            verification_token.used_at = datetime.now(timezone.utc)

            db.commit()
            return user

        except (SignatureExpired, BadSignature, ValueError, KeyError):
            # Token is invalid, expired, or malformed
            return None

    def _cleanup_user_tokens(self, db: Session, user_id: str) -> None:
        """Remove expired and used tokens for a user"""
        now = datetime.now(timezone.utc)

        # Delete expired tokens
        db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user_id,
            EmailVerificationToken.expires_at < now
        ).delete()

        # Delete already used tokens
        db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user_id,
            EmailVerificationToken.used_at.isnot(None)
        ).delete()

        db.commit()

    def resend_verification(self, db: Session, user: User) -> bool:
        """
        Check if user can request another verification email (rate limiting).

        Returns:
            bool: True if user can request resend, False if rate limited
        """
        # Check recent token generation (rate limiting)
        recent_threshold = datetime.now(timezone.utc) - timedelta(minutes=10)

        recent_token = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.created_at > recent_threshold
        ).first()

        return recent_token is None

    def cleanup_expired_tokens(self, db: Session) -> int:
        """
        Cleanup expired verification tokens (background job).

        Returns:
            int: Number of tokens cleaned up
        """
        now = datetime.now(timezone.utc)

        expired_count = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.expires_at < now
        ).count()

        db.query(EmailVerificationToken).filter(
            EmailVerificationToken.expires_at < now
        ).delete()

        db.commit()
        return expired_count