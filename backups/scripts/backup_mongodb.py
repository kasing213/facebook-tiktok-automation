"""
MongoDB Backup Script
=====================
Backs up MongoDB (Ads Alert media storage) to a compressed archive.
Uses mongodump via subprocess for reliable backups.
"""

import sys
import logging
import subprocess
import shutil
import gzip
import tarfile
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional
from urllib.parse import urlparse, parse_qs

from backup_config import (
    MONGODB_CONFIG,
    LOCAL_PATHS,
    LOG_CONFIG,
    is_mongodb_configured,
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


def parse_mongo_url(url: str) -> dict:
    """
    Parse MongoDB connection URL into components.

    Args:
        url: MongoDB connection string

    Returns:
        Dict with host, port, database, username, password, auth_db
    """
    parsed = urlparse(url)

    # Handle mongodb+srv:// vs mongodb://
    is_srv = parsed.scheme == "mongodb+srv"

    # Extract auth database from query params
    query_params = parse_qs(parsed.query)
    auth_db = query_params.get("authSource", ["admin"])[0]

    # Extract database from path
    database = parsed.path.lstrip("/").split("?")[0] or MONGODB_CONFIG["database"]

    return {
        "host": parsed.hostname,
        "port": parsed.port or (None if is_srv else 27017),
        "database": database,
        "username": parsed.username,
        "password": parsed.password,
        "auth_db": auth_db,
        "is_srv": is_srv,
        "full_url": url,
    }


def check_mongodump_available() -> bool:
    """Check if mongodump is available in PATH."""
    return shutil.which("mongodump") is not None


def run_mongodump(
    output_dir: Path,
    backup_type: str = "daily"
) -> Tuple[bool, Optional[Path]]:
    """
    Run mongodump to backup MongoDB.

    Args:
        output_dir: Directory to store backup
        backup_type: "daily" or "weekly"

    Returns:
        Tuple of (success, backup_path)
    """
    if not is_mongodb_configured():
        logger.warning("MongoDB not configured, skipping backup")
        return False, None

    # Parse connection URL
    mongo_config = parse_mongo_url(MONGODB_CONFIG["url"])

    # Generate backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dump_dir = output_dir / f"mongodb_{timestamp}_{backup_type}"
    archive_path = output_dir / f"mongodb_{timestamp}_{backup_type}.tar.gz"

    logger.info(f"Starting MongoDB backup...")
    logger.info(f"Database: {mongo_config['database']}")
    logger.info(f"Host: {mongo_config['host']}")

    # Build mongodump command
    cmd = ["mongodump"]

    # Use URI for connection (handles SRV and all options)
    cmd.extend(["--uri", MONGODB_CONFIG["url"]])

    # Output to directory
    cmd.extend(["--out", str(dump_dir)])

    # Use gzip compression
    cmd.append("--gzip")

    try:
        logger.info(f"Running mongodump...")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )

        if result.returncode != 0:
            logger.error(f"mongodump failed: {result.stderr}")
            return False, None

        logger.info("mongodump completed successfully")

        # Create tar.gz archive for easier storage/transfer
        logger.info(f"Creating archive: {archive_path.name}")

        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(dump_dir, arcname=dump_dir.name)

        # Clean up dump directory
        shutil.rmtree(dump_dir)

        archive_size = archive_path.stat().st_size / (1024 * 1024)
        logger.info(f"Archive created: {archive_path.name} ({archive_size:.2f} MB)")

        return True, archive_path

    except subprocess.TimeoutExpired:
        logger.error("mongodump timed out after 1 hour")
        return False, None
    except FileNotFoundError:
        logger.error("mongodump not found. Install MongoDB Database Tools.")
        return False, None
    except Exception as e:
        logger.error(f"MongoDB backup failed: {e}")
        return False, None


def run_mongodb_backup_alternative(
    output_dir: Path,
    backup_type: str = "daily"
) -> Tuple[bool, Optional[Path]]:
    """
    Alternative backup using pymongo directly (no mongodump required).
    Backs up GridFS files by exporting metadata and file content.

    Args:
        output_dir: Directory to store backup
        backup_type: "daily" or "weekly"

    Returns:
        Tuple of (success, backup_path)
    """
    if not is_mongodb_configured():
        logger.warning("MongoDB not configured, skipping backup")
        return False, None

    try:
        from pymongo import MongoClient
        import json
        import base64
    except ImportError:
        logger.error("pymongo not installed. Run: pip install pymongo")
        return False, None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = output_dir / f"mongodb_{timestamp}_{backup_type}"
    archive_path = output_dir / f"mongodb_{timestamp}_{backup_type}.tar.gz"

    logger.info("Starting MongoDB backup (Python method)...")

    try:
        # Connect to MongoDB
        client = MongoClient(MONGODB_CONFIG["url"])
        db = client[MONGODB_CONFIG["database"]]

        # Create backup directory
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Export fs.files (GridFS metadata)
        files_collection = db["fs.files"]
        files_data = list(files_collection.find())

        # Convert ObjectId to string for JSON serialization
        for doc in files_data:
            doc["_id"] = str(doc["_id"])
            if "uploadDate" in doc:
                doc["uploadDate"] = doc["uploadDate"].isoformat()

        with open(backup_dir / "fs.files.json", "w") as f:
            json.dump(files_data, f, indent=2, default=str)

        logger.info(f"Exported {len(files_data)} file metadata records")

        # Export fs.chunks (GridFS file content)
        # Note: This can be large, we'll export in batches
        chunks_collection = db["fs.chunks"]
        chunks_count = 0

        # Create chunks subdirectory
        chunks_dir = backup_dir / "chunks"
        chunks_dir.mkdir(exist_ok=True)

        # Export chunks grouped by files_id
        for file_doc in files_data:
            file_id = file_doc["_id"]
            chunks = list(chunks_collection.find({"files_id": file_id}))

            for chunk in chunks:
                chunk["_id"] = str(chunk["_id"])
                chunk["files_id"] = str(chunk["files_id"])
                # Base64 encode binary data
                if "data" in chunk:
                    chunk["data"] = base64.b64encode(chunk["data"]).decode("utf-8")

            if chunks:
                chunk_file = chunks_dir / f"{file_id}.json"
                with open(chunk_file, "w") as f:
                    json.dump(chunks, f)
                chunks_count += len(chunks)

        logger.info(f"Exported {chunks_count} chunks for {len(files_data)} files")

        # Create tar.gz archive
        logger.info(f"Creating archive: {archive_path.name}")

        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(backup_dir, arcname=backup_dir.name)

        # Clean up backup directory
        shutil.rmtree(backup_dir)

        archive_size = archive_path.stat().st_size / (1024 * 1024)
        logger.info(f"Archive created: {archive_path.name} ({archive_size:.2f} MB)")

        client.close()
        return True, archive_path

    except Exception as e:
        logger.error(f"MongoDB backup failed: {e}")
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        return False, None


def run_backup(backup_type: str = "daily") -> Tuple[bool, Optional[Path]]:
    """
    Run MongoDB backup using best available method.

    Args:
        backup_type: "daily" or "weekly"

    Returns:
        Tuple of (success, backup_path)
    """
    if not is_mongodb_configured():
        logger.info("MongoDB not configured, skipping backup")
        return True, None  # Return True to not fail the overall backup

    # Determine output directory
    output_dir = LOCAL_PATHS.get(f"mongodb_{backup_type}", LOCAL_PATHS["mongodb_daily"])
    output_dir.mkdir(parents=True, exist_ok=True)

    # Try mongodump first (faster, more reliable)
    if check_mongodump_available():
        logger.info("Using mongodump for backup")
        return run_mongodump(output_dir, backup_type)
    else:
        logger.info("mongodump not available, using Python backup method")
        return run_mongodb_backup_alternative(output_dir, backup_type)


def verify_backup(backup_path: Path) -> bool:
    """
    Verify MongoDB backup archive integrity.

    Args:
        backup_path: Path to backup archive

    Returns:
        True if verification passes
    """
    if not backup_path or not backup_path.exists():
        return False

    try:
        # Try to open and list contents
        with tarfile.open(backup_path, "r:gz") as tar:
            members = tar.getnames()
            logger.info(f"Archive contains {len(members)} files/directories")

            # Check for expected structure
            has_files = any("fs.files" in m for m in members)
            has_chunks = any("chunks" in m for m in members)

            if has_files:
                logger.info("Found GridFS metadata")
            if has_chunks:
                logger.info("Found GridFS chunks")

            return True

    except Exception as e:
        logger.error(f"Backup verification failed: {e}")
        return False


def main():
    """Main entry point for MongoDB backup script."""
    import argparse

    parser = argparse.ArgumentParser(description="MongoDB Backup Script")
    parser.add_argument(
        "--type",
        choices=["daily", "weekly"],
        default="daily",
        help="Backup type"
    )
    parser.add_argument(
        "--verify",
        type=Path,
        help="Verify an existing backup"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show MongoDB backup status"
    )

    args = parser.parse_args()

    if args.status:
        print("\n" + "=" * 60)
        print("MONGODB BACKUP STATUS")
        print("=" * 60)

        print(f"\nMongoDB configured: {'Yes' if is_mongodb_configured() else 'No'}")
        print(f"mongodump available: {'Yes' if check_mongodump_available() else 'No'}")

        if is_mongodb_configured():
            config = parse_mongo_url(MONGODB_CONFIG["url"])
            print(f"Host: {config['host']}")
            print(f"Database: {config['database']}")

        # Count backups
        for btype in ["mongodb_daily", "mongodb_weekly"]:
            path = LOCAL_PATHS.get(btype)
            if path and path.exists():
                count = len(list(path.glob("*.tar.gz")))
                print(f"\n{btype.replace('mongodb_', '').title()} backups: {count}")

        print("\n" + "=" * 60)
        sys.exit(0)

    if args.verify:
        if verify_backup(args.verify):
            print("Backup verification passed")
            sys.exit(0)
        else:
            print("Backup verification failed")
            sys.exit(1)

    # Run backup
    success, backup_path = run_backup(args.type)

    if success:
        if backup_path:
            print(f"\nBackup successful: {backup_path}")
        else:
            print("\nMongoDB not configured, no backup created")
        sys.exit(0)
    else:
        print("\nBackup failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
