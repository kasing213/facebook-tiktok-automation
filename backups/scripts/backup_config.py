"""
Backup Configuration Settings
=============================
Central configuration for database backups, cloud storage, and retention policies.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# =============================================================================
# DATABASE CONFIGURATION (Supabase PostgreSQL)
# =============================================================================

DATABASE_CONFIG = {
    "host": os.getenv("SUPABASE_HOST", "aws-1-ap-southeast-1.pooler.supabase.com"),
    "port": int(os.getenv("SUPABASE_PORT", "5432")),
    "database": os.getenv("SUPABASE_DB", "postgres"),
    "user": os.getenv("SUPABASE_USER", "postgres.owyhbkmbagmteihvnvek"),
    "password": os.getenv("SUPABASE_PASSWORD", ""),
}

# All schemas to backup (7 schemas total)
SCHEMAS_TO_BACKUP = [
    "public",        # Core: users, tenants, oauth tokens, automations
    "invoice",       # Business: invoices, customers, client links
    "inventory",     # Products: catalog, stock movements
    "scriptclient",  # Verification: payment screenshots metadata
    "audit_sales",   # Analytics: sales records
    "ads_alert",     # Marketing: promotions, chats
]

# =============================================================================
# MONGODB CONFIGURATION (Ads Alert Media Storage)
# =============================================================================

MONGODB_CONFIG = {
    "url": os.getenv("MONGO_URL_ADS_ALERT", ""),
    "database": "ads_alert",  # Database name for GridFS
}

# =============================================================================
# CLOUDFLARE R2 CONFIGURATION
# =============================================================================

R2_CONFIG = {
    "account_id": os.getenv("R2_ACCOUNT_ID", ""),
    "access_key": os.getenv("R2_ACCESS_KEY", ""),
    "secret_key": os.getenv("R2_SECRET_KEY", ""),
    "bucket": os.getenv("R2_BUCKET", "facebook-automation-backups"),
    "endpoint": f"https://{os.getenv('R2_ACCOUNT_ID', '')}.r2.cloudflarestorage.com",
}

# =============================================================================
# LOCAL STORAGE PATHS
# =============================================================================

BACKUP_ROOT = PROJECT_ROOT / "backups"
LOCAL_PATHS = {
    "daily": BACKUP_ROOT / "local" / "daily",
    "weekly": BACKUP_ROOT / "local" / "weekly",
    "mongodb_daily": BACKUP_ROOT / "local" / "mongodb" / "daily",
    "mongodb_weekly": BACKUP_ROOT / "local" / "mongodb" / "weekly",
    "configs": BACKUP_ROOT / "configs",
    "logs": BACKUP_ROOT / "logs",
}

# Ensure directories exist
for path in LOCAL_PATHS.values():
    path.mkdir(parents=True, exist_ok=True)

# =============================================================================
# RETENTION POLICY
# =============================================================================

RETENTION_POLICY = {
    "daily_retention_days": 7,      # Keep daily backups for 7 days
    "weekly_retention_days": 28,    # Keep weekly backups for 4 weeks
}

# =============================================================================
# BACKUP SETTINGS
# =============================================================================

BACKUP_SETTINGS = {
    "compression_level": 9,         # Maximum compression (1-9)
    "format": "custom",             # pg_dump custom format for selective restore
    "parallel_jobs": 2,             # Parallel dump jobs (careful with connections)
    "timeout_seconds": 3600,        # 1 hour timeout for large databases
}

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOG_CONFIG = {
    "file": LOCAL_PATHS["logs"] / "backup.log",
    "format": "%(asctime)s - %(levelname)s - %(message)s",
    "max_bytes": 10 * 1024 * 1024,  # 10MB max log file
    "backup_count": 5,              # Keep 5 rotated log files
}

# =============================================================================
# NOTIFICATION SETTINGS (Optional)
# =============================================================================

NOTIFICATION_CONFIG = {
    "telegram_enabled": os.getenv("BACKUP_TELEGRAM_NOTIFY", "false").lower() == "true",
    "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "telegram_chat_id": os.getenv("BACKUP_NOTIFY_CHAT_ID", ""),
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_database_url() -> str:
    """Generate PostgreSQL connection URL from config."""
    cfg = DATABASE_CONFIG
    return f"postgresql://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['database']}"


def is_r2_configured() -> bool:
    """Check if Cloudflare R2 is properly configured."""
    return all([
        R2_CONFIG["account_id"],
        R2_CONFIG["access_key"],
        R2_CONFIG["secret_key"],
    ])


def is_mongodb_configured() -> bool:
    """Check if MongoDB is properly configured."""
    return bool(MONGODB_CONFIG["url"])


def get_backup_filename(backup_type: str, extension: str = "dump") -> str:
    """Generate timestamped backup filename."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"backup_{timestamp}_{backup_type}.{extension}"


# =============================================================================
# VALIDATION
# =============================================================================

def validate_config():
    """Validate configuration on import."""
    errors = []

    if not DATABASE_CONFIG["password"]:
        errors.append("SUPABASE_PASSWORD not set in environment")

    if not is_r2_configured():
        print("WARNING: Cloudflare R2 not configured. Cloud backups will be skipped.")

    if errors:
        for error in errors:
            print(f"CONFIG ERROR: {error}")
        return False

    return True


# Run validation on import
if __name__ == "__main__":
    print("=" * 60)
    print("BACKUP CONFIGURATION")
    print("=" * 60)
    print(f"\nDatabase Host: {DATABASE_CONFIG['host']}")
    print(f"Database Name: {DATABASE_CONFIG['database']}")
    print(f"Schemas to backup: {', '.join(SCHEMAS_TO_BACKUP)}")
    print(f"\nR2 Configured: {is_r2_configured()}")
    print(f"R2 Bucket: {R2_CONFIG['bucket']}")
    print(f"\nLocal Backup Path: {BACKUP_ROOT / 'local'}")
    print(f"Daily Retention: {RETENTION_POLICY['daily_retention_days']} days")
    print(f"Weekly Retention: {RETENTION_POLICY['weekly_retention_days']} days")
    print("\n" + "=" * 60)

    validate_config()
