# app/routes/ip_management.py
"""
Admin endpoints for IP access control and rate limit management
"""
import ipaddress
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

from app.deps import LoggerDep
from app.routes.auth import get_current_user
from app.core.models import User, UserRole, IPRuleType, IPAccessRule, RateLimitViolation
from app.core.db import SessionLocal
from app.repositories.ip_access import IPAccessRepository
from app.core.exceptions import (
    IPAlreadyWhitelisted, IPAlreadyBlacklisted, IPRuleNotFound, IPNotBanned,
    InvalidIPAddress, IPRuleCreationFailed, AdminAccessRequired, DatabaseError
)


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


def validate_ip_address(ip_address: str) -> bool:
    """Validate IP address format (IPv4 or IPv6)"""
    try:
        ipaddress.ip_address(ip_address)
        return True
    except ValueError:
        return False


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require admin role"""
    if current_user.role != UserRole.admin:
        raise AdminAccessRequired(action="manage IP access rules")
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
    # Validate IP address format
    if not validate_ip_address(request.ip_address):
        logger.warning(f"Invalid IP address format attempted: {request.ip_address} by {admin_user.email}")
        raise InvalidIPAddress(ip_address=request.ip_address)

    try:
        with SessionLocal() as session:
            ip_repo = IPAccessRepository(session)

            # Check if rule already exists for this IP and type
            existing_rule = ip_repo.get_rule_by_ip(request.ip_address, request.rule_type)
            if existing_rule:
                if request.rule_type == IPRuleType.whitelist:
                    logger.info(f"IP {request.ip_address} already whitelisted - no action taken by {admin_user.email}")
                    raise IPAlreadyWhitelisted(ip_address=request.ip_address)
                elif request.rule_type == IPRuleType.blacklist:
                    logger.info(f"IP {request.ip_address} already blacklisted - no action taken by {admin_user.email}")
                    raise IPAlreadyBlacklisted(ip_address=request.ip_address)

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

            rule_action = "whitelisted" if request.rule_type == IPRuleType.whitelist else "blacklisted"
            logger.info(f"IP {request.ip_address} successfully {rule_action} by {admin_user.email}")

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

    except (IPAlreadyWhitelisted, IPAlreadyBlacklisted, InvalidIPAddress):
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error creating IP rule for {request.ip_address}: {str(e)}")
        raise IPRuleCreationFailed(ip_address=request.ip_address, reason="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error creating IP rule for {request.ip_address}: {str(e)}")
        raise IPRuleCreationFailed(ip_address=request.ip_address, reason="An unexpected error occurred")


@router.get("/rules", response_model=List[IPRuleResponse])
def list_ip_rules(
    logger: LoggerDep,
    admin_user: User = Depends(require_admin),
    rule_type: Optional[IPRuleType] = Query(None, description="Filter by rule type")
):
    """
    List all active IP access rules

    Requires admin role.
    """
    try:
        with SessionLocal() as session:
            ip_repo = IPAccessRepository(session)
            rules = ip_repo.get_active_rules(rule_type=rule_type)

            filter_desc = f" (filtered by {rule_type.value})" if rule_type else ""
            logger.info(f"Admin {admin_user.email} retrieved {len(rules)} IP rules{filter_desc}")

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

    except SQLAlchemyError as e:
        logger.error(f"Database error listing IP rules by {admin_user.email}: {str(e)}")
        raise DatabaseError(operation="retrieve IP access rules")
    except Exception as e:
        logger.error(f"Unexpected error listing IP rules by {admin_user.email}: {str(e)}")
        raise DatabaseError(operation="retrieve IP access rules")


@router.delete("/rules/{ip_address}")
def remove_ip_rule(
    ip_address: str,
    logger: LoggerDep,
    admin_user: User = Depends(require_admin),
    rule_type: IPRuleType = Query(..., description="Rule type to remove")
):
    """
    Remove IP access rule

    Requires admin role.
    """
    # Validate IP address format
    if not validate_ip_address(ip_address):
        logger.warning(f"Invalid IP address format for removal: {ip_address} by {admin_user.email}")
        raise InvalidIPAddress(ip_address=ip_address)

    try:
        with SessionLocal() as session:
            ip_repo = IPAccessRepository(session)
            success = ip_repo.remove_ip_rule(ip=ip_address, rule_type=rule_type)

            if not success:
                logger.info(f"No {rule_type.value} rule found for IP {ip_address} - removal requested by {admin_user.email}")
                raise IPRuleNotFound(ip_address=ip_address, rule_type=rule_type.value)

            logger.info(f"IP rule removed: {rule_type.value} for {ip_address} by {admin_user.email}")

            return {
                "status": "success",
                "message": f"The {rule_type.value} rule for IP {ip_address} has been removed successfully.",
                "ip_address": ip_address,
                "rule_type": rule_type.value
            }

    except (InvalidIPAddress, IPRuleNotFound):
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error removing IP rule for {ip_address}: {str(e)}")
        raise DatabaseError(operation=f"remove the {rule_type.value} rule")
    except Exception as e:
        logger.error(f"Unexpected error removing IP rule for {ip_address}: {str(e)}")
        raise DatabaseError(operation=f"remove the {rule_type.value} rule")


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
    # Validate IP address format
    if not validate_ip_address(ip_address):
        logger.warning(f"Invalid IP address format for unban: {ip_address} by {admin_user.email}")
        raise InvalidIPAddress(ip_address=ip_address)

    try:
        with SessionLocal() as session:
            ip_repo = IPAccessRepository(session)

            # Remove auto-ban rule
            auto_ban_removed = ip_repo.remove_ip_rule(ip=ip_address, rule_type=IPRuleType.auto_banned)

            # Remove blacklist rule
            blacklist_removed = ip_repo.remove_ip_rule(ip=ip_address, rule_type=IPRuleType.blacklist)

            if not auto_ban_removed and not blacklist_removed:
                logger.info(f"IP {ip_address} was not banned - unban requested by {admin_user.email}")
                raise IPNotBanned(ip_address=ip_address)

            # Build descriptive message
            removed_types = []
            if auto_ban_removed:
                removed_types.append("automatic ban")
            if blacklist_removed:
                removed_types.append("blacklist entry")
            removed_desc = " and ".join(removed_types)

            logger.info(f"IP {ip_address} unbanned ({removed_desc}) by {admin_user.email}")

            return {
                "status": "success",
                "message": f"IP {ip_address} has been unbanned. Removed: {removed_desc}.",
                "ip_address": ip_address,
                "auto_ban_removed": auto_ban_removed,
                "blacklist_removed": blacklist_removed
            }

    except (InvalidIPAddress, IPNotBanned):
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error unbanning IP {ip_address}: {str(e)}")
        raise DatabaseError(operation=f"unban IP {ip_address}")
    except Exception as e:
        logger.error(f"Unexpected error unbanning IP {ip_address}: {str(e)}")
        raise DatabaseError(operation=f"unban IP {ip_address}")


@router.get("/violations", response_model=List[RateLimitViolationResponse])
def list_rate_violations(
    logger: LoggerDep,
    admin_user: User = Depends(require_admin),
    limit: int = Query(100, description="Maximum violations to return", ge=1, le=500),
    ip_address: Optional[str] = Query(None, description="Filter by IP address")
):
    """
    List recent rate limit violations

    Requires admin role.
    """
    # Validate IP address format if provided
    if ip_address and not validate_ip_address(ip_address):
        logger.warning(f"Invalid IP address format for violations query: {ip_address} by {admin_user.email}")
        raise InvalidIPAddress(ip_address=ip_address)

    try:
        with SessionLocal() as session:
            from sqlalchemy import select, desc

            stmt = select(RateLimitViolation).order_by(desc(RateLimitViolation.last_violation_at))

            if ip_address:
                stmt = stmt.where(RateLimitViolation.ip_address == ip_address)

            stmt = stmt.limit(limit)

            violations = session.execute(stmt).scalars().all()

            filter_desc = f" for IP {ip_address}" if ip_address else ""
            logger.info(f"Admin {admin_user.email} retrieved {len(violations)} rate limit violations{filter_desc}")

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

    except InvalidIPAddress:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error listing rate violations by {admin_user.email}: {str(e)}")
        raise DatabaseError(operation="retrieve rate limit violations")
    except Exception as e:
        logger.error(f"Unexpected error listing rate violations by {admin_user.email}: {str(e)}")
        raise DatabaseError(operation="retrieve rate limit violations")


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
    # Validate IP address format
    if not validate_ip_address(ip_address):
        logger.warning(f"Invalid IP address format for status check: {ip_address} by {admin_user.email}")
        raise InvalidIPAddress(ip_address=ip_address)

    try:
        with SessionLocal() as session:
            ip_repo = IPAccessRepository(session)

            is_whitelisted = ip_repo.is_ip_whitelisted(ip_address)
            is_blacklisted = ip_repo.is_ip_blacklisted(ip_address)
            is_auto_banned = ip_repo.is_ip_auto_banned(ip_address)
            violations_count = ip_repo.get_violations_count(ip_address, time_window=3600)

            # Get active rule if exists
            rule = ip_repo.get_rule_by_ip(ip_address)

            access_allowed = is_whitelisted or (not is_blacklisted and not is_auto_banned)
            status_desc = "allowed" if access_allowed else "blocked"
            logger.info(f"Admin {admin_user.email} checked IP {ip_address} status: {status_desc}")

            # Build human-readable status message
            if is_whitelisted:
                status_message = f"IP {ip_address} is whitelisted and has full access."
            elif is_auto_banned:
                status_message = f"IP {ip_address} is automatically banned due to rate limit violations."
            elif is_blacklisted:
                status_message = f"IP {ip_address} is blacklisted and access is denied."
            else:
                status_message = f"IP {ip_address} has normal access with no special rules."

            return {
                "ip_address": ip_address,
                "status_message": status_message,
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
                "access_allowed": access_allowed
            }

    except InvalidIPAddress:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error checking IP status for {ip_address}: {str(e)}")
        raise DatabaseError(operation=f"check status for IP {ip_address}")
    except Exception as e:
        logger.error(f"Unexpected error checking IP status for {ip_address}: {str(e)}")
        raise DatabaseError(operation=f"check status for IP {ip_address}")
