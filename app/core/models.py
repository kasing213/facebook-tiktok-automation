# app/core/models.py
import enum, uuid, datetime as dt
from sqlalchemy import (
    Column, String, DateTime, Enum, JSON, ForeignKey, UniqueConstraint,
    Boolean, Integer, Text, Index, text, ARRAY
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

class TokenType(str, enum.Enum):
    user = "user"
    page = "page"

class IPRuleType(str, enum.Enum):
    whitelist = "whitelist"
    blacklist = "blacklist"
    auto_banned = "auto_banned"

class SubscriptionTier(str, enum.Enum):
    free = "free"
    pro = "pro"

class SubscriptionStatus(str, enum.Enum):
    active = "active"
    cancelled = "cancelled"
    past_due = "past_due"
    incomplete = "incomplete"

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
    telegram_username = Column(String(100), nullable=True)  # Telegram @username
    telegram_linked_at = Column(DateTime(timezone=True), nullable=True)  # When Telegram was linked
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
    """OAuth tokens for social media platforms per user"""
    __tablename__ = "ad_token"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)  # NOW REQUIRED
    social_identity_id = Column(UUID(as_uuid=True), ForeignKey("social_identity.id"), nullable=True)
    facebook_page_id = Column(UUID(as_uuid=True), ForeignKey("facebook_page.id"), nullable=True)
    platform = Column(Enum(Platform), nullable=False)
    token_type = Column(Enum(TokenType), nullable=False, default=TokenType.user)
    account_ref = Column(String(255), nullable=True)  # DEPRECATED: kept for backward compat
    account_name = Column(String(255), nullable=True)
    access_token_enc = Column(String, nullable=False)  # encrypted
    refresh_token_enc = Column(String, nullable=True)  # encrypted
    scope = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # UTC
    is_valid = Column(Boolean, default=True, nullable=False)
    last_validated = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete
    meta = Column(JSON, nullable=True)  # raw payloads / debug info
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="ad_tokens")
    user = relationship("User", back_populates="ad_tokens")
    social_identity = relationship("SocialIdentity", back_populates="ad_tokens")
    facebook_page = relationship("FacebookPage", back_populates="ad_tokens")

    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "platform", "account_ref", name="uq_token_tenant_user_platform_account"),
        Index("idx_ad_token_platform", "platform"),
        Index("idx_ad_token_expires", "expires_at"),
        Index("idx_ad_token_user", "user_id"),
        Index("idx_ad_token_social_identity", "social_identity_id"),
        Index("idx_ad_token_facebook_page", "facebook_page_id"),
        Index("idx_ad_token_deleted", "deleted_at"),
        Index(
            "idx_ad_token_one_active_user_token",
            "tenant_id", "user_id", "platform",
            unique=True,
            postgresql_where=text("deleted_at IS NULL AND token_type = 'user'")
        ),
    )

class SocialIdentity(Base):
    """Represents a user's identity on a social platform (Facebook, TikTok)"""
    __tablename__ = "social_identity"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    platform = Column(Enum(Platform), nullable=False)
    platform_user_id = Column(String(255), nullable=False)  # FB user ID or TikTok open_id
    facebook_user_id = Column(String(255), nullable=True)  # CRITICAL: Real FB user ID (stable anchor)
    platform_username = Column(String(255), nullable=True)
    display_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    avatar_url = Column(Text, nullable=True)
    profile_data = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant", backref="social_identities")
    user = relationship("User", backref="social_identities")
    ad_tokens = relationship("AdToken", back_populates="social_identity")
    facebook_pages = relationship("FacebookPage", back_populates="social_identity", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("platform", "platform_user_id", name="uq_social_identity_platform_user"),
        UniqueConstraint("tenant_id", "user_id", "platform", name="uq_social_identity_tenant_user_platform"),
        Index("idx_social_identity_tenant_user", "tenant_id", "user_id"),
        Index("idx_social_identity_platform_user", "platform", "platform_user_id"),
    )

class FacebookPage(Base):
    """Facebook Page managed by a user's Facebook account"""
    __tablename__ = "facebook_page"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    social_identity_id = Column(UUID(as_uuid=True), ForeignKey("social_identity.id"), nullable=False)
    page_id = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    category = Column(String(255), nullable=True)
    tasks = Column(ARRAY(String), nullable=True)  # Array of permissions
    page_data = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow, nullable=False)

    # Relationships
    social_identity = relationship("SocialIdentity", back_populates="facebook_pages")
    ad_tokens = relationship("AdToken", back_populates="facebook_page")

    __table_args__ = (
        Index("idx_facebook_page_identity", "social_identity_id"),
        Index("idx_facebook_page_page_id", "page_id"),
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

class IPAccessRule(Base):
    """IP whitelist/blacklist rules for access control"""
    __tablename__ = "ip_access_rule"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ip_address = Column(String(45), nullable=False)  # IPv6 max length
    rule_type = Column(Enum(IPRuleType), nullable=False)
    reason = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # For temporary bans
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)  # Admin who created rule

    __table_args__ = (
        Index("idx_ip_access_rule_ip", "ip_address"),
        Index("idx_ip_access_rule_type", "rule_type"),
        Index("idx_ip_access_rule_active", "is_active"),
        Index("idx_ip_access_rule_expires", "expires_at"),
    )

class RateLimitViolation(Base):
    """Rate limit violation tracking for automatic IP banning"""
    __tablename__ = "rate_limit_violation"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ip_address = Column(String(45), nullable=False)
    endpoint = Column(String(500), nullable=False)
    violation_count = Column(Integer, default=1, nullable=False)
    last_violation_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    auto_banned = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_rate_limit_violation_ip", "ip_address"),
        Index("idx_rate_limit_violation_last", "last_violation_at"),
        Index("idx_rate_limit_violation_ip_endpoint", "ip_address", "endpoint"),
    )


class TelegramLinkCode(Base):
    """Temporary codes for linking Telegram accounts to dashboard users"""
    __tablename__ = "telegram_link_code"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(32), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    telegram_user_id = Column(String(50), nullable=True)  # Filled when code is consumed

    # Relationships
    user = relationship("User", backref="telegram_link_codes")
    tenant = relationship("Tenant", backref="telegram_link_codes")

    __table_args__ = (
        Index("idx_telegram_link_code_code", "code", unique=True),
        Index("idx_telegram_link_code_expires", "expires_at"),
        Index("idx_telegram_link_code_user", "user_id"),
    )


class RefreshToken(Base):
    """Refresh tokens for rotating token authentication"""
    __tablename__ = "refresh_token"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(64), nullable=False, unique=True)  # SHA-256 hash
    family_id = Column(UUID(as_uuid=True), nullable=False)  # For token rotation detection
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    replaced_by_id = Column(UUID(as_uuid=True), nullable=True)  # Points to new token if rotated
    device_info = Column(String(255), nullable=True)  # User agent/device fingerprint
    ip_address = Column(String(45), nullable=True)

    # Relationships
    user = relationship("User", backref="refresh_tokens")
    tenant = relationship("Tenant", backref="refresh_tokens")

    __table_args__ = (
        Index("idx_refresh_token_hash", "token_hash", unique=True),
        Index("idx_refresh_token_user", "user_id"),
        Index("idx_refresh_token_family", "family_id"),
        Index("idx_refresh_token_expires", "expires_at"),
    )


class TokenBlacklist(Base):
    """Blacklisted JWT tokens (for logout and security revocations)"""
    __tablename__ = "token_blacklist"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jti = Column(String(36), nullable=False, unique=True)  # JWT ID claim
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)  # When token naturally expires
    revoked_at = Column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)
    reason = Column(String(50), nullable=True)  # 'logout', 'password_change', 'security_revoke'

    __table_args__ = (
        Index("idx_token_blacklist_jti", "jti", unique=True),
        Index("idx_token_blacklist_expires", "expires_at"),
        Index("idx_token_blacklist_user", "user_id"),
    )


class Subscription(Base):
    """User subscription for tiered features (Invoice Pro, etc.)"""
    __tablename__ = "subscription"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)

    # Stripe fields
    stripe_customer_id = Column(String(255), nullable=True, unique=True)
    stripe_subscription_id = Column(String(255), nullable=True, unique=True)

    # Subscription details
    tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.free, nullable=False)
    status = Column(Enum(SubscriptionStatus), nullable=True)  # null for free tier
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc),
                       onupdate=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", backref="subscription", uselist=False)
    tenant = relationship("Tenant", backref="subscriptions")

    __table_args__ = (
        Index("idx_subscription_user", "user_id", unique=True),
        Index("idx_subscription_tenant", "tenant_id"),
        Index("idx_subscription_stripe_customer", "stripe_customer_id"),
        Index("idx_subscription_stripe_sub", "stripe_subscription_id"),
        Index("idx_subscription_tier", "tier"),
    )

