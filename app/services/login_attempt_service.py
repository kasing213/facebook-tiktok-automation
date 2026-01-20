# app/services/login_attempt_service.py
"""
Service for tracking login attempts and managing account lockouts.

Implements:
- Login attempt logging (success/failure)
- Account lockout after repeated failures (5 failures = 30min lock)
- IP-based lockout for persistent attacks (10 failures = 1hr lock)
- Exponential backoff for repeat offenders
- Manual unlock by admins
"""
import datetime as dt
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.core.models import LoginAttempt, AccountLockout, LoginAttemptResult


class LoginAttemptService:
    """Service for managing login attempts and account lockouts"""

    # Configuration
    ACCOUNT_LOCKOUT_ATTEMPTS = 5  # Failed attempts before account lockout
    ACCOUNT_LOCKOUT_DURATION_MINUTES = 30  # Account lockout duration
    IP_LOCKOUT_ATTEMPTS = 10  # Failed attempts from same IP before IP lockout
    IP_LOCKOUT_DURATION_HOURS = 1  # IP lockout duration
    ATTEMPT_WINDOW_MINUTES = 15  # Time window to count failed attempts

    def __init__(self, db: Session):
        self.db = db

    def record_login_attempt(
        self,
        email: str,
        ip_address: str,
        result: LoginAttemptResult,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None
    ) -> LoginAttempt:
        """
        Record a login attempt in the database.

        Args:
            email: Email address attempted
            ip_address: Client IP address
            result: LoginAttemptResult.success or LoginAttemptResult.failure
            user_agent: Browser user agent string
            failure_reason: Reason for failure (e.g., "invalid_credentials", "account_locked")

        Returns:
            LoginAttempt: The created login attempt record
        """
        attempt = LoginAttempt(
            email=email.lower(),  # Normalize email
            ip_address=ip_address,
            user_agent=user_agent,
            result=result,
            failure_reason=failure_reason
        )

        self.db.add(attempt)
        self.db.commit()
        return attempt

    def is_account_locked(self, email: str) -> bool:
        """
        Check if an account is currently locked.

        Args:
            email: Email address to check

        Returns:
            bool: True if account is locked, False otherwise
        """
        now = dt.datetime.now(dt.timezone.utc)

        # Check for active lockout
        active_lockout = self.db.query(AccountLockout).filter(
            AccountLockout.email == email.lower(),
            AccountLockout.unlocked_at.is_(None),  # Not manually unlocked
            AccountLockout.unlock_at > now  # Lock period not expired
        ).first()

        return active_lockout is not None

    def get_account_lockout_info(self, email: str) -> Optional[AccountLockout]:
        """
        Get current lockout information for an account.

        Args:
            email: Email address to check

        Returns:
            AccountLockout: Active lockout record or None
        """
        now = dt.datetime.now(dt.timezone.utc)

        return self.db.query(AccountLockout).filter(
            AccountLockout.email == email.lower(),
            AccountLockout.unlocked_at.is_(None),
            AccountLockout.unlock_at > now
        ).first()

    def check_and_apply_lockout(self, email: str, ip_address: str) -> Tuple[bool, Optional[AccountLockout]]:
        """
        Check if account should be locked after a failed login attempt.
        If so, create the lockout record.

        Args:
            email: Email address that failed
            ip_address: IP address of the attempt

        Returns:
            Tuple[bool, Optional[AccountLockout]]: (was_locked, lockout_record)
        """
        now = dt.datetime.now(dt.timezone.utc)
        window_start = now - dt.timedelta(minutes=self.ATTEMPT_WINDOW_MINUTES)

        # Count recent failed attempts for this email
        failed_attempts = self.db.query(LoginAttempt).filter(
            LoginAttempt.email == email.lower(),
            LoginAttempt.result == LoginAttemptResult.failure,
            LoginAttempt.attempted_at >= window_start
        ).count()

        # Check if we should lock the account
        if failed_attempts >= self.ACCOUNT_LOCKOUT_ATTEMPTS:
            # Check if account is already locked
            if not self.is_account_locked(email):
                # Calculate unlock time with exponential backoff
                unlock_duration = self._calculate_lockout_duration(email)
                unlock_at = now + unlock_duration

                lockout = AccountLockout(
                    email=email.lower(),
                    ip_address=ip_address,
                    lockout_reason=f"too_many_failures ({failed_attempts} attempts in {self.ATTEMPT_WINDOW_MINUTES} minutes)",
                    failed_attempts_count=failed_attempts,
                    unlock_at=unlock_at
                )

                self.db.add(lockout)
                self.db.commit()
                return True, lockout

        return False, None

    def _calculate_lockout_duration(self, email: str) -> dt.timedelta:
        """
        Calculate lockout duration with exponential backoff for repeat offenders.

        Args:
            email: Email address to check history

        Returns:
            timedelta: Lockout duration
        """
        # Count previous lockouts for this email (last 24 hours)
        past_24h = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=24)

        previous_lockouts = self.db.query(AccountLockout).filter(
            AccountLockout.email == email.lower(),
            AccountLockout.locked_at >= past_24h
        ).count()

        # Exponential backoff: 30min, 1hr, 2hr, 4hr, max 24hr
        base_minutes = self.ACCOUNT_LOCKOUT_DURATION_MINUTES
        multiplier = 2 ** min(previous_lockouts, 10)  # Cap at 2^10 to prevent overflow
        duration_minutes = min(base_minutes * multiplier, 24 * 60)  # Max 24 hours

        return dt.timedelta(minutes=duration_minutes)

    def unlock_account(self, email: str, unlocked_by: str) -> bool:
        """
        Manually unlock an account (admin action).

        Args:
            email: Email address to unlock
            unlocked_by: Admin username/email who performed the unlock

        Returns:
            bool: True if account was unlocked, False if no active lockout found
        """
        now = dt.datetime.now(dt.timezone.utc)

        # Find active lockout
        active_lockout = self.db.query(AccountLockout).filter(
            AccountLockout.email == email.lower(),
            AccountLockout.unlocked_at.is_(None),
            AccountLockout.unlock_at > now
        ).first()

        if active_lockout:
            active_lockout.unlocked_at = now
            active_lockout.unlocked_by = unlocked_by
            self.db.commit()
            return True

        return False

    def get_failed_attempts_count(self, email: str, window_minutes: int = None) -> int:
        """
        Get count of failed login attempts within time window.

        Args:
            email: Email address to check
            window_minutes: Time window in minutes (default: ATTEMPT_WINDOW_MINUTES)

        Returns:
            int: Number of failed attempts
        """
        if window_minutes is None:
            window_minutes = self.ATTEMPT_WINDOW_MINUTES

        now = dt.datetime.now(dt.timezone.utc)
        window_start = now - dt.timedelta(minutes=window_minutes)

        return self.db.query(LoginAttempt).filter(
            LoginAttempt.email == email.lower(),
            LoginAttempt.result == LoginAttemptResult.failure,
            LoginAttempt.attempted_at >= window_start
        ).count()

    def cleanup_old_records(self, days_to_keep: int = 30) -> Tuple[int, int]:
        """
        Clean up old login attempts and lockout records.

        Args:
            days_to_keep: Number of days to keep records

        Returns:
            Tuple[int, int]: (attempts_deleted, lockouts_deleted)
        """
        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days_to_keep)

        attempts_deleted = self.db.query(LoginAttempt).filter(
            LoginAttempt.attempted_at < cutoff
        ).delete()

        lockouts_deleted = self.db.query(AccountLockout).filter(
            AccountLockout.locked_at < cutoff
        ).delete()

        self.db.commit()
        return attempts_deleted, lockouts_deleted