# app/services/mfa_service.py
"""
Multi-Factor Authentication (MFA) service using TOTP (Time-based One-Time Password).
Implements Google Authenticator/Authy compatible 2FA.
"""
import base64
import secrets
import datetime as dt
from typing import List, Optional, Tuple, Dict, Any
import pyotp
import qrcode
from io import BytesIO
from sqlalchemy.orm import Session
from app.core.models import MFASecret, User, UserRole
from app.core.config import get_settings


class MFAService:
    """Service for handling Multi-Factor Authentication"""

    def __init__(self, db: Session):
        self.db = db

    def generate_secret(self) -> str:
        """
        Generate a new TOTP secret.

        Returns:
            str: Base32 encoded secret
        """
        return pyotp.random_base32()

    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """
        Generate backup codes for MFA recovery.

        Args:
            count: Number of backup codes to generate

        Returns:
            List[str]: List of backup codes
        """
        backup_codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric codes
            code = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
            backup_codes.append(code)
        return backup_codes

    def setup_mfa(self, user: User) -> Tuple[str, str, List[str]]:
        """
        Set up MFA for a user (generate secret and backup codes).

        Args:
            user: User to set up MFA for

        Returns:
            Tuple[str, str, List[str]]: (secret, qr_code_url, backup_codes)

        Raises:
            ValueError: If user already has MFA enabled
        """
        # Check if user already has MFA
        existing_mfa = self.db.query(MFASecret).filter_by(user_id=user.id).first()
        if existing_mfa and existing_mfa.is_verified:
            raise ValueError("User already has MFA enabled")

        # Generate new secret and backup codes
        secret = self.generate_secret()
        backup_codes = self.generate_backup_codes()

        # Create or update MFA record
        if existing_mfa:
            existing_mfa.secret = secret
            existing_mfa.backup_codes = backup_codes
            existing_mfa.is_verified = False
            existing_mfa.backup_codes_used = 0
            mfa_record = existing_mfa
        else:
            mfa_record = MFASecret(
                user_id=user.id,
                tenant_id=user.tenant_id,
                secret=secret,
                backup_codes=backup_codes,
                is_verified=False,
                backup_codes_used=0
            )
            self.db.add(mfa_record)

        # Generate QR code URL
        settings = get_settings()
        app_name = "Facebook-TikTok Automation"
        totp = pyotp.TOTP(secret)
        qr_code_url = totp.provisioning_uri(
            name=user.email or user.username,
            issuer_name=app_name
        )

        self.db.commit()
        return secret, qr_code_url, backup_codes

    def generate_qr_code(self, qr_code_url: str) -> bytes:
        """
        Generate QR code image for TOTP setup.

        Args:
            qr_code_url: TOTP provisioning URL

        Returns:
            bytes: PNG image data
        """
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_code_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()

    def verify_totp_code(self, user: User, code: str, allow_backup: bool = True) -> bool:
        """
        Verify a TOTP code or backup code.

        Args:
            user: User to verify code for
            code: 6-digit TOTP code or 8-character backup code
            allow_backup: Whether to allow backup code verification

        Returns:
            bool: True if code is valid, False otherwise
        """
        mfa_record = self.db.query(MFASecret).filter_by(user_id=user.id).first()
        if not mfa_record:
            return False

        # Check if it's a backup code first (8 characters, case insensitive)
        if allow_backup and len(code) == 8 and code.upper() in (mfa_record.backup_codes or []):
            # Mark backup code as used by removing it
            backup_codes = list(mfa_record.backup_codes or [])
            backup_codes.remove(code.upper())
            mfa_record.backup_codes = backup_codes
            mfa_record.backup_codes_used = (mfa_record.backup_codes_used or 0) + 1
            mfa_record.last_used_at = dt.datetime.now(dt.timezone.utc)

            # If this was the verification step, mark as verified
            if not mfa_record.is_verified:
                mfa_record.is_verified = True

            self.db.commit()
            return True

        # Check TOTP code (6 digits)
        if len(code) == 6 and code.isdigit():
            totp = pyotp.TOTP(mfa_record.secret)
            if totp.verify(code):
                mfa_record.last_used_at = dt.datetime.now(dt.timezone.utc)

                # If this was the verification step, mark as verified
                if not mfa_record.is_verified:
                    mfa_record.is_verified = True

                self.db.commit()
                return True

        return False

    def is_mfa_enabled(self, user: User) -> bool:
        """
        Check if user has MFA enabled and verified.

        Args:
            user: User to check

        Returns:
            bool: True if MFA is enabled, False otherwise
        """
        mfa_record = self.db.query(MFASecret).filter_by(user_id=user.id).first()
        return mfa_record is not None and mfa_record.is_verified

    def is_mfa_required(self, user: User) -> bool:
        """
        Check if MFA is required for this user based on their role.

        Args:
            user: User to check

        Returns:
            bool: True if MFA is required, False otherwise
        """
        # MFA required for admin roles (owners)
        return user.role == UserRole.admin

    def disable_mfa(self, user: User) -> bool:
        """
        Disable MFA for a user.

        Args:
            user: User to disable MFA for

        Returns:
            bool: True if MFA was disabled, False if not enabled
        """
        mfa_record = self.db.query(MFASecret).filter_by(user_id=user.id).first()
        if mfa_record:
            self.db.delete(mfa_record)
            self.db.commit()
            return True
        return False

    def get_backup_codes_count(self, user: User) -> int:
        """
        Get the number of remaining backup codes.

        Args:
            user: User to check

        Returns:
            int: Number of remaining backup codes
        """
        mfa_record = self.db.query(MFASecret).filter_by(user_id=user.id).first()
        if mfa_record and mfa_record.backup_codes:
            return len(mfa_record.backup_codes)
        return 0

    def regenerate_backup_codes(self, user: User) -> List[str]:
        """
        Regenerate backup codes for a user.

        Args:
            user: User to regenerate codes for

        Returns:
            List[str]: New backup codes

        Raises:
            ValueError: If user doesn't have MFA enabled
        """
        mfa_record = self.db.query(MFASecret).filter_by(user_id=user.id).first()
        if not mfa_record or not mfa_record.is_verified:
            raise ValueError("User doesn't have MFA enabled")

        backup_codes = self.generate_backup_codes()
        mfa_record.backup_codes = backup_codes
        mfa_record.backup_codes_used = 0
        self.db.commit()

        return backup_codes

    def get_mfa_status(self, user: User) -> Dict[str, Any]:
        """
        Get comprehensive MFA status for a user.

        Args:
            user: User to check

        Returns:
            Dict: MFA status information
        """
        mfa_record = self.db.query(MFASecret).filter_by(user_id=user.id).first()

        if not mfa_record:
            return {
                "enabled": False,
                "required": self.is_mfa_required(user),
                "verified": False,
                "backup_codes_remaining": 0,
                "last_used_at": None
            }

        return {
            "enabled": True,
            "required": self.is_mfa_required(user),
            "verified": mfa_record.is_verified,
            "backup_codes_remaining": len(mfa_record.backup_codes or []),
            "backup_codes_used": mfa_record.backup_codes_used,
            "last_used_at": mfa_record.last_used_at.isoformat() if mfa_record.last_used_at else None,
            "created_at": mfa_record.created_at.isoformat()
        }