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
    FB_SCOPES: str = Field(default="ads_read", description="Facebook API scopes")
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

    # Stripe Integration
    STRIPE_SECRET_KEY: SecretStr = Field(default=SecretStr(""), description="Stripe secret key")
    STRIPE_WEBHOOK_SECRET: SecretStr = Field(default=SecretStr(""), description="Stripe webhook signing secret")
    STRIPE_PRICE_ID_MONTHLY: str = Field(default="", description="Stripe monthly price ID for Pro subscription")
    STRIPE_PRICE_ID_YEARLY: str = Field(default="", description="Stripe yearly price ID for Pro subscription")

    # Invoice Mock Mode (for testing without external API)
    INVOICE_MOCK_MODE: bool = Field(default=False, description="Use mock in-memory Invoice API instead of external service")
    INVOICE_TIER_ENFORCEMENT: bool = Field(default=True, description="Enforce Pro tier for PDF/Export features (disable for testing)")

    # API Server settings
    API_HOST: str = Field(default="0.0.0.0", description="API server host")
    API_PORT: int = Field(default=8000, description="API server port", ge=1024, le=65535)

    # Background Job Configuration
    TOKEN_REFRESH_INTERVAL: int = Field(default=3600, description="Token refresh check interval in seconds (default: 1 hour)", ge=60)
    AUTOMATION_CHECK_INTERVAL: int = Field(default=60, description="Automation scheduler check interval in seconds (default: 1 minute)", ge=10)
    CLEANUP_INTERVAL: int = Field(default=86400, description="Cleanup job interval in seconds (default: 24 hours)", ge=3600)

    # Rate Limiting Configuration
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="Maximum requests per minute per IP", ge=1)
    RATE_LIMIT_VIOLATION_THRESHOLD: int = Field(default=5, description="Violations before auto-ban", ge=1)
    RATE_LIMIT_AUTO_BAN_DURATION: int = Field(default=86400, description="Auto-ban duration in seconds (default: 24 hours)", ge=60)

    # IP Blocking Configuration
    TRUST_PROXY_HEADERS: bool = Field(default=True, description="Trust X-Forwarded-For headers from proxies")

    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate DATABASE_URL format"""
        if not v.startswith(('postgresql://', 'postgresql+psycopg2://')):
            raise ValueError('DATABASE_URL must be a valid PostgreSQL connection string')
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
