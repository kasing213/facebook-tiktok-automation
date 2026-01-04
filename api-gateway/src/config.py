# api-gateway/src/config.py
"""Configuration settings for API Gateway."""

from typing import Optional
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

    # PostgreSQL (required for user linking)
    DATABASE_URL: str = Field(default="", description="PostgreSQL connection string")

    # Core API URL
    CORE_API_URL: str = Field(
        default="http://localhost:8000",
        description="Facebook-automation core API URL"
    )

    # MongoDB - Invoice Generator
    MONGO_URL_INVOICE: Optional[str] = Field(default=None)
    MONGO_DB_INVOICE: str = Field(default="invoice_generator")

    # MongoDB - Scriptclient
    MONGO_URL_SCRIPTCLIENT: Optional[str] = Field(default=None)
    MONGO_DB_SCRIPTCLIENT: str = Field(default="scriptclient")

    # MongoDB - Audit Sales
    MONGO_URL_AUDIT_SALES: Optional[str] = Field(default=None)
    MONGO_DB_AUDIT_SALES: str = Field(default="audit_sales")

    # MongoDB - Ads Alert
    MONGO_URL_ADS_ALERT: Optional[str] = Field(default=None)
    MONGO_DB_ADS_ALERT: str = Field(default="ads_alert")

    # Server
    PORT: int = Field(default=8001)


# Global settings instance
settings = Settings()
