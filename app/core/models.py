# app/core/models.py
import enum, uuid, datetime as dt
from sqlalchemy import (
    Column, String, DateTime, Enum, JSON, ForeignKey, UniqueConstraint,
    Boolean, Integer, Text, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Platform(str, enum.Enum):
    facebook = "facebook"
    tiktok = "tiktok"

class UserRole(str, enum.Enum):
    admin = "admin"
    user = "user"
    viewer = "viewer"

class DestinationType(str, enum.Enum):
    telegram_chat = "telegram_chat"
    webhook = "webhook"
    email = "email"

class AutomationStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    stopped = "stopped"
    error = "error"

class AutomationType(str, enum.Enum):
    scheduled_report = "scheduled_report"
    alert = "alert"
    data_sync = "data_sync"

# Multi-tenant core models
class Tenant(Base):
    """Core tenant model for multi-tenant isolation"""
    __tablename__ = "tenant"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False, unique=True)  # URL-friendly identifier
    is_active = Column(Boolean, default=True, nullable=False)
    settings = Column(JSON, nullable=True)  # tenant-specific configuration
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow, nullable=False)

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    ad_tokens = relationship("AdToken", back_populates="tenant", cascade="all, delete-orphan")
    destinations = relationship("Destination", back_populates="tenant", cascade="all, delete-orphan")
    automations = relationship("Automation", back_populates="tenant", cascade="all, delete-orphan")

class User(Base):
    """Users within a tenant - supports multiple users per tenant"""
    __tablename__ = "user"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id"), nullable=False)
    telegram_user_id = Column(String(50), nullable=True)  # Telegram user ID
    email = Column(String(255), nullable=True)
    username = Column(String(100), nullable=True)
    password_hash = Column(String(255), nullable=True)  # For web-based authentication
    email_verified = Column(Boolean, default=False, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.user, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)
    profile_data = Column(JSON, nullable=True)  # Additional profile information
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    ad_tokens = relationship("AdToken", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("tenant_id", "telegram_user_id", name="uq_user_tenant_telegram"),
        UniqueConstraint("tenant_id", "email", name="uq_user_tenant_email"),
        Index("idx_user_telegram_id", "telegram_user_id"),
    )

class Destination(Base):
    """Where to send reports/alerts - Telegram chats, webhooks, email"""
    __tablename__ = "destination"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id"), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(Enum(DestinationType), nullable=False)
    config = Column(JSON, nullable=False)  # type-specific configuration
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="destinations")
    automations = relationship("Automation", back_populates="destination")

    __table_args__ = (
        Index("idx_destination_tenant_type", "tenant_id", "type"),
    )

class AdToken(Base):
    """OAuth tokens for social media platforms per tenant"""
    __tablename__ = "ad_token"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)
    platform = Column(Enum(Platform), nullable=False)
    account_ref = Column(String(255), nullable=True)  # e.g., act_123, or TikTok open_id
    account_name = Column(String(255), nullable=True)  # human-readable account name
    access_token_enc = Column(String, nullable=False)  # encrypted
    refresh_token_enc = Column(String, nullable=True)  # encrypted
    scope = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # UTC
    is_valid = Column(Boolean, default=True, nullable=False)
    last_validated = Column(DateTime, nullable=True)
    meta = Column(JSON, nullable=True)  # raw payloads / debug info
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="ad_tokens")
    user = relationship("User", back_populates="ad_tokens")

    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "platform", "account_ref", name="uq_token_tenant_user_platform_account"),
        Index("idx_ad_token_platform", "platform"),
        Index("idx_ad_token_expires", "expires_at"),
        Index("idx_ad_token_user", "user_id"),
    )

class Automation(Base):
    """Automation rules for reports, alerts, and data syncing"""
    __tablename__ = "automation"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id"), nullable=False)
    destination_id = Column(UUID(as_uuid=True), ForeignKey("destination.id"), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(Enum(AutomationType), nullable=False)
    status = Column(Enum(AutomationStatus), default=AutomationStatus.active, nullable=False)

    # Scheduling and configuration
    schedule_config = Column(JSON, nullable=True)  # cron-like scheduling
    automation_config = Column(JSON, nullable=False)  # automation-specific settings
    platforms = Column(JSON, nullable=True)  # which platforms to include

    # Execution tracking
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    run_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="automations")
    destination = relationship("Destination", back_populates="automations")
    runs = relationship("AutomationRun", back_populates="automation", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_automation_next_run", "next_run"),
        Index("idx_automation_tenant_status", "tenant_id", "status"),
    )

class AutomationRun(Base):
    """Execution history and logs for automations"""
    __tablename__ = "automation_run"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    automation_id = Column(UUID(as_uuid=True), ForeignKey("automation.id"), nullable=False)
    started_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False)  # running, completed, failed
    result = Column(JSON, nullable=True)  # execution results
    error_message = Column(Text, nullable=True)
    logs = Column(JSON, nullable=True)  # detailed execution logs

    # Relationships
    automation = relationship("Automation", back_populates="runs")

    __table_args__ = (
        Index("idx_automation_run_started", "started_at"),
        Index("idx_automation_run_automation_status", "automation_id", "status"),
    )

