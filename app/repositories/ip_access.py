# app/repositories/ip_access.py
"""Repository for IP access control and rate limit violations"""
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import Session

from app.core.models import IPAccessRule, RateLimitViolation, IPRuleType


class IPAccessRepository:
    """Repository for managing IP access rules and rate limit violations"""

    def __init__(self, session: Session):
        self.session = session

    def is_ip_whitelisted(self, ip: str) -> bool:
        """Check if IP is whitelisted"""
        stmt = select(IPAccessRule).where(
            and_(
                IPAccessRule.ip_address == ip,
                IPAccessRule.rule_type == IPRuleType.whitelist,
                IPAccessRule.is_active == True,
                or_(
                    IPAccessRule.expires_at.is_(None),
                    IPAccessRule.expires_at > datetime.utcnow()
                )
            )
        )
        result = self.session.execute(stmt).scalars().first()
        return result is not None

    def is_ip_blacklisted(self, ip: str) -> bool:
        """Check if IP is blacklisted"""
        stmt = select(IPAccessRule).where(
            and_(
                IPAccessRule.ip_address == ip,
                IPAccessRule.rule_type == IPRuleType.blacklist,
                IPAccessRule.is_active == True,
                or_(
                    IPAccessRule.expires_at.is_(None),
                    IPAccessRule.expires_at > datetime.utcnow()
                )
            )
        )
        result = self.session.execute(stmt).scalars().first()
        return result is not None

    def is_ip_auto_banned(self, ip: str) -> bool:
        """Check if IP is auto-banned"""
        stmt = select(IPAccessRule).where(
            and_(
                IPAccessRule.ip_address == ip,
                IPAccessRule.rule_type == IPRuleType.auto_banned,
                IPAccessRule.is_active == True,
                or_(
                    IPAccessRule.expires_at.is_(None),
                    IPAccessRule.expires_at > datetime.utcnow()
                )
            )
        )
        result = self.session.execute(stmt).scalars().first()
        return result is not None

    def add_ip_rule(
        self,
        ip: str,
        rule_type: IPRuleType,
        reason: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        created_by: Optional[str] = None
    ) -> IPAccessRule:
        """Add new IP access rule"""
        rule = IPAccessRule(
            id=uuid4(),
            ip_address=ip,
            rule_type=rule_type,
            reason=reason,
            expires_at=expires_at,
            is_active=True,
            created_by=created_by
        )
        self.session.add(rule)
        self.session.commit()
        self.session.refresh(rule)
        return rule

    def remove_ip_rule(self, ip: str, rule_type: IPRuleType) -> bool:
        """Remove IP access rule (soft delete by setting is_active=False)"""
        stmt = select(IPAccessRule).where(
            and_(
                IPAccessRule.ip_address == ip,
                IPAccessRule.rule_type == rule_type,
                IPAccessRule.is_active == True
            )
        )
        rule = self.session.execute(stmt).scalars().first()
        if rule:
            rule.is_active = False
            rule.updated_at = datetime.utcnow()
            self.session.commit()
            return True
        return False

    def get_active_rules(self, rule_type: Optional[IPRuleType] = None) -> List[IPAccessRule]:
        """Get all active IP access rules"""
        stmt = select(IPAccessRule).where(IPAccessRule.is_active == True)
        if rule_type:
            stmt = stmt.where(IPAccessRule.rule_type == rule_type)

        # Filter out expired rules
        stmt = stmt.where(
            or_(
                IPAccessRule.expires_at.is_(None),
                IPAccessRule.expires_at > datetime.utcnow()
            )
        )

        result = self.session.execute(stmt).scalars().all()
        return list(result)

    def record_violation(self, ip: str, endpoint: str) -> RateLimitViolation:
        """Record a rate limit violation"""
        # Check if violation already exists for this IP+endpoint
        stmt = select(RateLimitViolation).where(
            and_(
                RateLimitViolation.ip_address == ip,
                RateLimitViolation.endpoint == endpoint
            )
        )
        violation = self.session.execute(stmt).scalars().first()

        if violation:
            # Update existing violation
            violation.violation_count += 1
            violation.last_violation_at = datetime.utcnow()
        else:
            # Create new violation record
            violation = RateLimitViolation(
                id=uuid4(),
                ip_address=ip,
                endpoint=endpoint,
                violation_count=1,
                last_violation_at=datetime.utcnow()
            )
            self.session.add(violation)

        self.session.commit()
        self.session.refresh(violation)
        return violation

    def get_violations_count(self, ip: str, time_window: int = 3600) -> int:
        """
        Get count of violations for IP within time window (in seconds)

        Args:
            ip: IP address
            time_window: Time window in seconds (default: 1 hour)
        """
        cutoff_time = datetime.utcnow() - timedelta(seconds=time_window)

        stmt = select(func.sum(RateLimitViolation.violation_count)).where(
            and_(
                RateLimitViolation.ip_address == ip,
                RateLimitViolation.last_violation_at >= cutoff_time
            )
        )
        result = self.session.execute(stmt).scalar()
        return int(result) if result else 0

    def auto_ban_ip(self, ip: str, reason: str, duration_seconds: int = 86400) -> IPAccessRule:
        """
        Automatically ban an IP address

        Args:
            ip: IP address to ban
            reason: Reason for ban
            duration_seconds: Ban duration in seconds (default: 24 hours)
        """
        expires_at = datetime.utcnow() + timedelta(seconds=duration_seconds)

        # Deactivate existing auto-bans for this IP to prevent duplicates
        existing_bans_stmt = select(IPAccessRule).where(
            and_(
                IPAccessRule.ip_address == ip,
                IPAccessRule.rule_type == IPRuleType.auto_banned,
                IPAccessRule.is_active == True
            )
        )
        for existing_rule in self.session.execute(existing_bans_stmt).scalars().all():
            existing_rule.is_active = False
            existing_rule.updated_at = datetime.utcnow()

        # Mark all violations for this IP as auto-banned
        stmt = select(RateLimitViolation).where(RateLimitViolation.ip_address == ip)
        violations = self.session.execute(stmt).scalars().all()
        for violation in violations:
            violation.auto_banned = True

        # Create auto-ban rule
        rule = self.add_ip_rule(
            ip=ip,
            rule_type=IPRuleType.auto_banned,
            reason=reason,
            expires_at=expires_at,
            created_by="system"
        )

        return rule

    def cleanup_expired_rules(self) -> int:
        """Remove expired rules (maintenance task)"""
        stmt = select(IPAccessRule).where(
            and_(
                IPAccessRule.expires_at.isnot(None),
                IPAccessRule.expires_at < datetime.utcnow(),
                IPAccessRule.is_active == True
            )
        )
        expired_rules = self.session.execute(stmt).scalars().all()
        count = len(expired_rules)

        for rule in expired_rules:
            rule.is_active = False
            rule.updated_at = datetime.utcnow()

        if count > 0:
            self.session.commit()

        return count

    def get_rule_by_ip(self, ip: str, rule_type: Optional[IPRuleType] = None) -> Optional[IPAccessRule]:
        """Get active rule for specific IP"""
        stmt = select(IPAccessRule).where(
            and_(
                IPAccessRule.ip_address == ip,
                IPAccessRule.is_active == True
            )
        )
        if rule_type:
            stmt = stmt.where(IPAccessRule.rule_type == rule_type)

        return self.session.execute(stmt).scalars().first()
