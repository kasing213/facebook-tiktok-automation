# app/jobs/ads_alert_scheduler.py
"""Background scheduler for ads_alert scheduled promotions"""
import asyncio
from datetime import datetime, timezone
from typing import Optional

from app.core.db import get_db_session
from app.deps import get_logger
from app.repositories.ads_alert import AdsAlertPromotionRepository, AdsAlertChatRepository
from app.services.ads_alert_service import AdsAlertService
from app.core.models import PromotionStatus


async def process_scheduled_promotions() -> dict:
    """
    Process all promotions that are due to be sent.
    Returns a summary of processed promotions.
    """
    log = get_logger()
    results = {
        "processed": 0,
        "success": 0,
        "failed": 0,
        "errors": []
    }

    try:
        with get_db_session() as db:
            promo_repo = AdsAlertPromotionRepository(db)
            chat_repo = AdsAlertChatRepository(db)

            # Get all promotions due to be sent
            due_promotions = promo_repo.get_due_promotions()

            if not due_promotions:
                log.debug("No scheduled promotions due")
                return results

            # Log tenant breakdown for audit trail
            tenant_counts = {}
            for p in due_promotions:
                tid = str(p.tenant_id)[:8]  # First 8 chars for brevity
                tenant_counts[tid] = tenant_counts.get(tid, 0) + 1
            log.info(
                f"Found {len(due_promotions)} scheduled promotions due for sending. "
                f"Tenants: {tenant_counts}"
            )

            for promotion in due_promotions:
                try:
                    results["processed"] += 1

                    # Get target chats
                    if promotion.target_type.value == "all":
                        chats = chat_repo.get_by_tenant(
                            promotion.tenant_id,
                            subscribed_only=True,
                            active_only=True
                        )
                    else:
                        # Get specific chats
                        chats = []
                        for chat_id in promotion.target_chat_ids or []:
                            chat = chat_repo.get_by_id_and_tenant(chat_id, promotion.tenant_id)
                            if chat and chat.subscribed and chat.is_active:
                                chats.append(chat)

                    if not chats:
                        log.warning(f"Promotion {promotion.id}: No target chats found")
                        promo_repo.update_by_tenant(
                            promotion.id,
                            promotion.tenant_id,
                            status=PromotionStatus.cancelled
                        )
                        continue

                    # Send the promotion
                    service = AdsAlertService(db)
                    result = await service.send_promotion(
                        promotion_id=promotion.id,
                        tenant_id=promotion.tenant_id
                    )

                    if result.get("sent", 0) > 0:
                        results["success"] += 1
                        log.info(
                            f"Promotion {promotion.id} sent: "
                            f"{result['sent']}/{result['total']} successful"
                        )
                    else:
                        results["failed"] += 1
                        log.warning(f"Promotion {promotion.id} failed: No messages sent")

                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(str(e))
                    log.error(f"Error processing promotion {promotion.id}: {e}")

    except Exception as e:
        log.error(f"Error in process_scheduled_promotions: {e}")
        results["errors"].append(str(e))

    return results


async def run_ads_alert_scheduler(check_interval: int = 60):
    """
    Run the ads_alert scheduler loop.

    Args:
        check_interval: Seconds between each check for due promotions
    """
    log = get_logger()
    log.info(f"Starting ads_alert scheduler (check interval: {check_interval}s)")

    while True:
        try:
            results = await process_scheduled_promotions()

            if results["processed"] > 0:
                log.info(
                    f"Ads Alert Scheduler: Processed {results['processed']} promotions "
                    f"({results['success']} success, {results['failed']} failed)"
                )

        except Exception as e:
            log.error(f"Error in ads_alert scheduler loop: {e}")

        # Wait before next check
        await asyncio.sleep(check_interval)
