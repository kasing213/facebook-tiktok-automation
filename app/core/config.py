from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Supports configuration through:
    - Environment variables
    - .env file
    - Default values for non-sensitive settings
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"  # Allow extra env vars for flexibility
    )

    # Application settings
    ENV: Literal["dev", "staging", "prod"] = "dev"
    BASE_URL: AnyHttpUrl = Field(default="http://localhost:8000", description="Base URL for the application")

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

    # TikTok integration
    TIKTOK_CLIENT_KEY: str = Field(..., description="TikTok Client Key")
    TIKTOK_CLIENT_SECRET: SecretStr = Field(..., description="TikTok Client Secret")
    TIKTOK_SCOPES: str = Field(default="user.info.basic", description="TikTok API scopes")

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: SecretStr = Field(..., description="Telegram Bot Token")

    # API Server settings
    API_HOST: str = Field(default="0.0.0.0", description="API server host")
    API_PORT: int = Field(default=8000, description="API server port")

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.

    Uses lru_cache to ensure settings are loaded only once
    and reused across the application lifecycle.
    """
    return Settings()
