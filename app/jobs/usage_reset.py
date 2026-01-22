"""Monthly usage counter reset job

Resets monthly usage counters for all tenants on the 1st of each month.
This job should be scheduled to run via cron at midnight on the 1st of each month.
"""
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db_session

logger = logging.getLogger(__name__)


def reset_monthly_usage() -> None:
    """Reset monthly usage counters for all tenants on the 1st of each month."""

    logger.info("Starting monthly usage counter reset...")

    with get_db_session() as db:
        try:
            # Get current time in UTC
            now = datetime.now(timezone.utc)
            current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            # Reset counters for tenants that haven't been reset this month
            result = db.execute(text("""
                UPDATE tenant
                SET current_month_invoices = 0,
                    current_month_exports = 0,
                    current_month_promotions = 0,
                    current_month_broadcasts = 0,
                    current_month_reset_at = :reset_time
                WHERE current_month_reset_at IS NULL
                   OR current_month_reset_at < :current_month_start
                RETURNING id, name
            """), {
                "reset_time": now,
                "current_month_start": current_month_start
            })

            reset_tenants = result.fetchall()

            if reset_tenants:
                tenant_count = len(reset_tenants)
                logger.info(f"✅ Monthly usage reset completed for {tenant_count} tenants:")
                for tenant in reset_tenants:
                    logger.info(f"  - {tenant.name} ({tenant.id})")
            else:
                logger.info("ℹ️ No tenants needed usage reset (already reset this month)")

            # Optional: Log current usage statistics
            stats_result = db.execute(text("""
                SELECT
                    COUNT(*) as total_tenants,
                    SUM(current_month_invoices) as total_invoices,
                    SUM(current_month_exports) as total_exports,
                    AVG(current_month_invoices) as avg_invoices_per_tenant,
                    MAX(current_month_invoices) as max_invoices_per_tenant
                FROM tenant
                WHERE is_active = true
            """))

            stats = stats_result.fetchone()
            if stats:
                logger.info(f"📊 Post-reset usage statistics:")
                logger.info(f"  - Active tenants: {stats.total_tenants}")
                logger.info(f"  - Total invoices this month: {stats.total_invoices}")
                logger.info(f"  - Total exports this month: {stats.total_exports}")
                logger.info(f"  - Average invoices per tenant: {stats.avg_invoices_per_tenant:.1f}")
                logger.info(f"  - Highest usage tenant: {stats.max_invoices_per_tenant} invoices")

        except Exception as e:
            logger.error(f"❌ Failed to reset monthly usage counters: {e}")
            db.rollback()
            raise
        else:
            db.commit()
            logger.info("✅ Monthly usage counter reset completed successfully")


def get_tenants_approaching_limits() -> list:
    """Get list of tenants approaching their usage limits (80%+)"""

    with get_db_session() as db:
        result = db.execute(text("""
            SELECT
                t.id,
                t.name,
                t.current_month_invoices,
                t.invoice_limit,
                t.current_month_exports,
                (t.current_month_invoices::float / t.invoice_limit * 100) as invoice_usage_percent,
                (t.current_month_exports::float / 20 * 100) as export_usage_percent
            FROM tenant t
            WHERE t.is_active = true
              AND (
                  t.current_month_invoices >= (t.invoice_limit * 0.8)
                  OR t.current_month_exports >= (20 * 0.8)
              )
            ORDER BY invoice_usage_percent DESC
        """))

        tenants = []
        for row in result.fetchall():
            tenant_data = {
                "id": row.id,
                "name": row.name,
                "invoice_usage": {
                    "current": row.current_month_invoices,
                    "limit": row.invoice_limit,
                    "percentage": round(row.invoice_usage_percent, 1)
                },
                "export_usage": {
                    "current": row.current_month_exports,
                    "limit": 20,  # Free tier export limit
                    "percentage": round(row.export_usage_percent, 1)
                }
            }
            tenants.append(tenant_data)

        return tenants


def send_usage_warnings() -> None:
    """Send Telegram notifications to tenants approaching limits"""

    tenants_at_risk = get_tenants_approaching_limits()

    if not tenants_at_risk:
        logger.info("ℹ️ No tenants approaching usage limits")
        return

    logger.info(f"📢 Sending usage warnings to {len(tenants_at_risk)} tenants")

    for tenant in tenants_at_risk:
        try:
            # Get tenant owner's Telegram ID
            with get_db_session() as db:
                result = db.execute(text("""
                    SELECT telegram_user_id, email
                    FROM "user"
                    WHERE tenant_id = :tenant_id
                      AND role = 'admin'
                      AND is_active = true
                      AND telegram_user_id IS NOT NULL
                    LIMIT 1
                """), {"tenant_id": tenant["id"]})

                owner = result.fetchone()
                if not owner or not owner.telegram_user_id:
                    logger.warning(f"No Telegram ID for tenant {tenant['name']} - skipping warning")
                    continue

            # Format warning message
            warnings = []
            invoice_usage = tenant["invoice_usage"]
            export_usage = tenant["export_usage"]

            if invoice_usage["percentage"] >= 80:
                warnings.append(f"📄 Invoices: {invoice_usage['current']}/{invoice_usage['limit']} ({invoice_usage['percentage']}%)")

            if export_usage["percentage"] >= 80:
                warnings.append(f"📤 Exports: {export_usage['current']}/{export_usage['limit']} ({export_usage['percentage']}%)")

            message = (
                f"⚠️ <b>Usage Alert</b>\n\n"
                f"Hi {tenant['name']},\n\n"
                f"You're approaching your monthly limits:\n\n"
                + "\n".join(warnings) +
                "\n\n💡 Upgrade to Pro for unlimited usage:\n"
                "/upgrade"
            )

            # TODO: Send via Telegram bot
            logger.info(f"📤 Would send warning to {tenant['name']}: {message[:100]}...")

        except Exception as e:
            logger.error(f"❌ Failed to send warning to {tenant['name']}: {e}")


if __name__ == "__main__":
    # Can be run directly for testing
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--warnings":
        send_usage_warnings()
    else:
        reset_monthly_usage()