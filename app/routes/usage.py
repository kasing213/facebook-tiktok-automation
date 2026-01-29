"""Usage limits and billing information endpoints"""
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import get_current_user
from app.core.models import User
from app.core.usage_limits import get_tenant_usage_limits, check_and_notify_usage_warnings

router = APIRouter(prefix="/api/usage", tags=["usage"])


@router.get("/limits")
async def get_usage_limits(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get current usage limits and counters for the tenant"""
    return get_tenant_usage_limits(current_user.tenant_id, db)


@router.get("/warnings")
async def check_usage_warnings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Check if tenant is approaching usage limits and return warnings"""
    warnings = await check_and_notify_usage_warnings(current_user.tenant_id, db)
    return warnings or {"warnings": []}


@router.get("/dashboard")
async def get_usage_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get comprehensive usage dashboard data"""
    from sqlalchemy import text

    # Get basic limits
    limits_data = get_tenant_usage_limits(current_user.tenant_id, db)

    # Get additional usage counts
    result = db.execute(text("""
        SELECT
            -- Product count
            (SELECT COUNT(*) FROM inventory.products
             WHERE tenant_id = :tenant_id AND is_active = true) as product_count,

            -- Customer count
            (SELECT COUNT(*) FROM invoice.customer
             WHERE tenant_id = :tenant_id) as customer_count,

            -- Team member count
            (SELECT COUNT(*) FROM "user"
             WHERE tenant_id = :tenant_id AND is_active = true) as team_member_count,

            -- This month stats
            (SELECT COUNT(*) FROM invoice.invoice
             WHERE tenant_id = :tenant_id
               AND created_at >= DATE_TRUNC('month', NOW())) as invoices_this_month_alt
    """), {"tenant_id": current_user.tenant_id})

    counts = result.fetchone()

    # Add current usage counts
    limits_data["current_counts"] = {
        "products": counts.product_count,
        "customers": counts.customer_count,
        "team_members": counts.team_member_count,
        "invoices_this_month": counts.invoices_this_month_alt
    }

    # Calculate usage percentages
    limits = limits_data["limits"]
    current = limits_data["current_usage"]
    counts = limits_data["current_counts"]

    limits_data["usage_percentages"] = {
        "invoices": round((current["invoices"] / limits["invoice"]) * 100, 1),
        "exports": round((current["exports"] / 20) * 100, 1) if limits_data["subscription_tier"] == "free" else 0,
        "products": round((counts["products"] / limits["product"]) * 100, 1),
        "customers": round((counts["customers"] / limits["customer"]) * 100, 1),
        "team_members": round((counts["team_members"] / limits["team_member"]) * 100, 1),
        "storage": round((current["storage_mb"] / limits["storage_mb"]) * 100, 1)
    }

    # Check for warnings
    warnings = await check_and_notify_usage_warnings(current_user.tenant_id, db)
    limits_data["has_warnings"] = bool(warnings)

    return limits_data