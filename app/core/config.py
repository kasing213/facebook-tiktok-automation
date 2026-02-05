from functools import lru_cache
from typing import Literal
from pathlib import Path

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the project root directory (2 levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Supports configuration through:
    - Environment variables
    - .env file
    - Default values for non-sensitive settings
    """

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"  # Allow extra env vars for flexibility
    )

    # Application settings
    ENV: Literal["dev", "staging", "prod"] = "dev"
    BASE_URL: AnyHttpUrl = Field(default="http://localhost:8000", description="Base URL for the application")
    FRONTEND_URL: AnyHttpUrl = Field(default="http://localhost:3000", description="Frontend base URL for redirects")

    # Database configuration
    DATABASE_URL: str = Field(..., description="PostgreSQL database connection string")
    REDIS_URL: str | None = Field(default=None, description="Redis connection string (optional)")

    # Security settings
    OAUTH_STATE_SECRET: SecretStr = Field(..., description="Secret key for OAuth state validation")
    MASTER_SECRET_KEY: SecretStr = Field(..., description="Master secret key for application security")

    # Facebook integration
    FB_APP_ID: str = Field(..., description="Facebook App ID")
    FB_APP_SECRET: SecretStr = Field(..., description="Facebook App Secret")
    FB_SCOPES: str = Field(
        default="public_profile,email,pages_show_list,pages_read_engagement,pages_manage_posts,ads_read",
        description="Facebook OAuth scopes (comma-separated)"
    )
    FB_FORCE_REAUTH: bool = Field(default=False, description="Force Facebook re-authentication in OAuth flow")

    # TikTok integration
    TIKTOK_CLIENT_KEY: str = Field(..., description="TikTok Client Key")
    TIKTOK_CLIENT_SECRET: SecretStr = Field(..., description="TikTok Client Secret")
    TIKTOK_SCOPES: str = Field(default="user.info.basic,video.upload,video.publish", description="TikTok API scopes")

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: SecretStr = Field(..., description="Telegram Bot Token")
    TELEGRAM_BOT_USERNAME: str = Field(default="your_bot", description="Telegram Bot username (without @)")

    # Webhook configuration
    FACEBOOK_WEBHOOK_VERIFY_TOKEN: SecretStr = Field(default="my_facebook_verify_token_change_me", description="Facebook webhook verification token")
    TIKTOK_WEBHOOK_VERIFY_TOKEN: SecretStr = Field(default="my_tiktok_verify_token_change_me", description="TikTok webhook verification token")

    # Invoice API Integration
    INVOICE_API_URL: str = Field(default="", description="External Invoice API base URL")
    INVOICE_API_KEY: SecretStr = Field(default=SecretStr(""), description="Invoice API authentication key")
    INVOICE_JWT_SECRET: SecretStr = Field(default=SecretStr(""), description="JWT secret for Invoice API authentication")

    # Stripe Integration
    STRIPE_SECRET_KEY: SecretStr = Field(default=SecretStr(""), description="Stripe secret key")
    STRIPE_WEBHOOK_SECRET: SecretStr = Field(default=SecretStr(""), description="Stripe webhook signing secret")
    STRIPE_PRICE_ID_MONTHLY: str = Field(default="", description="Stripe monthly price ID for Pro subscription")
    STRIPE_PRICE_ID_YEARLY: str = Field(default="", description="Stripe yearly price ID for Pro subscription")

    # Invoice Mock Mode (for testing without external API)
    INVOICE_MOCK_MODE: bool = Field(default=False, description="Use mock in-memory Invoice API instead of external service")
    INVOICE_TIER_ENFORCEMENT: bool = Field(default=True, description="Enforce Pro tier for PDF/Export features (disable for testing)")

    # OCR Verification Service
    OCR_API_URL: str = Field(default="", description="OCR verification service base URL")
    OCR_API_KEY: SecretStr = Field(default=SecretStr(""), description="OCR API authentication key")

    # Email/SMTP Configuration (optional - falls back to console logging in dev)
    SMTP_HOST: str = Field(default="", description="SMTP server host (e.g., smtp.gmail.com)")
    SMTP_PORT: int = Field(default=587, description="SMTP server port")
    SMTP_USER: str = Field(default="", description="SMTP username/email")
    SMTP_PASSWORD: SecretStr = Field(default=SecretStr(""), description="SMTP password or app password")
    SMTP_FROM_EMAIL: str = Field(default="noreply@example.com", description="From email address")
    SMTP_FROM_NAME: str = Field(default="KS Automation", description="From name in emails")
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = Field(default=24, description="Email verification token expiry in hours")

    # Google OAuth for Gmail API (recommended for cloud environments like Railway)
    # SMTP is blocked by most cloud providers, so Gmail API is the reliable alternative
    # Run: python scripts/setup_gmail_oauth.py to get these values
    GOOGLE_CLIENT_ID: str = Field(default="", description="Google OAuth Client ID for Gmail API")
    GOOGLE_CLIENT_SECRET: SecretStr = Field(default=SecretStr(""), description="Google OAuth Client Secret")
    GOOGLE_REFRESH_TOKEN: SecretStr = Field(default=SecretStr(""), description="Google OAuth Refresh Token for Gmail API")

    # API Gateway (for Telegram notifications)
    API_GATEWAY_URL: str = Field(default="", description="API Gateway base URL for internal service calls")

    # Supabase Storage (legacy - use R2 instead)
    SUPABASE_URL: str = Field(default="", description="Supabase project URL")
    SUPABASE_SERVICE_KEY: SecretStr = Field(default=SecretStr(""), description="Supabase service role key for backend operations")
    SUPABASE_STORAGE_BUCKET: str = Field(default="promotions", description="Supabase storage bucket for promotion media")

    # Cloudflare R2 Storage for Media (S3-compatible)
    # Separate from backup R2 credentials for better access control
    R2_MEDIA_ACCOUNT_ID: str = Field(default="", description="Cloudflare R2 account ID for media storage")
    R2_MEDIA_ACCESS_KEY: str = Field(default="", description="R2 access key ID for media storage")
    R2_MEDIA_SECRET_KEY: SecretStr = Field(default=SecretStr(""), description="R2 secret access key for media storage")
    R2_MEDIA_BUCKET: str = Field(default="facebook-automation-media", description="R2 bucket name for media storage")
    R2_MEDIA_PUBLIC_URL: str = Field(default="", description="R2 public URL (e.g., https://pub-xxxxx.r2.dev or custom domain)")

    # MongoDB GridFS for Ads Alert Media Storage
    MONGO_URL_ADS_ALERT: str = Field(default="", description="MongoDB connection string for ads alert media storage (GridFS)")

    # API Server settings
    API_HOST: str = Field(default="0.0.0.0", description="API server host")
    API_PORT: int = Field(default=8000, description="API server port", ge=1024, le=65535)

    # Background Job Configuration
    TOKEN_REFRESH_INTERVAL: int = Field(default=3600, description="Token refresh check interval in seconds (default: 1 hour)", ge=60)
    AUTOMATION_CHECK_INTERVAL: int = Field(default=60, description="Automation scheduler check interval in seconds (default: 1 minute)", ge=10)
    CLEANUP_INTERVAL: int = Field(default=86400, description="Cleanup job interval in seconds (default: 24 hours)", ge=3600)

    # Backup Configuration
    BACKUP_ENABLED: bool = Field(default=True, description="Enable automated daily backups to R2")
    BACKUP_HOUR_UTC: int = Field(default=2, description="Hour of day to run backup (0-23 UTC)", ge=0, le=23)

    # Rate Limiting Configuration
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="Maximum requests per minute per IP", ge=1)
    RATE_LIMIT_VIOLATION_THRESHOLD: int = Field(default=5, description="Violations before auto-ban", ge=1)
    RATE_LIMIT_AUTO_BAN_DURATION: int = Field(default=86400, description="Auto-ban duration in seconds (default: 24 hours)", ge=60)

    # IP Blocking Configuration
    TRUST_PROXY_HEADERS: bool = Field(default=True, description="Trust X-Forwarded-For headers from proxies")

    # Refresh Token Cookie Configuration
    REFRESH_TOKEN_COOKIE_NAME: str = Field(default="refresh_token", description="Name of the refresh token cookie")
    REFRESH_TOKEN_COOKIE_SECURE: bool = Field(default=True, description="Require HTTPS for refresh token cookie")
    REFRESH_TOKEN_COOKIE_SAMESITE: Literal["lax", "strict", "none"] = Field(default="none", description="SameSite attribute for refresh token cookie")
    REFRESH_TOKEN_COOKIE_DOMAIN: str | None = Field(default=None, description="Domain for refresh token cookie (None for current domain)")

    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate DATABASE_URL format"""
        valid_prefixes = (
            'postgresql://',
            'postgresql+psycopg://',      # psycopg3 format
            'postgresql+psycopg2://',     # psycopg2 format (legacy)
            'postgres://'                 # Heroku/Railway common format
        )
        if not v.startswith(valid_prefixes):
            raise ValueError(f'DATABASE_URL must start with one of: {", ".join(valid_prefixes)}')
        return v

    @field_validator('FB_SCOPES', 'TIKTOK_SCOPES')
    @classmethod
    def validate_scopes(cls, v: str) -> str:
        """Validate and normalize OAuth scopes"""
        if not v:
            raise ValueError('OAuth scopes cannot be empty')
        # Normalize scopes by removing extra whitespace
        return ','.join(scope.strip() for scope in v.split(',') if scope.strip())

    @property
    def database_url_safe(self) -> str:
        """Get database URL with credentials masked for logging"""
        if '@' in self.DATABASE_URL:
            protocol, rest = self.DATABASE_URL.split('://', 1)
            if '@' in rest:
                credentials, host_db = rest.split('@', 1)
                return f"{protocol}://<credentials>@{host_db}"
        return self.DATABASE_URL

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.

    Uses lru_cache to ensure settings are loaded only once
    and reused across the application lifecycle.
    """
    return Settings()
