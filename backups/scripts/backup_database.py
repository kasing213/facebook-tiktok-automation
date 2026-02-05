"""
Database Backup Script
======================
Creates PostgreSQL backups using pg_dump for all configured schemas.
Supports both daily incremental and weekly full backups.
"""

import subprocess
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from backup_config import (
    DATABASE_CONFIG,
    SCHEMAS_TO_BACKUP,
    LOCAL_PATHS,
    BACKUP_SETTINGS,
    LOG_CONFIG,
    get_backup_filename,
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


def check_pg_dump_available() -> bool:
    """Check if pg_dump is available in PATH."""
    try:
        result = subprocess.run(
            ["pg_dump", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            logger.info(f"pg_dump version: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        logger.error("pg_dump not found. Please install PostgreSQL client tools.")
    except Exception as e:
        logger.error(f"Error checking pg_dump: {e}")
    return False


def build_pg_dump_command(output_path: Path, include_data: bool = True) -> list:
    """
    Build pg_dump command with all required parameters.

    Args:
        output_path: Path to save the backup file
        include_data: If False, only backup schema (no data)

    Returns:
        List of command arguments
    """
    cfg = DATABASE_CONFIG
    settings = BACKUP_SETTINGS

    cmd = [
        "pg_dump",
        f"--host={cfg['host']}",
        f"--port={cfg['port']}",
        f"--username={cfg['user']}",
        f"--dbname={cfg['database']}",
        f"--format={settings['format']}",
        f"--compress={settings['compression_level']}",
        "--no-owner",           # Skip ownership (for cross-env restore)
        "--no-privileges",      # Skip privileges
        "--verbose",            # Show progress
    ]

    # Add schema filters
    for schema in SCHEMAS_TO_BACKUP:
        cmd.append(f"--schema={schema}")

    # Schema-only for incremental backups
    if not include_data:
        cmd.append("--schema-only")

    # Output file
    cmd.append(f"--file={output_path}")

    return cmd


def run_backup(
    backup_type: str = "daily",
    include_data: bool = True
) -> Tuple[bool, Optional[Path]]:
    """
    Execute database backup.

    Args:
        backup_type: "daily" or "weekly"
        include_data: Include table data (False for schema-only)

    Returns:
        Tuple of (success: bool, backup_path: Optional[Path])
    """
    logger.info(f"Starting {backup_type} backup...")

    # Check prerequisites
    if not check_pg_dump_available():
        return False, None

    if not DATABASE_CONFIG["password"]:
        logger.error("Database password not configured. Set SUPABASE_PASSWORD in .env")
        return False, None

    # Determine output directory
    output_dir = LOCAL_PATHS.get(backup_type, LOCAL_PATHS["daily"])
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    filename = get_backup_filename(backup_type, "dump")
    output_path = output_dir / filename

    # Build and run command
    cmd = build_pg_dump_command(output_path, include_data)

    # Set environment with password (more secure than command line)
    env = {
        **subprocess.os.environ,
        "PGPASSWORD": DATABASE_CONFIG["password"],
    }

    logger.info(f"Backing up schemas: {', '.join(SCHEMAS_TO_BACKUP)}")
    logger.info(f"Output: {output_path}")

    try:
        start_time = datetime.now()

        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=BACKUP_SETTINGS["timeout_seconds"]
        )

        duration = (datetime.now() - start_time).total_seconds()

        if result.returncode == 0:
            file_size = output_path.stat().st_size / (1024 * 1024)  # MB
            logger.info(f"Backup completed successfully!")
            logger.info(f"File: {output_path.name}")
            logger.info(f"Size: {file_size:.2f} MB")
            logger.info(f"Duration: {duration:.1f} seconds")
            return True, output_path
        else:
            logger.error(f"pg_dump failed with return code {result.returncode}")
            logger.error(f"stderr: {result.stderr}")
            return False, None

    except subprocess.TimeoutExpired:
        logger.error(f"Backup timed out after {BACKUP_SETTINGS['timeout_seconds']} seconds")
        return False, None
    except Exception as e:
        logger.error(f"Backup failed with exception: {e}")
        return False, None


def verify_backup(backup_path: Path) -> bool:
    """
    Verify backup file integrity using pg_restore --list.
    Falls back to basic file validation if pg_restore is not available.

    Args:
        backup_path: Path to backup file

    Returns:
        True if backup is valid
    """
    if not backup_path.exists():
        logger.error(f"Backup file not found: {backup_path}")
        return False

    # Check file size (should be > 0)
    file_size = backup_path.stat().st_size
    if file_size == 0:
        logger.error("Backup file is empty")
        return False

    # Try pg_restore verification if available
    try:
        result = subprocess.run(
            ["pg_restore", "--list", str(backup_path)],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            # Count objects in backup
            lines = [l for l in result.stdout.split("\n") if l.strip() and not l.startswith(";")]
            logger.info(f"Backup verified: {len(lines)} objects found")
            return True
        else:
            logger.error(f"Backup verification failed: {result.stderr}")
            return False

    except FileNotFoundError:
        # pg_restore not installed - fall back to basic validation
        logger.warning("pg_restore not found - using basic file validation")
        # Check if file has valid PostgreSQL custom format header (PGDMP)
        try:
            with open(backup_path, 'rb') as f:
                header = f.read(5)
                if header == b'PGDMP':
                    logger.info(f"Backup verified (basic): valid PostgreSQL dump header, size: {file_size / (1024*1024):.2f} MB")
                    return True
                else:
                    logger.error("Invalid backup file: missing PostgreSQL dump header")
                    return False
        except Exception as e:
            logger.error(f"Failed to read backup file: {e}")
            return False

    except Exception as e:
        logger.error(f"Verification error: {e}")
        return False


def main():
    """Main entry point for backup script."""
    import argparse

    parser = argparse.ArgumentParser(description="Database Backup Script")
    parser.add_argument(
        "--type",
        choices=["daily", "weekly"],
        default="daily",
        help="Backup type (daily or weekly)"
    )
    parser.add_argument(
        "--schema-only",
        action="store_true",
        help="Backup schema only (no data)"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify backup after creation"
    )

    args = parser.parse_args()

    # Run backup
    success, backup_path = run_backup(
        backup_type=args.type,
        include_data=not args.schema_only
    )

    if success and backup_path:
        # Verify if requested
        if args.verify:
            if verify_backup(backup_path):
                logger.info("Backup verification passed!")
            else:
                logger.warning("Backup verification failed!")
                sys.exit(1)

        print(f"\nBackup saved to: {backup_path}")
        sys.exit(0)
    else:
        logger.error("Backup failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
