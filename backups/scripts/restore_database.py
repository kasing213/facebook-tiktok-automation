"""
Database Restore Script
=======================
Restores PostgreSQL database from backup files.
Supports full restore and selective schema restore.

WARNING: This script will overwrite existing data!
Always verify you have a recent backup before restoring.
"""

import subprocess
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from backup_config import (
    DATABASE_CONFIG,
    SCHEMAS_TO_BACKUP,
    LOCAL_PATHS,
    LOG_CONFIG,
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


def list_backup_contents(backup_path: Path) -> List[str]:
    """
    List contents of a backup file.

    Args:
        backup_path: Path to backup file

    Returns:
        List of object descriptions in the backup
    """
    try:
        result = subprocess.run(
            ["pg_restore", "--list", str(backup_path)],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            lines = [l for l in result.stdout.split("\n") if l.strip() and not l.startswith(";")]
            return lines
        else:
            logger.error(f"Failed to list backup contents: {result.stderr}")
            return []

    except Exception as e:
        logger.error(f"Error listing backup: {e}")
        return []


def restore_database(
    backup_path: Path,
    schemas: Optional[List[str]] = None,
    clean: bool = True,
    dry_run: bool = False
) -> bool:
    """
    Restore database from backup file.

    Args:
        backup_path: Path to backup file (.dump)
        schemas: List of schemas to restore (None for all)
        clean: Drop existing objects before restore
        dry_run: If True, only show what would be restored

    Returns:
        True if restore successful
    """
    if not backup_path.exists():
        logger.error(f"Backup file not found: {backup_path}")
        return False

    if not DATABASE_CONFIG["password"]:
        logger.error("Database password not configured. Set SUPABASE_PASSWORD in .env")
        return False

    # Build restore command
    cfg = DATABASE_CONFIG
    cmd = [
        "pg_restore",
        f"--host={cfg['host']}",
        f"--port={cfg['port']}",
        f"--username={cfg['user']}",
        f"--dbname={cfg['database']}",
        "--verbose",
        "--no-owner",
        "--no-privileges",
    ]

    if clean:
        cmd.extend(["--clean", "--if-exists"])

    # Add schema filters if specified
    if schemas:
        for schema in schemas:
            cmd.append(f"--schema={schema}")

    # Add backup file
    cmd.append(str(backup_path))

    # Dry run mode
    if dry_run:
        print("\n" + "=" * 60)
        print("DRY RUN - No changes will be made")
        print("=" * 60)
        print(f"\nBackup file: {backup_path}")
        print(f"File size: {backup_path.stat().st_size / (1024*1024):.2f} MB")
        print(f"Schemas to restore: {schemas or 'ALL'}")
        print(f"Clean mode: {clean}")
        print(f"\nCommand: {' '.join(cmd)}")

        # List backup contents
        contents = list_backup_contents(backup_path)
        print(f"\nBackup contains {len(contents)} objects")

        return True

    # Confirm before restore
    print("\n" + "!" * 60)
    print("WARNING: This will overwrite existing data!")
    print("!" * 60)
    print(f"\nBackup file: {backup_path}")
    print(f"Target database: {cfg['host']}/{cfg['database']}")
    print(f"Schemas: {schemas or 'ALL'}")
    print(f"Clean mode: {clean}")

    confirm = input("\nType 'RESTORE' to confirm: ")
    if confirm != "RESTORE":
        logger.info("Restore cancelled by user")
        return False

    # Set environment with password
    env = {
        **subprocess.os.environ,
        "PGPASSWORD": DATABASE_CONFIG["password"],
    }

    logger.info("Starting database restore...")
    start_time = datetime.now()

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )

        duration = (datetime.now() - start_time).total_seconds()

        # pg_restore returns non-zero for warnings too, so check stderr
        if "error" in result.stderr.lower():
            logger.error(f"Restore completed with errors:")
            logger.error(result.stderr)
            return False
        else:
            logger.info(f"Restore completed in {duration:.1f} seconds")
            if result.stderr:
                logger.warning(f"Warnings: {result.stderr[:500]}")
            return True

    except subprocess.TimeoutExpired:
        logger.error("Restore timed out after 1 hour")
        return False
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        return False


def find_latest_backup(backup_type: str = "daily") -> Optional[Path]:
    """
    Find the most recent backup file.

    Args:
        backup_type: "daily" or "weekly"

    Returns:
        Path to latest backup or None
    """
    backup_dir = LOCAL_PATHS.get(backup_type, LOCAL_PATHS["daily"])

    backups = list(backup_dir.glob("*.dump"))
    if not backups:
        return None

    return max(backups, key=lambda p: p.stat().st_mtime)


def verify_restore() -> bool:
    """
    Verify database after restore by checking table counts.

    Returns:
        True if verification passes
    """
    try:
        import psycopg2

        cfg = DATABASE_CONFIG
        conn = psycopg2.connect(
            host=cfg["host"],
            port=cfg["port"],
            database=cfg["database"],
            user=cfg["user"],
            password=cfg["password"]
        )

        cur = conn.cursor()

        print("\n" + "=" * 60)
        print("POST-RESTORE VERIFICATION")
        print("=" * 60)

        # Check each schema
        for schema in SCHEMAS_TO_BACKUP:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
            """, (schema,))
            tables = cur.fetchall()

            total_rows = 0
            for (table_name,) in tables:
                cur.execute(f'SELECT COUNT(*) FROM "{schema}"."{table_name}"')
                count = cur.fetchone()[0]
                total_rows += count

            print(f"\n{schema}:")
            print(f"  Tables: {len(tables)}")
            print(f"  Total rows: {total_rows:,}")

        cur.close()
        conn.close()

        print("\n" + "=" * 60)
        return True

    except ImportError:
        logger.warning("psycopg2 not installed, skipping verification")
        return True
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False


def main():
    """Main entry point for restore script."""
    import argparse

    parser = argparse.ArgumentParser(description="Database Restore Script")
    parser.add_argument(
        "backup_file",
        nargs="?",
        type=Path,
        help="Backup file to restore (uses latest if not specified)"
    )
    parser.add_argument(
        "--type",
        choices=["daily", "weekly"],
        default="daily",
        help="Backup type to find latest (if backup_file not specified)"
    )
    parser.add_argument(
        "--schema",
        action="append",
        dest="schemas",
        help="Restore specific schema(s) only (can be repeated)"
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Don't drop existing objects before restore"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be restored without making changes"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify database after restore"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available local backups"
    )

    args = parser.parse_args()

    # List backups mode
    if args.list:
        print("\nAvailable backups:")
        for btype in ["daily", "weekly"]:
            backup_dir = LOCAL_PATHS[btype]
            backups = sorted(backup_dir.glob("*.dump"), key=lambda p: p.stat().st_mtime, reverse=True)
            print(f"\n{btype.upper()} ({backup_dir}):")
            if backups:
                for b in backups[:5]:
                    size_mb = b.stat().st_size / (1024 * 1024)
                    mtime = datetime.fromtimestamp(b.stat().st_mtime)
                    print(f"  {b.name} ({size_mb:.2f} MB) - {mtime}")
            else:
                print("  No backups found")
        sys.exit(0)

    # Find backup file
    backup_path = args.backup_file
    if not backup_path:
        backup_path = find_latest_backup(args.type)
        if not backup_path:
            print(f"No {args.type} backups found. Specify a backup file.")
            sys.exit(1)
        print(f"Using latest {args.type} backup: {backup_path.name}")

    # Run restore
    success = restore_database(
        backup_path=backup_path,
        schemas=args.schemas,
        clean=not args.no_clean,
        dry_run=args.dry_run
    )

    if success and not args.dry_run:
        if args.verify:
            verify_restore()
        print("\nRestore completed successfully!")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
