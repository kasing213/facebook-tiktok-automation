"""
Pydantic schemas for request/response validation and serialization.

This module contains all the Pydantic models used for API validation,
request parsing, and response serialization throughout the application.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# Enums
class PlatformType(str, Enum):
    """Supported social media platforms."""
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"


class UserRole(str, Enum):
    """User roles for access control."""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class DestinationType(str, Enum):
    """Types of automation destinations."""
    TELEGRAM_CHAT = "telegram_chat"
    WEBHOOK = "webhook"
    EMAIL = "email"


class AutomationType(str, Enum):
    """Types of automations."""
    SCHEDULED_REPORT = "scheduled_report"
    ALERT = "alert"
    DATA_SYNC = "data_sync"


class AutomationStatus(str, Enum):
    """Automation execution status."""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(from_attributes=True)


# Tenant schemas
class TenantBase(BaseSchema):
    """Base tenant schema."""
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True
    settings: Optional[Dict[str, Any]] = None


class TenantCreate(TenantBase):
    """Schema for creating a tenant."""
    pass


class TenantUpdate(BaseSchema):
    """Schema for updating a tenant."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None


class TenantResponse(TenantBase):
    """Schema for tenant response."""
    id: UUID
    created_at: datetime
    updated_at: datetime


# User schemas
class UserBase(BaseSchema):
    """Base user schema."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    role: UserRole = UserRole.USER
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, max_length=100)
    tenant_id: Optional[UUID] = None


class UserUpdate(BaseSchema):
    """Schema for updating user."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    profile_data: Optional[Dict[str, Any]] = None


class UserResponse(UserBase):
    """Schema for user response."""
    id: UUID
    tenant_id: UUID
    email_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class UserLogin(BaseSchema):
    """Schema for user login."""
    username: str
    password: str


class UserToken(BaseSchema):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# AdToken schemas
class AdTokenBase(BaseSchema):
    """Base ad token schema."""
    platform: PlatformType
    account_ref: str = Field(..., min_length=1, max_length=200)
    account_name: Optional[str] = Field(None, max_length=200)
    scope: Optional[str] = None
    is_valid: bool = True


class AdTokenCreate(AdTokenBase):
    """Schema for creating an ad token."""
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    meta: Optional[Dict[str, Any]] = None


class AdTokenUpdate(BaseSchema):
    """Schema for updating an ad token."""
    account_name: Optional[str] = None
    is_valid: Optional[bool] = None
    meta: Optional[Dict[str, Any]] = None


class AdTokenResponse(AdTokenBase):
    """Schema for ad token response (no sensitive data)."""
    id: UUID
    tenant_id: UUID
    expires_at: Optional[datetime]
    last_validated: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# Destination schemas
class DestinationBase(BaseSchema):
    """Base destination schema."""
    name: str = Field(..., min_length=1, max_length=200)
    type: DestinationType
    config: Dict[str, Any]
    is_active: bool = True


class DestinationCreate(DestinationBase):
    """Schema for creating a destination."""
    pass


class DestinationUpdate(BaseSchema):
    """Schema for updating a destination."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class DestinationResponse(DestinationBase):
    """Schema for destination response."""
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime


# Automation schemas
class AutomationBase(BaseSchema):
    """Base automation schema."""
    name: str = Field(..., min_length=1, max_length=200)
    type: AutomationType
    status: AutomationStatus = AutomationStatus.ACTIVE
    schedule_config: Dict[str, Any]
    automation_config: Dict[str, Any]
    platforms: List[PlatformType]


class AutomationCreate(AutomationBase):
    """Schema for creating an automation."""
    destination_id: UUID


class AutomationUpdate(BaseSchema):
    """Schema for updating an automation."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[AutomationStatus] = None
    schedule_config: Optional[Dict[str, Any]] = None
    automation_config: Optional[Dict[str, Any]] = None
    platforms: Optional[List[PlatformType]] = None
    destination_id: Optional[UUID] = None


class AutomationResponse(AutomationBase):
    """Schema for automation response."""
    id: UUID
    tenant_id: UUID
    destination_id: UUID
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    run_count: int
    error_count: int
    created_at: datetime
    updated_at: datetime


# Automation Run schemas
class AutomationRunBase(BaseSchema):
    """Base automation run schema."""
    status: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    logs: Optional[Dict[str, Any]] = None


class AutomationRunResponse(AutomationRunBase):
    """Schema for automation run response."""
    id: UUID
    automation_id: UUID
    started_at: datetime
    completed_at: Optional[datetime]


# Health check schema
class HealthResponse(BaseSchema):
    """Schema for health check response."""
    status: str
    timestamp: datetime
    database: str
    version: str
