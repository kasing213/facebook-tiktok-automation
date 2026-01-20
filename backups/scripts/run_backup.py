"""
Main Backup Runner
==================
Entry point for running backups. Can be scheduled via cron or Windows Task Scheduler.
Orchestrates database backup, cloud upload, and cleanup.
"""

import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from backup_config import (
    LOG_CONFIG,
    NOTIFICATION_CONFIG,
    is_r2_configured,
    is_mongodb_configured,
    validate_config,
)
from backup_database import run_backup, verify_backup
from backup_mongodb import run_backup as run_mongodb_backup, verify_backup as verify_mongodb_backup
from cleanup_backups import cleanup_all

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format=LOG_CONFIG["format"],
    handlers=[
        logging.FileHandler(LOG_CONFIG["file"]),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


def send_telegram_notification(message: str, success: bool = True) -> bool:
    """
    Send backup notification via Telegram.

    Args:
        message: Notification message
        success: Whether backup was successful

    Returns:
        True if notification sent
    """
    if not NOTIFICATION_CONFIG["telegram_enabled"]:
        return False

    try:
        import httpx

        token = NOTIFICATION_CONFIG["telegram_bot_token"]
        chat_id = NOTIFICATION_CONFIG["telegram_chat_id"]

        if not token or not chat_id:
            return False

        # Add emoji based on status
        emoji = "[OK]" if success else "[FAIL]"
        full_message = f"{emoji} *Backup Notification*\n\n{message}"

        response = httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": full_message,
                "parse_mode": "Markdown",
            },
            timeout=10
        )

        return response.status_code == 200

    except Exception as e:
        logger.warning(f"Failed to send Telegram notification: {e}")
        return False


def run_full_backup(
    backup_type: str = "daily",
    upload_to_cloud: bool = True,
    run_cleanup: bool = True,
    verify: bool = True
) -> bool:
    """
    Run complete backup workflow.

    Args:
        backup_type: "daily" or "weekly"
        upload_to_cloud: Upload to R2 after backup
        run_cleanup: Run cleanup after backup
        verify: Verify backup integrity

    Returns:
        True if all operations successful
    """
    start_time = datetime.now()
    mongodb_enabled = is_mongodb_configured()
    total_steps = 5 if mongodb_enabled else 4

    results = {
        "postgres_backup": False,
        "postgres_verify": False,
        "mongodb_backup": None,  # None = not configured
        "mongodb_verify": None,
        "upload": False,
        "cleanup": False,
    }

    logger.info("=" * 60)
    logger.info(f"BACKUP STARTED: {backup_type.upper()}")
    logger.info(f"Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"MongoDB: {'Enabled' if mongodb_enabled else 'Not configured'}")
    logger.info("=" * 60)

    # Validate configuration
    if not validate_config():
        logger.error("Configuration validation failed")
        return False

    backup_files = []  # Track all backup files for upload
    total_size = 0

    # Step 1: PostgreSQL database backup
    logger.info(f"\n[1/{total_steps}] Running PostgreSQL backup...")
    success, backup_path = run_backup(backup_type=backup_type)

    if not success or not backup_path:
        logger.error("PostgreSQL backup failed!")
        send_telegram_notification(
            f"PostgreSQL backup failed!\nType: {backup_type}\nTime: {start_time}",
            success=False
        )
        return False

    results["postgres_backup"] = True
    postgres_size = backup_path.stat().st_size / (1024 * 1024)
    total_size += postgres_size
    backup_files.append(("postgres", backup_path))
    logger.info(f"PostgreSQL backup created: {backup_path.name} ({postgres_size:.2f} MB)")

    # Step 1b: MongoDB backup (if configured)
    mongodb_path = None
    mongodb_size = 0
    if mongodb_enabled:
        logger.info(f"\n[2/{total_steps}] Running MongoDB backup...")
        try:
            mongo_success, mongodb_path = run_mongodb_backup(backup_type=backup_type)
            if mongo_success and mongodb_path:
                results["mongodb_backup"] = True
                mongodb_size = mongodb_path.stat().st_size / (1024 * 1024)
                total_size += mongodb_size
                backup_files.append(("mongodb", mongodb_path))
                logger.info(f"MongoDB backup created: {mongodb_path.name} ({mongodb_size:.2f} MB)")
            else:
                results["mongodb_backup"] = False
                logger.warning("MongoDB backup failed (continuing with PostgreSQL only)")
        except Exception as e:
            results["mongodb_backup"] = False
            logger.warning(f"MongoDB backup error: {e}")

    current_step = 3 if mongodb_enabled else 2

    # Step: Verify backups
    if verify:
        logger.info(f"\n[{current_step}/{total_steps}] Verifying backup integrity...")

        # Verify PostgreSQL
        if verify_backup(backup_path):
            results["postgres_verify"] = True
            logger.info("PostgreSQL verification passed")
        else:
            logger.warning("PostgreSQL verification failed (continuing anyway)")

        # Verify MongoDB
        if mongodb_enabled and mongodb_path:
            if verify_mongodb_backup(mongodb_path):
                results["mongodb_verify"] = True
                logger.info("MongoDB verification passed")
            else:
                results["mongodb_verify"] = False
                logger.warning("MongoDB verification failed (continuing anyway)")

        current_step += 1

    # Step: Upload to R2
    if upload_to_cloud and is_r2_configured():
        logger.info(f"\n[{current_step}/{total_steps}] Uploading to Cloudflare R2...")
        try:
            from upload_to_r2 import upload_file
            upload_success = True

            for db_type, file_path in backup_files:
                logger.info(f"  Uploading {db_type}: {file_path.name}...")
                if upload_file(file_path, backup_type=backup_type, db_type=db_type):
                    logger.info(f"    {db_type} upload completed")
                else:
                    logger.warning(f"    {db_type} upload failed")
                    upload_success = False

            results["upload"] = upload_success
            if upload_success:
                logger.info("All R2 uploads completed")
        except Exception as e:
            logger.warning(f"R2 upload error: {e}")
    else:
        logger.info(f"\n[{current_step}/{total_steps}] Skipping R2 upload (not configured)")
        results["upload"] = None  # Not applicable

    current_step += 1

    # Step: Cleanup old backups
    if run_cleanup:
        logger.info(f"\n[{current_step}/{total_steps}] Running cleanup...")
        try:
            cleanup_all()
            results["cleanup"] = True
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")

    # Summary
    duration = (datetime.now() - start_time).total_seconds()

    def status_str(val):
        if val is True:
            return "OK"
        elif val is False:
            return "FAIL"
        return "-"

    logger.info("\n" + "=" * 60)
    logger.info("BACKUP COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Type: {backup_type}")
    logger.info(f"PostgreSQL: {backup_path.name} ({postgres_size:.2f} MB)")
    if mongodb_enabled and mongodb_path:
        logger.info(f"MongoDB: {mongodb_path.name} ({mongodb_size:.2f} MB)")
    logger.info(f"Total Size: {total_size:.2f} MB")
    logger.info(f"Duration: {duration:.1f} seconds")
    logger.info(f"Results:")
    logger.info(f"  - PostgreSQL Backup: {status_str(results['postgres_backup'])}")
    logger.info(f"  - PostgreSQL Verify: {status_str(results['postgres_verify'])}")
    if mongodb_enabled:
        logger.info(f"  - MongoDB Backup: {status_str(results['mongodb_backup'])}")
        logger.info(f"  - MongoDB Verify: {status_str(results['mongodb_verify'])}")
    logger.info(f"  - R2 Upload: {status_str(results['upload'])}")
    logger.info(f"  - Cleanup: {status_str(results['cleanup'])}")
    logger.info("=" * 60)

    # Send notification
    mongo_info = ""
    if mongodb_enabled:
        mongo_status = "OK" if results['mongodb_backup'] else "FAIL"
        mongo_info = f"\nMongoDB: `{mongodb_path.name if mongodb_path else 'N/A'}` ({mongodb_size:.2f} MB) [{mongo_status}]"

    notification_msg = f"""*Backup Complete*
Type: {backup_type}
PostgreSQL: `{backup_path.name}` ({postgres_size:.2f} MB){mongo_info}
Total: {total_size:.2f} MB
Duration: {duration:.1f}s
R2 Upload: {'Yes' if results['upload'] else 'No'}"""

    send_telegram_notification(notification_msg, success=True)

    return results["postgres_backup"]


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Facebook Automation Backup System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_backup.py --type daily          # Daily backup with upload and cleanup
  python run_backup.py --type weekly         # Weekly backup
  python run_backup.py --type daily --no-upload  # Skip R2 upload
  python run_backup.py --type daily --no-cleanup # Skip cleanup
  python run_backup.py --status              # Show backup status
        """
    )

    parser.add_argument(
        "--type",
        choices=["daily", "weekly"],
        default="daily",
        help="Backup type (default: daily)"
    )
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Skip uploading to R2"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Skip cleanup of old backups"
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip backup verification"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show backup system status"
    )

    args = parser.parse_args()

    # Status mode
    if args.status:
        from backup_config import DATABASE_CONFIG, MONGODB_CONFIG, LOCAL_PATHS, R2_CONFIG

        print("\n" + "=" * 60)
        print("BACKUP SYSTEM STATUS")
        print("=" * 60)

        # PostgreSQL status
        print(f"\n[PostgreSQL]")
        print(f"  Host: {DATABASE_CONFIG['host']}")
        print(f"  Configured: {'Yes' if DATABASE_CONFIG['password'] else 'No (missing password)'}")

        # MongoDB status
        print(f"\n[MongoDB]")
        print(f"  Configured: {'Yes' if is_mongodb_configured() else 'No'}")
        if is_mongodb_configured():
            print(f"  Database: {MONGODB_CONFIG['database']}")

        # R2 status
        print(f"\n[Cloudflare R2]")
        print(f"  Configured: {'Yes' if is_r2_configured() else 'No'}")
        if is_r2_configured():
            print(f"  Bucket: {R2_CONFIG['bucket']}")

        print(f"\n[Local Backup Paths]")
        for name, path in LOCAL_PATHS.items():
            exists = "[OK]" if path.exists() else "[X]"
            print(f"  {exists} {name}: {path}")

        # Count PostgreSQL backups
        print(f"\n[PostgreSQL Backups]")
        for btype in ["daily", "weekly"]:
            path = LOCAL_PATHS[btype]
            if path.exists():
                count = len(list(path.glob("*.dump")))
                print(f"  {btype.title()}: {count} backup(s)")

        # Count MongoDB backups
        if is_mongodb_configured():
            print(f"\n[MongoDB Backups]")
            for btype in ["mongodb_daily", "mongodb_weekly"]:
                path = LOCAL_PATHS[btype]
                if path.exists():
                    count = len(list(path.glob("*.tar.gz")))
                    label = btype.replace("mongodb_", "").title()
                    print(f"  {label}: {count} backup(s)")

        print("\n" + "=" * 60)
        sys.exit(0)

    # Run backup
    success = run_full_backup(
        backup_type=args.type,
        upload_to_cloud=not args.no_upload,
        run_cleanup=not args.no_cleanup,
        verify=not args.no_verify
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
