"""
Backup Cleanup Script
=====================
Enforces retention policy by deleting old backups.
Cleans both local backups and R2 cloud backups.
"""

import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple

from backup_config import (
    LOCAL_PATHS,
    RETENTION_POLICY,
    LOG_CONFIG,
    is_r2_configured,
)

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


def get_backup_files(backup_dir: Path) -> List[Tuple[Path, datetime]]:
    """
    Get all backup files in a directory with their modification times.

    Args:
        backup_dir: Directory to scan

    Returns:
        List of (path, mtime) tuples sorted by mtime (newest first)
    """
    if not backup_dir.exists():
        return []

    backups = []
    for f in backup_dir.glob("*.dump"):
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        backups.append((f, mtime))

    return sorted(backups, key=lambda x: x[1], reverse=True)


def cleanup_local_backups(
    backup_type: str,
    retention_days: int,
    dry_run: bool = False
) -> int:
    """
    Delete local backups older than retention period.

    Args:
        backup_type: "daily" or "weekly"
        retention_days: Keep backups newer than this many days
        dry_run: If True, only show what would be deleted

    Returns:
        Number of backups deleted
    """
    backup_dir = LOCAL_PATHS.get(backup_type)
    if not backup_dir:
        logger.error(f"Unknown backup type: {backup_type}")
        return 0

    cutoff_date = datetime.now() - timedelta(days=retention_days)
    backups = get_backup_files(backup_dir)

    if not backups:
        logger.info(f"No {backup_type} backups found")
        return 0

    logger.info(f"Scanning {backup_type} backups (retention: {retention_days} days)")
    logger.info(f"Cutoff date: {cutoff_date.strftime('%Y-%m-%d %H:%M')}")

    deleted = 0
    kept = 0
    freed_bytes = 0

    for backup_path, mtime in backups:
        if mtime < cutoff_date:
            size = backup_path.stat().st_size
            if dry_run:
                logger.info(f"[DRY RUN] Would delete: {backup_path.name} ({mtime.strftime('%Y-%m-%d')})")
            else:
                try:
                    backup_path.unlink()
                    logger.info(f"Deleted: {backup_path.name} ({mtime.strftime('%Y-%m-%d')})")
                    deleted += 1
                    freed_bytes += size
                except Exception as e:
                    logger.error(f"Failed to delete {backup_path.name}: {e}")
        else:
            kept += 1

    logger.info(f"Summary: Kept {kept}, Deleted {deleted}, Freed {freed_bytes / (1024*1024):.2f} MB")
    return deleted


def cleanup_r2_backups(
    backup_type: str,
    retention_days: int,
    dry_run: bool = False
) -> int:
    """
    Delete R2 backups older than retention period.

    Args:
        backup_type: "daily" or "weekly"
        retention_days: Keep backups newer than this many days
        dry_run: If True, only show what would be deleted

    Returns:
        Number of backups deleted
    """
    if not is_r2_configured():
        logger.info("R2 not configured, skipping cloud cleanup")
        return 0

    try:
        from upload_to_r2 import get_r2_client, R2_CONFIG

        client = get_r2_client()
        bucket = R2_CONFIG["bucket"]
        prefix = f"backups/{backup_type}/"

        cutoff_date = datetime.now(datetime.now().astimezone().tzinfo) - timedelta(days=retention_days)

        # List all objects with prefix
        response = client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=1000)
        objects = response.get("Contents", [])

        if not objects:
            logger.info(f"No {backup_type} backups found in R2")
            return 0

        logger.info(f"Scanning R2 {backup_type} backups...")

        deleted = 0
        for obj in objects:
            if obj["LastModified"].replace(tzinfo=None) < cutoff_date.replace(tzinfo=None):
                if dry_run:
                    logger.info(f"[DRY RUN] Would delete: {obj['Key']}")
                else:
                    try:
                        client.delete_object(Bucket=bucket, Key=obj["Key"])
                        logger.info(f"Deleted R2: {obj['Key']}")
                        deleted += 1
                    except Exception as e:
                        logger.error(f"Failed to delete {obj['Key']}: {e}")

        logger.info(f"R2 cleanup: Deleted {deleted} {backup_type} backups")
        return deleted

    except Exception as e:
        logger.error(f"R2 cleanup failed: {e}")
        return 0


def cleanup_all(dry_run: bool = False) -> dict:
    """
    Run cleanup for all backup types (local and R2).

    Args:
        dry_run: If True, only show what would be deleted

    Returns:
        Dictionary with cleanup statistics
    """
    stats = {
        "local_daily": 0,
        "local_weekly": 0,
        "r2_daily": 0,
        "r2_weekly": 0,
    }

    logger.info("=" * 60)
    logger.info("BACKUP CLEANUP")
    logger.info("=" * 60)

    if dry_run:
        logger.info("[DRY RUN MODE - No files will be deleted]")

    # Local cleanup
    logger.info("\n--- Local Daily Backups ---")
    stats["local_daily"] = cleanup_local_backups(
        "daily",
        RETENTION_POLICY["daily_retention_days"],
        dry_run
    )

    logger.info("\n--- Local Weekly Backups ---")
    stats["local_weekly"] = cleanup_local_backups(
        "weekly",
        RETENTION_POLICY["weekly_retention_days"],
        dry_run
    )

    # R2 cleanup
    if is_r2_configured():
        logger.info("\n--- R2 Daily Backups ---")
        stats["r2_daily"] = cleanup_r2_backups(
            "daily",
            RETENTION_POLICY["daily_retention_days"],
            dry_run
        )

        logger.info("\n--- R2 Weekly Backups ---")
        stats["r2_weekly"] = cleanup_r2_backups(
            "weekly",
            RETENTION_POLICY["weekly_retention_days"],
            dry_run
        )

    # Summary
    total_deleted = sum(stats.values())
    logger.info("\n" + "=" * 60)
    logger.info(f"CLEANUP COMPLETE: {total_deleted} total backups deleted")
    logger.info("=" * 60)

    return stats


def show_disk_usage():
    """Show current backup disk usage."""
    print("\n" + "=" * 60)
    print("BACKUP DISK USAGE")
    print("=" * 60)

    total_size = 0
    total_files = 0

    for backup_type in ["daily", "weekly"]:
        backup_dir = LOCAL_PATHS[backup_type]
        backups = get_backup_files(backup_dir)

        type_size = sum(f.stat().st_size for f, _ in backups)
        total_size += type_size
        total_files += len(backups)

        print(f"\n{backup_type.upper()} ({backup_dir}):")
        print(f"  Files: {len(backups)}")
        print(f"  Size: {type_size / (1024*1024):.2f} MB")

        if backups:
            oldest = min(mtime for _, mtime in backups)
            newest = max(mtime for _, mtime in backups)
            print(f"  Oldest: {oldest.strftime('%Y-%m-%d %H:%M')}")
            print(f"  Newest: {newest.strftime('%Y-%m-%d %H:%M')}")

    print(f"\nTOTAL: {total_files} files, {total_size / (1024*1024):.2f} MB")
    print("=" * 60)


def main():
    """Main entry point for cleanup script."""
    import argparse

    parser = argparse.ArgumentParser(description="Backup Cleanup Script")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without deleting"
    )
    parser.add_argument(
        "--type",
        choices=["daily", "weekly", "all"],
        default="all",
        help="Backup type to clean up"
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Only clean up local backups"
    )
    parser.add_argument(
        "--show-usage",
        action="store_true",
        help="Show current disk usage and exit"
    )

    args = parser.parse_args()

    if args.show_usage:
        show_disk_usage()
        sys.exit(0)

    if args.type == "all":
        cleanup_all(args.dry_run)
    else:
        cleanup_local_backups(
            args.type,
            RETENTION_POLICY[f"{args.type}_retention_days"],
            args.dry_run
        )
        if not args.local_only and is_r2_configured():
            cleanup_r2_backups(
                args.type,
                RETENTION_POLICY[f"{args.type}_retention_days"],
                args.dry_run
            )


if __name__ == "__main__":
    main()
