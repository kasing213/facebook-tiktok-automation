# api-gateway/src/services/pro_reward_service.py
"""Pro subscription reward service for early payment incentives."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import text

from src.db.postgres import get_db_session

logger = logging.getLogger(__name__)


class ProRewardService:
    """Service for managing Pro subscription rewards."""

    async def grant_free_pro_month(
        self,
        user_id: str,
        tenant_id: str,
        invoice_id: str
    ) -> Dict[str, Any]:
        """Grant 1 month of free Pro subscription for early payment."""
        try:
            with get_db_session() as db:
                # Check if user already has a subscription
                result = db.execute(
                    text("""
                        SELECT id, tier, status, current_period_end, is_trial, trial_ends_at
                        FROM public.subscription
                        WHERE user_id = :user_id
                    """),
                    {"user_id": user_id}
                )
                subscription = result.fetchone()

                # Calculate new Pro end date (1 month from now or extend current)
                if subscription and subscription.current_period_end:
                    # Extend existing subscription by 1 month
                    current_end = subscription.current_period_end
                    new_end_date = current_end + timedelta(days=30)
                else:
                    # New Pro subscription for 1 month
                    new_end_date = datetime.utcnow() + timedelta(days=30)

                if subscription:
                    # Update existing subscription
                    db.execute(
                        text("""
                            UPDATE public.subscription
                            SET tier = 'pro',
                                status = 'active',
                                current_period_end = :new_end_date,
                                updated_at = NOW()
                            WHERE user_id = :user_id
                        """),
                        {
                            "user_id": user_id,
                            "new_end_date": new_end_date
                        }
                    )
                    action = "extended"
                else:
                    # Create new Pro subscription
                    db.execute(
                        text("""
                            INSERT INTO public.subscription (
                                user_id, tenant_id, tier, status,
                                current_period_start, current_period_end
                            )
                            VALUES (
                                :user_id, :tenant_id, 'pro', 'active',
                                NOW(), :new_end_date
                            )
                        """),
                        {
                            "user_id": user_id,
                            "tenant_id": tenant_id,
                            "new_end_date": new_end_date
                        }
                    )
                    action = "granted"

                # Mark the Pro reward as granted in the invoice
                db.execute(
                    text("""
                        UPDATE invoice.invoice
                        SET pro_reward_granted = TRUE,
                            pro_reward_granted_at = NOW(),
                            updated_at = NOW()
                        WHERE id = :invoice_id
                    """),
                    {"invoice_id": invoice_id}
                )

                db.commit()

                return {
                    "success": True,
                    "action": action,
                    "message": f"Free Pro month {action} successfully",
                    "pro_end_date": new_end_date.isoformat(),
                    "benefits": [
                        "Custom branding",
                        "API access",
                        "Priority support",
                        "Unlimited invoices",
                        "Team collaboration",
                        "Advanced reports",
                        "Bulk operations",
                        "Social automation",
                        "Ads alerts"
                    ]
                }

        except Exception as e:
            logger.error(f"Error granting free Pro month: {e}")
            return {
                "success": False,
                "message": f"Error granting Pro reward: {str(e)}"
            }

    async def check_pro_reward_eligibility(
        self,
        invoice_id: str
    ) -> Dict[str, Any]:
        """Check if invoice is eligible for Pro reward (not already granted)."""
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        SELECT pro_reward_granted, pro_reward_granted_at,
                               early_payment_enabled, customer_id, tenant_id
                        FROM invoice.invoice
                        WHERE id = :invoice_id
                    """),
                    {"invoice_id": invoice_id}
                )
                invoice = result.fetchone()

                if not invoice:
                    return {"eligible": False, "reason": "Invoice not found"}

                if invoice.pro_reward_granted:
                    return {
                        "eligible": False,
                        "reason": f"Pro reward already granted on {invoice.pro_reward_granted_at}"
                    }

                if not invoice.early_payment_enabled:
                    return {
                        "eligible": False,
                        "reason": "Early payment discount not enabled on this invoice"
                    }

                return {
                    "eligible": True,
                    "customer_id": str(invoice.customer_id),
                    "tenant_id": str(invoice.tenant_id)
                }

        except Exception as e:
            logger.error(f"Error checking Pro reward eligibility: {e}")
            return {"eligible": False, "reason": f"Error: {str(e)}"}

    async def get_customer_user_id(
        self,
        customer_id: str,
        tenant_id: str
    ) -> Optional[str]:
        """Get user ID associated with customer for Pro reward."""
        try:
            with get_db_session() as db:
                # Try to find user through customer metadata or linked accounts
                result = db.execute(
                    text("""
                        SELECT meta
                        FROM invoice.customer
                        WHERE id = :customer_id AND tenant_id = :tenant_id
                    """),
                    {"customer_id": customer_id, "tenant_id": tenant_id}
                )
                customer = result.fetchone()

                if customer and customer.meta:
                    # Check if user_id is stored in customer metadata
                    meta = customer.meta
                    if isinstance(meta, dict) and "user_id" in meta:
                        return meta["user_id"]

                # Fallback: look for linked Telegram users (if available)
                result = db.execute(
                    text("""
                        SELECT user_id
                        FROM public.telegram_user_link tul
                        JOIN invoice.customer c ON c.phone = tul.phone_number
                        WHERE c.id = :customer_id AND c.tenant_id = :tenant_id
                        LIMIT 1
                    """),
                    {"customer_id": customer_id, "tenant_id": tenant_id}
                )
                link = result.fetchone()

                if link:
                    return str(link.user_id)

                return None

        except Exception as e:
            logger.error(f"Error getting customer user ID: {e}")
            return None

    async def process_early_payment_rewards(
        self,
        invoice_id: str
    ) -> Dict[str, Any]:
        """Process complete early payment rewards (discount + Pro month)."""
        try:
            # Check eligibility for Pro reward
            eligibility = await self.check_pro_reward_eligibility(invoice_id)
            if not eligibility["eligible"]:
                return {"success": False, "message": eligibility["reason"]}

            # Get user ID for the customer
            user_id = await self.get_customer_user_id(
                eligibility["customer_id"],
                eligibility["tenant_id"]
            )

            if not user_id:
                # Still grant discount, but note Pro reward couldn't be granted
                return {
                    "success": True,
                    "discount_applied": True,
                    "pro_reward_granted": False,
                    "message": "Discount applied, but customer account not found for Pro reward"
                }

            # Grant the free Pro month
            pro_result = await self.grant_free_pro_month(
                user_id,
                eligibility["tenant_id"],
                invoice_id
            )

            if pro_result["success"]:
                return {
                    "success": True,
                    "discount_applied": True,
                    "pro_reward_granted": True,
                    "message": "Early payment benefits applied: 10% discount + Free Pro month!",
                    "pro_details": pro_result
                }
            else:
                return {
                    "success": True,
                    "discount_applied": True,
                    "pro_reward_granted": False,
                    "message": f"Discount applied, but Pro reward failed: {pro_result['message']}"
                }

        except Exception as e:
            logger.error(f"Error processing early payment rewards: {e}")
            return {
                "success": False,
                "message": f"Error processing rewards: {str(e)}"
            }


# Global service instance
pro_reward_service = ProRewardService()