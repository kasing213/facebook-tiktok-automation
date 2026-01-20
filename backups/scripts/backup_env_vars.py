"""
Environment Variables Backup Script
====================================
Exports Railway and Vercel environment variables for backup.
Sensitive values are masked for security.
"""

import subprocess
import sys
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from backup_config import (
    LOCAL_PATHS,
    LOG_CONFIG,
    PROJECT_ROOT,
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

# Patterns that indicate sensitive values (should be masked)
SENSITIVE_PATTERNS = [
    "PASSWORD",
    "SECRET",
    "TOKEN",
    "KEY",
    "CREDENTIAL",
    "PRIVATE",
    "API_KEY",
    "ACCESS_KEY",
    "AUTH",
]


def mask_sensitive_value(key: str, value: str) -> str:
    """
    Mask sensitive values while preserving format for verification.

    Args:
        key: Environment variable name
        value: Environment variable value

    Returns:
        Masked value or original if not sensitive
    """
    # Check if key contains sensitive patterns
    key_upper = key.upper()
    is_sensitive = any(pattern in key_upper for pattern in SENSITIVE_PATTERNS)

    if is_sensitive and value:
        if len(value) > 8:
            return f"{value[:4]}...{value[-4:]}"
        else:
            return "***"

    return value


def hash_value(value: str) -> str:
    """Generate SHA-256 hash of value for change detection."""
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def export_railway_vars(project_name: Optional[str] = None) -> Optional[Dict]:
    """
    Export Railway environment variables using CLI.

    Args:
        project_name: Railway project name (optional)

    Returns:
        Dictionary of variables or None if failed
    """
    logger.info("Exporting Railway environment variables...")

    try:
        # Check if Railway CLI is available
        result = subprocess.run(
            ["railway", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            logger.warning("Railway CLI not installed or not in PATH")
            return None

    except FileNotFoundError:
        logger.warning("Railway CLI not found. Install with: npm install -g @railway/cli")
        return None

    try:
        # Get variables
        cmd = ["railway", "variables", "--json"]
        if project_name:
            cmd.extend(["-p", project_name])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            vars_data = json.loads(result.stdout)

            # Process and mask sensitive values
            processed = {}
            for key, value in vars_data.items():
                processed[key] = {
                    "value_masked": mask_sensitive_value(key, value),
                    "value_hash": hash_value(value),
                    "length": len(value),
                }

            logger.info(f"Exported {len(processed)} Railway variables")
            return processed
        else:
            logger.error(f"Railway CLI error: {result.stderr}")
            return None

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Railway output: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to export Railway vars: {e}")
        return None


def export_vercel_vars(project_dir: Optional[Path] = None) -> Optional[Dict]:
    """
    Export Vercel environment variables.

    Args:
        project_dir: Vercel project directory

    Returns:
        Dictionary of variables or None if failed
    """
    logger.info("Exporting Vercel environment variables...")

    # Check for existing .env files in frontend
    frontend_dir = project_dir or (PROJECT_ROOT / "frontend")
    env_files = [
        frontend_dir / ".env",
        frontend_dir / ".env.local",
        frontend_dir / ".env.production",
        frontend_dir / ".env.production.local",
    ]

    processed = {}

    for env_file in env_files:
        if env_file.exists():
            logger.info(f"Reading: {env_file.name}")
            try:
                with open(env_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, _, value = line.partition("=")
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")

                            processed[key] = {
                                "value_masked": mask_sensitive_value(key, value),
                                "value_hash": hash_value(value),
                                "length": len(value),
                                "source": env_file.name,
                            }
            except Exception as e:
                logger.error(f"Failed to read {env_file}: {e}")

    # Try Vercel CLI if available
    try:
        result = subprocess.run(
            ["vercel", "env", "ls"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(frontend_dir)
        )
        if result.returncode == 0:
            logger.info("Vercel CLI available, environment listed")
    except FileNotFoundError:
        logger.info("Vercel CLI not available (optional)")

    logger.info(f"Exported {len(processed)} Vercel variables")
    return processed if processed else None


def export_local_env() -> Optional[Dict]:
    """
    Export variables from local .env file.

    Returns:
        Dictionary of variables or None if failed
    """
    logger.info("Exporting local .env variables...")

    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        logger.warning("No .env file found in project root")
        return None

    processed = {}
    try:
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")

                    processed[key] = {
                        "value_masked": mask_sensitive_value(key, value),
                        "value_hash": hash_value(value),
                        "length": len(value),
                    }

        logger.info(f"Exported {len(processed)} local variables")
        return processed

    except Exception as e:
        logger.error(f"Failed to read .env: {e}")
        return None


def save_backup(data: Dict, name: str) -> Path:
    """
    Save environment backup to JSON file.

    Args:
        data: Environment data to save
        name: Backup name (e.g., 'railway', 'vercel')

    Returns:
        Path to saved file
    """
    configs_dir = LOCAL_PATHS["configs"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"env_{name}_{timestamp}.json"
    filepath = configs_dir / filename

    backup_data = {
        "exported_at": datetime.now().isoformat(),
        "source": name,
        "variable_count": len(data),
        "variables": data,
    }

    with open(filepath, "w") as f:
        json.dump(backup_data, f, indent=2, default=str)

    logger.info(f"Saved to: {filepath}")
    return filepath


def export_all() -> Dict[str, Optional[Path]]:
    """
    Export all environment variables from all sources.

    Returns:
        Dictionary of source -> backup file path
    """
    results = {}

    logger.info("=" * 60)
    logger.info("ENVIRONMENT VARIABLES BACKUP")
    logger.info("=" * 60)

    # Local .env
    logger.info("\n--- Local .env ---")
    local_vars = export_local_env()
    if local_vars:
        results["local"] = save_backup(local_vars, "local")

    # Railway
    logger.info("\n--- Railway ---")
    railway_vars = export_railway_vars()
    if railway_vars:
        results["railway"] = save_backup(railway_vars, "railway")

    # Vercel
    logger.info("\n--- Vercel ---")
    vercel_vars = export_vercel_vars()
    if vercel_vars:
        results["vercel"] = save_backup(vercel_vars, "vercel")

    logger.info("\n" + "=" * 60)
    logger.info(f"Backup complete: {len([r for r in results.values() if r])} sources exported")
    logger.info("=" * 60)

    return results


def compare_backups(file1: Path, file2: Path) -> None:
    """
    Compare two environment backups to detect changes.

    Args:
        file1: First backup file
        file2: Second backup file
    """
    with open(file1, "r") as f:
        data1 = json.load(f)
    with open(file2, "r") as f:
        data2 = json.load(f)

    vars1 = set(data1.get("variables", {}).keys())
    vars2 = set(data2.get("variables", {}).keys())

    added = vars2 - vars1
    removed = vars1 - vars2
    common = vars1 & vars2

    changed = []
    for key in common:
        hash1 = data1["variables"][key].get("value_hash")
        hash2 = data2["variables"][key].get("value_hash")
        if hash1 != hash2:
            changed.append(key)

    print(f"\n{'='*60}")
    print("ENVIRONMENT COMPARISON")
    print(f"{'='*60}")
    print(f"\nComparing:")
    print(f"  Old: {file1.name}")
    print(f"  New: {file2.name}")

    if added:
        print(f"\n+ ADDED ({len(added)}):")
        for key in sorted(added):
            print(f"    {key}")

    if removed:
        print(f"\n- REMOVED ({len(removed)}):")
        for key in sorted(removed):
            print(f"    {key}")

    if changed:
        print(f"\n~ CHANGED ({len(changed)}):")
        for key in sorted(changed):
            print(f"    {key}")

    if not (added or removed or changed):
        print("\nNo changes detected")

    print(f"\n{'='*60}")


def main():
    """Main entry point for env vars backup script."""
    import argparse

    parser = argparse.ArgumentParser(description="Environment Variables Backup")
    parser.add_argument(
        "action",
        nargs="?",
        choices=["export", "compare", "list"],
        default="export",
        help="Action to perform"
    )
    parser.add_argument(
        "--source",
        choices=["local", "railway", "vercel", "all"],
        default="all",
        help="Source to export"
    )
    parser.add_argument(
        "--file1",
        type=Path,
        help="First file for comparison"
    )
    parser.add_argument(
        "--file2",
        type=Path,
        help="Second file for comparison"
    )

    args = parser.parse_args()

    if args.action == "export":
        if args.source == "all":
            export_all()
        elif args.source == "local":
            data = export_local_env()
            if data:
                save_backup(data, "local")
        elif args.source == "railway":
            data = export_railway_vars()
            if data:
                save_backup(data, "railway")
        elif args.source == "vercel":
            data = export_vercel_vars()
            if data:
                save_backup(data, "vercel")

    elif args.action == "compare":
        if not args.file1 or not args.file2:
            print("ERROR: --file1 and --file2 required for comparison")
            sys.exit(1)
        compare_backups(args.file1, args.file2)

    elif args.action == "list":
        configs_dir = LOCAL_PATHS["configs"]
        backups = sorted(configs_dir.glob("env_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        print(f"\nEnvironment backups in {configs_dir}:")
        for b in backups[:10]:
            mtime = datetime.fromtimestamp(b.stat().st_mtime)
            print(f"  {b.name} - {mtime.strftime('%Y-%m-%d %H:%M')}")


if __name__ == "__main__":
    main()
