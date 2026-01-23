# app/jobs/subscription_trial_checker.py
"""Background scheduler for subscription trial expiration checks."""
import asyncio
from datetime import datetime, timezone

from app.core.db import get_db_session
from app.deps import get_logger
from app.core.models import Subscription, SubscriptionTier, SubscriptionStatus


async def process_expired_trials() -> dict:
    """
    Process all subscriptions with expired trials.
    Downgrades them from Pro to Free tier.
    Returns a summary of processed subscriptions.
    """
    log = get_logger()
    results = {
        "processed": 0,
        "downgraded": 0,
        "errors": []
    }

    try:
        with get_db_session() as db:
            now = datetime.now(timezone.utc)

            # Find all trial subscriptions that have expired
            expired_trials = db.query(Subscription).filter(
                Subscription.is_trial == True,
                Subscription.trial_ends_at <= now,
                Subscription.tier != SubscriptionTier.free  # Not already downgraded
            ).all()

            if not expired_trials:
                log.debug("No expired trials found")
                return results

            log.info(f"Found {len(expired_trials)} expired trial subscriptions")

            for subscription in expired_trials:
                try:
                    results["processed"] += 1

                    # Downgrade to Free tier
                    subscription.tier = SubscriptionTier.free
                    subscription.is_trial = False
                    subscription.status = None  # Free tier has no status

                    results["downgraded"] += 1
                    log.info(f"Downgraded subscription {subscription.id} (user: {subscription.user_id}) to Free tier")

                except Exception as e:
                    error_msg = f"Error downgrading subscription {subscription.id}: {str(e)}"
                    results["errors"].append(error_msg)
                    log.error(error_msg)

            # Commit all changes
            db.commit()

    except Exception as e:
        error_msg = f"Error processing expired trials: {str(e)}"
        results["errors"].append(error_msg)
        log.error(error_msg)

    return results


async def run_trial_checker_scheduler(check_interval: int = 3600):
    """
    Run the trial checker on a schedule.

    Args:
        check_interval: Seconds between checks (default: 3600 = 1 hour)
    """
    log = get_logger()
    log.info(f"Trial checker scheduler started (interval: {check_interval}s)")

    while True:
        try:
            results = await process_expired_trials()

            if results["downgraded"] > 0:
                log.info(
                    f"Trial checker: Processed {results['processed']}, "
                    f"Downgraded {results['downgraded']}"
                )
            elif results["errors"]:
                log.warning(f"Trial checker completed with errors: {results['errors']}")

        except Exception as e:
            log.error(f"Trial checker error: {e}")

        await asyncio.sleep(check_interval)
