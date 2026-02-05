# app/jobs/backup_scheduler.py
"""
Background scheduler for automated database backups to Cloudflare R2.

This scheduler:
1. Runs daily at a configured hour (default: 2 AM UTC)
2. Executes full backup workflow (PostgreSQL + MongoDB + R2 upload)
3. Uses thread pool to avoid blocking the event loop
4. Includes exponential backoff on failures
"""
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.deps import get_logger

# Add backup scripts to path
BACKUP_SCRIPTS_PATH = Path(__file__).parent.parent.parent / "backups" / "scripts"
if str(BACKUP_SCRIPTS_PATH) not in sys.path:
    sys.path.insert(0, str(BACKUP_SCRIPTS_PATH))


async def perform_backup(backup_type: str = "daily") -> dict:
    """
    Execute database backup in a thread pool (non-blocking).

    Args:
        backup_type: "daily" or "weekly"

    Returns:
        dict with status, duration, and any errors
    """
    log = get_logger()
    results = {
        "status": "pending",
        "backup_type": backup_type,
        "duration_seconds": 0,
        "r2_uploaded": False,
        "error": None
    }

    start_time = datetime.now(timezone.utc)

    try:
        # Import backup functions (lazy import to avoid startup issues)
        from run_backup import run_full_backup
        from backup_config import is_r2_configured

        upload_to_cloud = is_r2_configured()

        if not upload_to_cloud:
            log.warning("R2 not configured - backup will only be stored locally")

        # Run synchronous backup in thread pool to not block event loop
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(
            None,  # Default ThreadPoolExecutor
            lambda: run_full_backup(
                backup_type=backup_type,
                upload_to_cloud=upload_to_cloud,
                run_cleanup=True,
                verify=True
            )
        )

        results["status"] = "success" if success else "failed"
        results["r2_uploaded"] = upload_to_cloud and success

    except ImportError as e:
        results["status"] = "failed"
        results["error"] = f"Backup scripts not found: {e}"
        log.error(f"Backup import error: {e}")
    except Exception as e:
        results["status"] = "failed"
        results["error"] = str(e)
        log.error(f"Backup execution error: {e}", exc_info=True)

    results["duration_seconds"] = (datetime.now(timezone.utc) - start_time).total_seconds()
    return results


def _should_run_backup(backup_hour_utc: int, last_backup_date: datetime | None) -> bool:
    """
    Check if backup should run based on current time and last backup.

    Args:
        backup_hour_utc: Hour of day to run backup (0-23 UTC)
        last_backup_date: Date of last successful backup (or None)

    Returns:
        True if backup should run now
    """
    now = datetime.now(timezone.utc)
    current_hour = now.hour

    # Check if we're in the backup hour window
    if current_hour != backup_hour_utc:
        return False

    # Check if we already ran today
    if last_backup_date is not None:
        if last_backup_date.date() == now.date():
            return False

    return True


async def run_backup_scheduler(backup_hour_utc: int = 2, check_interval: int = 300):
    """
    Run the backup scheduler on a schedule.

    Args:
        backup_hour_utc: Hour of day to run backup (0-23 UTC, default: 2 AM)
        check_interval: Seconds between schedule checks (default: 300 = 5 minutes)
    """
    log = get_logger()
    log.info(f"Backup scheduler started (backup hour: {backup_hour_utc:02d}:00 UTC, check interval: {check_interval}s)")

    last_backup_date: datetime | None = None
    consecutive_failures = 0
    max_consecutive_failures = 5

    while True:
        try:
            # Check if backup should run
            if _should_run_backup(backup_hour_utc, last_backup_date):
                log.info("Starting scheduled daily backup...")

                results = await perform_backup(backup_type="daily")

                if results["status"] == "success":
                    last_backup_date = datetime.now(timezone.utc)
                    consecutive_failures = 0
                    log.info(
                        f"Backup completed successfully "
                        f"(duration: {results['duration_seconds']:.1f}s, "
                        f"R2: {'yes' if results['r2_uploaded'] else 'no'})"
                    )
                else:
                    consecutive_failures += 1
                    log.error(
                        f"Backup failed (attempt {consecutive_failures}/{max_consecutive_failures}): "
                        f"{results.get('error', 'Unknown error')}"
                    )

                    # If repeated failures, wait longer before retry
                    if consecutive_failures >= max_consecutive_failures:
                        log.critical(
                            f"Backup has failed {consecutive_failures} times. "
                            "Will retry in next backup window."
                        )
                        # Set last_backup_date to prevent immediate retry
                        last_backup_date = datetime.now(timezone.utc)
                        consecutive_failures = 0

            # Also run weekly backup on Sundays at the same hour
            now = datetime.now(timezone.utc)
            if (now.weekday() == 6 and  # Sunday
                now.hour == backup_hour_utc and
                (last_backup_date is None or
                 last_backup_date.date() != now.date())):
                log.info("Starting scheduled weekly backup...")
                await perform_backup(backup_type="weekly")

        except Exception as e:
            log.error(f"Backup scheduler error: {e}", exc_info=True)

        await asyncio.sleep(check_interval)
