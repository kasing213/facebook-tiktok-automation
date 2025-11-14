# app/deps.py
from typing import Generator, Annotated, Optional
import logging
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings, Settings
from app.core.db import get_db as get_database_session

# Service imports
from app.services import TenantService, AuthService, AutomationService

# Repository imports
from app.repositories import (
    TenantRepository, UserRepository, AdTokenRepository,
    DestinationRepository, AutomationRepository
)

# Integration imports
from app.integrations.oauth import FacebookOAuth, TikTokOAuth, OAuthProvider, FacebookAPIClient
from app.integrations.tiktok import TikTokService
from app.core.crypto import load_encryptor, TokenEncryptor

# --- Logging ---
_logger = logging.getLogger("app")
if not _logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    ))
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)

def get_logger() -> logging.Logger:
    return _logger

# --- Configuration ---
def get_settings_dep() -> Settings:
    """FastAPI dependency for settings"""
    return get_settings()

# --- Database ---
def get_db() -> Generator[Session, None, None]:
    """Database session dependency with improved error handling"""
    yield from get_database_session()

# --- Repositories ---
def get_tenant_repository(db: Session = Depends(get_db)) -> TenantRepository:
    """Get tenant repository"""
    return TenantRepository(db)

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Get user repository"""
    return UserRepository(db)

def get_ad_token_repository(db: Session = Depends(get_db)) -> AdTokenRepository:
    """Get ad token repository"""
    return AdTokenRepository(db)

def get_destination_repository(db: Session = Depends(get_db)) -> DestinationRepository:
    """Get destination repository"""
    return DestinationRepository(db)

def get_automation_repository(db: Session = Depends(get_db)) -> AutomationRepository:
    """Get automation repository"""
    return AutomationRepository(db)

# --- Integration Services ---
_encryptor_cache: Optional[TokenEncryptor] = None

def get_token_encryptor(settings: Settings = Depends(get_settings_dep)) -> TokenEncryptor:
    """Get cached token encryptor"""
    global _encryptor_cache
    if _encryptor_cache is None:
        _encryptor_cache = load_encryptor(settings.MASTER_SECRET_KEY.get_secret_value())
    return _encryptor_cache

# --- Services ---
def get_tenant_service(db: Session = Depends(get_db)) -> TenantService:
    """Get tenant service"""
    return TenantService(db)

def get_auth_service(
    db: Session = Depends(get_db),
    encryptor: TokenEncryptor = Depends(get_token_encryptor)
) -> AuthService:
    """Get authentication service"""
    return AuthService(db, encryptor)

def get_automation_service(db: Session = Depends(get_db)) -> AutomationService:
    """Get automation service"""
    return AutomationService(db)

def get_oauth_provider(settings: Settings = Depends(get_settings_dep)) -> OAuthProvider:
    """Get base OAuth provider"""
    return OAuthProvider(settings)

def get_facebook_oauth(settings: Settings = Depends(get_settings_dep)) -> FacebookOAuth:
    """Get Facebook OAuth provider"""
    return FacebookOAuth(settings)

def get_tiktok_oauth(settings: Settings = Depends(get_settings_dep)) -> TikTokOAuth:
    """Get TikTok OAuth provider"""
    return TikTokOAuth(settings)

def get_tiktok_service(db: Session = Depends(get_db)) -> TikTokService:
    """Get TikTok service"""
    return TikTokService(db)

# --- Type aliases for easier imports ---
DatabaseSession = Annotated[Session, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
LoggerDep = Annotated[logging.Logger, Depends(get_logger)]

# Repository dependencies
TenantRepo = Annotated[TenantRepository, Depends(get_tenant_repository)]
UserRepo = Annotated[UserRepository, Depends(get_user_repository)]
AdTokenRepo = Annotated[AdTokenRepository, Depends(get_ad_token_repository)]
DestinationRepo = Annotated[DestinationRepository, Depends(get_destination_repository)]
AutomationRepo = Annotated[AutomationRepository, Depends(get_automation_repository)]

# Service dependencies
TenantSvc = Annotated[TenantService, Depends(get_tenant_service)]
AuthSvc = Annotated[AuthService, Depends(get_auth_service)]
AutomationSvc = Annotated[AutomationService, Depends(get_automation_service)]

# Integration dependencies
TokenEnc = Annotated[TokenEncryptor, Depends(get_token_encryptor)]
FacebookOAuthProvider = Annotated[FacebookOAuth, Depends(get_facebook_oauth)]
TikTokOAuthProvider = Annotated[TikTokOAuth, Depends(get_tiktok_oauth)]
TikTokSvc = Annotated[TikTokService, Depends(get_tiktok_service)]
