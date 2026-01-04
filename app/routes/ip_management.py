# app/routes/ip_management.py
"""
Admin endpoints for IP access control and rate limit management
"""
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.deps import get_logger, LoggerDep
from app.routes.auth import get_current_user
from app.core.models import User, UserRole, IPRuleType, IPAccessRule, RateLimitViolation
from app.core.db import SessionLocal
from app.repositories.ip_access import IPAccessRepository


router = APIRouter(prefix="/api/admin/ip", tags=["admin", "ip-management"])


# Request/Response models
class CreateIPRuleRequest(BaseModel):
    """Request to create IP access rule"""
    ip_address: str = Field(..., description="IP address to whitelist/blacklist", min_length=7, max_length=45)
    rule_type: IPRuleType = Field(..., description="Rule type: whitelist, blacklist, or auto_banned")
    reason: Optional[str] = Field(None, description="Reason for the rule")
    expires_hours: Optional[int] = Field(None, description="Hours until rule expires (null = permanent)", ge=1)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ip_address": "192.168.1.100",
                    "rule_type": "whitelist",
                    "reason": "Internal office IP"
                },
                {
                    "ip_address": "203.0.113.42",
                    "rule_type": "blacklist",
                    "reason": "Malicious activity detected",
                    "expires_hours": 24
                }
            ]
        }
    }


class IPRuleResponse(BaseModel):
    """IP access rule response"""
    id: str
    ip_address: str
    rule_type: str
    reason: Optional[str]
    expires_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    created_by: Optional[str]

    model_config = {"from_attributes": True}


class RateLimitViolationResponse(BaseModel):
    """Rate limit violation response"""
    id: str
    ip_address: str
    endpoint: str
    violation_count: int
    last_violation_at: datetime
    auto_banned: bool

    model_config = {"from_attributes": True}


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require admin role"""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.post("/rules", response_model=IPRuleResponse)
def create_ip_rule(
    request: CreateIPRuleRequest,
    logger: LoggerDep,
    admin_user: User = Depends(require_admin)
):
    """
    Create IP access rule (whitelist/blacklist)

    Requires admin role.
    """
    try:
        with SessionLocal() as session:
            ip_repo = IPAccessRepository(session)

            # Calculate expiry if specified
            expires_at = None
            if request.expires_hours:
                expires_at = datetime.utcnow() + timedelta(hours=request.expires_hours)

            # Create rule
            rule = ip_repo.add_ip_rule(
                ip=request.ip_address,
                rule_type=request.rule_type,
                reason=request.reason,
                expires_at=expires_at,
                created_by=admin_user.username or admin_user.email or str(admin_user.id)
            )

            logger.info(f"IP rule created: {request.rule_type} for {request.ip_address} by {admin_user.email}")

            return IPRuleResponse(
                id=str(rule.id),
                ip_address=rule.ip_address,
                rule_type=rule.rule_type.value,
                reason=rule.reason,
                expires_at=rule.expires_at,
                is_active=rule.is_active,
                created_at=rule.created_at,
                created_by=rule.created_by
            )

    except Exception as e:
        logger.error(f"Failed to create IP rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to create IP rule")


@router.get("/rules", response_model=List[IPRuleResponse])
def list_ip_rules(
    rule_type: Optional[IPRuleType] = Query(None, description="Filter by rule type"),
    logger: LoggerDep,
    admin_user: User = Depends(require_admin)
):
    """
    List all active IP access rules

    Requires admin role.
    """
    try:
        with SessionLocal() as session:
            ip_repo = IPAccessRepository(session)
            rules = ip_repo.get_active_rules(rule_type=rule_type)

            return [
                IPRuleResponse(
                    id=str(rule.id),
                    ip_address=rule.ip_address,
                    rule_type=rule.rule_type.value,
                    reason=rule.reason,
                    expires_at=rule.expires_at,
                    is_active=rule.is_active,
                    created_at=rule.created_at,
                    created_by=rule.created_by
                )
                for rule in rules
            ]

    except Exception as e:
        logger.error(f"Failed to list IP rules: {e}")
        raise HTTPException(status_code=500, detail="Failed to list IP rules")


@router.delete("/rules/{ip_address}")
def remove_ip_rule(
    ip_address: str,
    rule_type: IPRuleType = Query(..., description="Rule type to remove"),
    logger: LoggerDep,
    admin_user: User = Depends(require_admin)
):
    """
    Remove IP access rule

    Requires admin role.
    """
    try:
        with SessionLocal() as session:
            ip_repo = IPAccessRepository(session)
            success = ip_repo.remove_ip_rule(ip=ip_address, rule_type=rule_type)

            if not success:
                raise HTTPException(status_code=404, detail=f"No active {rule_type.value} rule found for IP {ip_address}")

            logger.info(f"IP rule removed: {rule_type} for {ip_address} by {admin_user.email}")

            return {
                "status": "success",
                "message": f"Rule removed for IP {ip_address}",
                "ip_address": ip_address,
                "rule_type": rule_type.value
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove IP rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove IP rule")


@router.post("/rules/{ip_address}/unban")
def unban_ip(
    ip_address: str,
    logger: LoggerDep,
    admin_user: User = Depends(require_admin)
):
    """
    Manually unban an IP address (removes auto-ban and blacklist)

    Requires admin role.
    """
    try:
        with SessionLocal() as session:
            ip_repo = IPAccessRepository(session)

            # Remove auto-ban rule
            auto_ban_removed = ip_repo.remove_ip_rule(ip=ip_address, rule_type=IPRuleType.auto_banned)

            # Remove blacklist rule
            blacklist_removed = ip_repo.remove_ip_rule(ip=ip_address, rule_type=IPRuleType.blacklist)

            if not auto_ban_removed and not blacklist_removed:
                raise HTTPException(status_code=404, detail=f"No ban found for IP {ip_address}")

            logger.info(f"IP unbanned: {ip_address} by {admin_user.email}")

            return {
                "status": "success",
                "message": f"IP {ip_address} has been unbanned",
                "ip_address": ip_address,
                "auto_ban_removed": auto_ban_removed,
                "blacklist_removed": blacklist_removed
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unban IP: {e}")
        raise HTTPException(status_code=500, detail="Failed to unban IP")


@router.get("/violations", response_model=List[RateLimitViolationResponse])
def list_rate_violations(
    limit: int = Query(100, description="Maximum violations to return", ge=1, le=500),
    ip_address: Optional[str] = Query(None, description="Filter by IP address"),
    logger: LoggerDep,
    admin_user: User = Depends(require_admin)
):
    """
    List recent rate limit violations

    Requires admin role.
    """
    try:
        with SessionLocal() as session:
            from sqlalchemy import select, desc

            stmt = select(RateLimitViolation).order_by(desc(RateLimitViolation.last_violation_at))

            if ip_address:
                stmt = stmt.where(RateLimitViolation.ip_address == ip_address)

            stmt = stmt.limit(limit)

            violations = session.execute(stmt).scalars().all()

            return [
                RateLimitViolationResponse(
                    id=str(v.id),
                    ip_address=v.ip_address,
                    endpoint=v.endpoint,
                    violation_count=v.violation_count,
                    last_violation_at=v.last_violation_at,
                    auto_banned=v.auto_banned
                )
                for v in violations
            ]

    except Exception as e:
        logger.error(f"Failed to list violations: {e}")
        raise HTTPException(status_code=500, detail="Failed to list violations")


@router.get("/check/{ip_address}")
def check_ip_status(
    ip_address: str,
    logger: LoggerDep,
    admin_user: User = Depends(require_admin)
):
    """
    Check IP access status

    Requires admin role.
    """
    try:
        with SessionLocal() as session:
            ip_repo = IPAccessRepository(session)

            is_whitelisted = ip_repo.is_ip_whitelisted(ip_address)
            is_blacklisted = ip_repo.is_ip_blacklisted(ip_address)
            is_auto_banned = ip_repo.is_ip_auto_banned(ip_address)
            violations_count = ip_repo.get_violations_count(ip_address, time_window=3600)

            # Get active rule if exists
            rule = ip_repo.get_rule_by_ip(ip_address)

            return {
                "ip_address": ip_address,
                "is_whitelisted": is_whitelisted,
                "is_blacklisted": is_blacklisted,
                "is_auto_banned": is_auto_banned,
                "violations_last_hour": violations_count,
                "active_rule": {
                    "id": str(rule.id),
                    "rule_type": rule.rule_type.value,
                    "reason": rule.reason,
                    "expires_at": rule.expires_at.isoformat() if rule.expires_at else None,
                    "created_by": rule.created_by
                } if rule else None,
                "access_allowed": is_whitelisted or (not is_blacklisted and not is_auto_banned)
            }

    except Exception as e:
        logger.error(f"Failed to check IP status: {e}")
        raise HTTPException(status_code=500, detail="Failed to check IP status")
