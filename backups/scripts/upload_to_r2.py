"""
Cloudflare R2 Upload Script
===========================
Uploads backup files to Cloudflare R2 object storage.
R2 is S3-compatible, so we use boto3 for the upload.
"""

import sys
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, List

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    print("ERROR: boto3 not installed. Run: pip install boto3")
    sys.exit(1)

from backup_config import (
    R2_CONFIG,
    LOCAL_PATHS,
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


def get_r2_client():
    """Create and return Cloudflare R2 client."""
    if not is_r2_configured():
        raise ValueError("Cloudflare R2 not configured. Set R2_ACCOUNT_ID, R2_ACCESS_KEY, R2_SECRET_KEY in .env")

    return boto3.client(
        "s3",
        endpoint_url=R2_CONFIG["endpoint"],
        aws_access_key_id=R2_CONFIG["access_key"],
        aws_secret_access_key=R2_CONFIG["secret_key"],
        region_name="auto",  # R2 uses 'auto' region
    )


def calculate_md5(file_path: Path) -> str:
    """Calculate MD5 hash of file for integrity verification."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def upload_file(
    local_path: Path,
    remote_key: Optional[str] = None,
    backup_type: str = "daily",
    db_type: str = "postgres"
) -> bool:
    """
    Upload a single file to Cloudflare R2.

    Args:
        local_path: Path to local file
        remote_key: Remote object key (path in bucket). If None, uses local filename.
        backup_type: "daily" or "weekly" - determines R2 folder
        db_type: "postgres" or "mongodb" - determines subfolder

    Returns:
        True if upload successful
    """
    if not local_path.exists():
        logger.error(f"File not found: {local_path}")
        return False

    # Generate remote key if not provided
    if remote_key is None:
        # Organize by type, database, and date: backups/daily/postgres/2026/01/backup_20260118.dump
        date = datetime.now()
        remote_key = f"backups/{backup_type}/{db_type}/{date.year}/{date.month:02d}/{local_path.name}"

    try:
        client = get_r2_client()
        bucket = R2_CONFIG["bucket"]

        file_size = local_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)

        logger.info(f"Uploading {local_path.name} ({file_size_mb:.2f} MB) to R2...")
        logger.info(f"Bucket: {bucket}")
        logger.info(f"Key: {remote_key}")

        # Calculate MD5 for verification
        local_md5 = calculate_md5(local_path)

        # Upload with metadata
        start_time = datetime.now()

        with open(local_path, "rb") as f:
            client.upload_fileobj(
                f,
                bucket,
                remote_key,
                ExtraArgs={
                    "Metadata": {
                        "backup-type": backup_type,
                        "database-type": db_type,
                        "local-md5": local_md5,
                        "upload-timestamp": datetime.now().isoformat(),
                        "source": "facebook-automation-backup",
                    }
                }
            )

        duration = (datetime.now() - start_time).total_seconds()
        speed_mbps = file_size_mb / duration if duration > 0 else 0

        logger.info(f"Upload completed!")
        logger.info(f"Duration: {duration:.1f}s ({speed_mbps:.2f} MB/s)")
        logger.info(f"MD5: {local_md5}")

        return True

    except NoCredentialsError:
        logger.error("R2 credentials not found or invalid")
        return False
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_msg = e.response.get("Error", {}).get("Message", str(e))
        logger.error(f"R2 upload failed: [{error_code}] {error_msg}")
        return False
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return False


def list_backups(
    backup_type: Optional[str] = None,
    db_type: Optional[str] = None,
    limit: int = 20
) -> List[dict]:
    """
    List backups stored in R2.

    Args:
        backup_type: Filter by type ("daily" or "weekly"). None for all.
        db_type: Filter by database ("postgres" or "mongodb"). None for all.
        limit: Maximum number of results

    Returns:
        List of backup objects with metadata
    """
    try:
        client = get_r2_client()
        bucket = R2_CONFIG["bucket"]

        # Build prefix based on filters
        if backup_type and db_type:
            prefix = f"backups/{backup_type}/{db_type}/"
        elif backup_type:
            prefix = f"backups/{backup_type}/"
        else:
            prefix = "backups/"

        response = client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix,
            MaxKeys=limit
        )

        backups = []
        for obj in response.get("Contents", []):
            # Extract db_type from key path
            key_parts = obj["Key"].split("/")
            detected_db_type = key_parts[2] if len(key_parts) > 2 else "unknown"

            backups.append({
                "key": obj["Key"],
                "size_mb": obj["Size"] / (1024 * 1024),
                "last_modified": obj["LastModified"],
                "db_type": detected_db_type,
            })

        return sorted(backups, key=lambda x: x["last_modified"], reverse=True)

    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        return []


def download_backup(remote_key: str, local_path: Path) -> bool:
    """
    Download a backup from R2.

    Args:
        remote_key: Object key in R2
        local_path: Local destination path

    Returns:
        True if download successful
    """
    try:
        client = get_r2_client()
        bucket = R2_CONFIG["bucket"]

        logger.info(f"Downloading {remote_key}...")

        local_path.parent.mkdir(parents=True, exist_ok=True)

        client.download_file(bucket, remote_key, str(local_path))

        logger.info(f"Downloaded to: {local_path}")
        return True

    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False


def delete_old_backups(
    backup_type: str,
    keep_count: int,
    db_type: str = "postgres"
) -> int:
    """
    Delete old backups from R2, keeping only the most recent ones.

    Args:
        backup_type: "daily" or "weekly"
        keep_count: Number of backups to keep
        db_type: "postgres" or "mongodb"

    Returns:
        Number of backups deleted
    """
    try:
        client = get_r2_client()
        bucket = R2_CONFIG["bucket"]

        # List all backups of this type and database
        backups = list_backups(backup_type, db_type=db_type, limit=100)

        if len(backups) <= keep_count:
            logger.info(f"Only {len(backups)} {db_type}/{backup_type} backups exist, keeping all")
            return 0

        # Delete oldest backups
        to_delete = backups[keep_count:]
        deleted = 0

        for backup in to_delete:
            try:
                client.delete_object(Bucket=bucket, Key=backup["key"])
                logger.info(f"Deleted old backup: {backup['key']}")
                deleted += 1
            except Exception as e:
                logger.error(f"Failed to delete {backup['key']}: {e}")

        return deleted

    except Exception as e:
        logger.error(f"Failed to cleanup R2 backups: {e}")
        return 0


def upload_latest_backup(
    backup_type: str = "daily",
    db_type: str = "postgres"
) -> bool:
    """
    Find and upload the latest local backup of given type.

    Args:
        backup_type: "daily" or "weekly"
        db_type: "postgres" or "mongodb"

    Returns:
        True if upload successful
    """
    # Determine local directory and file pattern based on db_type
    if db_type == "mongodb":
        dir_key = f"mongodb_{backup_type}"
        file_pattern = "*.tar.gz"
    else:
        dir_key = backup_type
        file_pattern = "*.dump"

    local_dir = LOCAL_PATHS.get(dir_key, LOCAL_PATHS["daily"])

    # Find latest backup file
    backup_files = list(local_dir.glob(file_pattern))
    if not backup_files:
        logger.warning(f"No {db_type} backup files found in {local_dir}")
        return False

    latest = max(backup_files, key=lambda p: p.stat().st_mtime)
    logger.info(f"Found latest {db_type} backup: {latest.name}")

    return upload_file(latest, backup_type=backup_type, db_type=db_type)


def main():
    """Main entry point for R2 upload script."""
    import argparse

    parser = argparse.ArgumentParser(description="Cloudflare R2 Backup Upload")
    parser.add_argument(
        "action",
        choices=["upload", "list", "download", "cleanup"],
        help="Action to perform"
    )
    parser.add_argument(
        "--type",
        choices=["daily", "weekly"],
        default="daily",
        help="Backup type"
    )
    parser.add_argument(
        "--db",
        choices=["postgres", "mongodb", "all"],
        default="postgres",
        help="Database type (default: postgres, use 'all' for list)"
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Specific file to upload or download destination"
    )
    parser.add_argument(
        "--key",
        help="R2 object key (for download)"
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=7,
        help="Number of backups to keep (for cleanup)"
    )

    args = parser.parse_args()

    if not is_r2_configured():
        print("\nCloudflare R2 not configured!")
        print("Add these to your .env file:")
        print("  R2_ACCOUNT_ID=your_account_id")
        print("  R2_ACCESS_KEY=your_access_key")
        print("  R2_SECRET_KEY=your_secret_key")
        sys.exit(1)

    if args.action == "upload":
        if args.file:
            success = upload_file(args.file, backup_type=args.type, db_type=args.db)
        else:
            success = upload_latest_backup(args.type, db_type=args.db)
        sys.exit(0 if success else 1)

    elif args.action == "list":
        db_filter = None if args.db == "all" else args.db
        backups = list_backups(args.type, db_type=db_filter)
        if backups:
            print(f"\n{args.type.upper()} Backups in R2:")
            print("-" * 70)
            for b in backups:
                db_label = f"[{b.get('db_type', 'unknown').upper()}]"
                print(f"  {db_label} {b['key']}")
                print(f"       Size: {b['size_mb']:.2f} MB | Modified: {b['last_modified']}")
        else:
            print("No backups found")

    elif args.action == "download":
        if not args.key:
            print("ERROR: --key required for download")
            sys.exit(1)
        dest = args.file or Path(args.key.split("/")[-1])
        success = download_backup(args.key, dest)
        sys.exit(0 if success else 1)

    elif args.action == "cleanup":
        if args.db == "all":
            # Cleanup both database types
            deleted_pg = delete_old_backups(args.type, args.keep, db_type="postgres")
            deleted_mongo = delete_old_backups(args.type, args.keep, db_type="mongodb")
            print(f"Deleted {deleted_pg} old postgres {args.type} backups")
            print(f"Deleted {deleted_mongo} old mongodb {args.type} backups")
        else:
            deleted = delete_old_backups(args.type, args.keep, db_type=args.db)
            print(f"Deleted {deleted} old {args.db} {args.type} backups")


if __name__ == "__main__":
    main()
