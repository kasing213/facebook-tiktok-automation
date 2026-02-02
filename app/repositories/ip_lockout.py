# app/repositories/ip_lockout.py
"""
Repository for IP lockout management.
"""
import datetime as dt
from typing import Optional, List
from sqlalchemy.orm import Session
from app.core.models import IPLockout
from app.repositories.base import BaseRepository


class IPLockoutRepository(BaseRepository[IPLockout]):
    """Repository for managing IP address lockouts"""

    def __init__(self, db: Session):
        super().__init__(db, IPLockout)

    def create_lockout(
        self,
        ip_address: str,
        failed_attempts_count: int,
        unlock_at: dt.datetime,
        lockout_reason: str = "too_many_failures_from_ip"
    ) -> IPLockout:
        """
        Create a new IP lockout.

        Args:
            ip_address: IP address to lock
            failed_attempts_count: Number of failed attempts that triggered lockout
            unlock_at: When the lockout should expire
            lockout_reason: Reason for the lockout

        Returns:
            IPLockout: Created lockout record
        """
        return self.create(
            ip_address=ip_address,
            failed_attempts_count=failed_attempts_count,
            unlock_at=unlock_at,
            lockout_reason=lockout_reason
        )

    def get_active_lockout(self, ip_address: str) -> Optional[IPLockout]:
        """
        Get active lockout for an IP address.

        Args:
            ip_address: IP address to check

        Returns:
            IPLockout: Active lockout record or None
        """
        now = dt.datetime.now(dt.timezone.utc)

        return self.db.query(IPLockout).filter(
            IPLockout.ip_address == ip_address,
            IPLockout.unlocked_at.is_(None),  # Not manually unlocked
            IPLockout.unlock_at > now  # Lock period not expired
        ).first()

    def is_ip_locked(self, ip_address: str) -> bool:
        """
        Check if an IP address is currently locked.

        Args:
            ip_address: IP address to check

        Returns:
            bool: True if IP is locked, False otherwise
        """
        return self.get_active_lockout(ip_address) is not None

    def unlock_ip(self, ip_address: str, unlocked_by: str) -> bool:
        """
        Manually unlock an IP address (admin action).

        Args:
            ip_address: IP address to unlock
            unlocked_by: Admin username/email who performed the unlock

        Returns:
            bool: True if IP was unlocked, False if no active lockout found
        """
        active_lockout = self.get_active_lockout(ip_address)

        if active_lockout:
            now = dt.datetime.now(dt.timezone.utc)
            active_lockout.unlocked_at = now
            active_lockout.unlocked_by = unlocked_by
            self.db.flush()
            return True

        return False

    def get_ip_lockout_history(
        self,
        ip_address: str,
        days: int = 30
    ) -> List[IPLockout]:
        """
        Get lockout history for an IP address.

        Args:
            ip_address: IP address to check
            days: Number of days to look back

        Returns:
            List[IPLockout]: List of lockout records
        """
        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)

        return self.db.query(IPLockout).filter(
            IPLockout.ip_address == ip_address,
            IPLockout.locked_at >= cutoff
        ).order_by(IPLockout.locked_at.desc()).all()

    def cleanup_expired_lockouts(self, days_to_keep: int = 30) -> int:
        """
        Clean up old lockout records.

        Args:
            days_to_keep: Number of days to keep records

        Returns:
            int: Number of records deleted
        """
        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days_to_keep)

        deleted_count = self.db.query(IPLockout).filter(
            IPLockout.locked_at < cutoff
        ).delete()

        return deleted_count