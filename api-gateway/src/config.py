# api-gateway/src/config.py
"""Configuration settings for API Gateway."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """API Gateway settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )

    # Telegram Bot (bot won't start without it but app will run)
    TELEGRAM_BOT_TOKEN: str = Field(default="", description="Telegram Bot Token")
    TELEGRAM_BOT_USERNAME: str = Field(default="KS_automations_bot", description="Telegram Bot Username")

    # PostgreSQL (required for all operations)
    DATABASE_URL: str = Field(default="", description="PostgreSQL connection string")

    # Core API URL (for Telegram linking - calls main backend)
    CORE_API_URL: str = Field(
        default="http://localhost:8000",
        description="Facebook-automation core API URL"
    )

    # Server
    PORT: int = Field(default=8001)

    # OCR Verification Service
    OCR_API_URL: str = Field(default="", description="OCR verification service URL")
    OCR_API_KEY: str = Field(default="", description="OCR API authentication key")
    OCR_MOCK_MODE: bool = Field(default=True, description="Use mock OCR when API not configured")

    # Service Authentication
    MASTER_SECRET_KEY: str = Field(..., description="Master secret key for service JWT validation")


# Global settings instance
settings = Settings()
