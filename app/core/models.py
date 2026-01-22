# app/core/models.py
import enum, uuid, datetime as dt
from sqlalchemy import (
    Column, String, DateTime, Enum, JSON, ForeignKey, UniqueConstraint,
    Boolean, Integer, Text, Index, text, ARRAY, Numeric
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
    invoice_plus = "invoice_plus"  # $10/month - Invoice + Inventory
    marketing_plus = "marketing_plus"  # $10/month - Social + Ads Alerts
    pro = "pro"  # $20/month - Both products combined

class SubscriptionStatus(str, enum.Enum):
    active = "active"
    cancelled = "cancelled"
    past_due = "past_due"
    incomplete = "incomplete"

class MovementType(str, enum.Enum):
    in_stock = "in"
    out_stock = "out"
    adjustment = "adjustment"

class PromotionStatus(str, enum.Enum):
    draft = "draft"
    scheduled = "scheduled"
    sent = "sent"
    cancelled = "cancelled"

class PromotionMediaType(str, enum.Enum):
    text = "text"
    image = "image"
    video = "video"
    document = "document"
    mixed = "mixed"

class PromotionTargetType(str, enum.Enum):
    all = "all"
    selected = "selected"

class PromotionCustomerTargetType(str, enum.Enum):
    """Customer-based targeting for promotions"""
    none = "none"                    # Use existing chat targeting
    all_customers = "all_customers"  # All invoice customers with linked Telegram
    selected_customers = "selected_customers"  # Specific customers by ID

class BroadcastStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"

class LoginAttemptResult(str, enum.Enum):
    success = "success"
    failure = "failure"

# Multi-tenant core models
class Tenant(Base):
    """Core tenant model for multi-tenant isolation"""
    __tablename__ = "tenant"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False, unique=True)  # URL-friendly identifier
    is_active = Column(Boolean, default=True, nullable=False)
    settings = Column(JSON, nullable=True)  # tenant-specific configuration

    # Usage limits (per tier)
    invoice_limit = Column(Integer, default=50, nullable=False)
    product_limit = Column(Integer, default=100, nullable=False)
    customer_limit = Column(Integer, default=50, nullable=False)
    team_member_limit = Column(Integer, default=1, nullable=False)  # Free tier: owner only
    storage_limit_mb = Column(Integer, default=500, nullable=False)
    api_calls_limit_hourly = Column(Integer, default=100, nullable=False)

    # Marketing/Promotion limits (anti-abuse)
    promotion_limit = Column(Integer, default=0, nullable=False)  # Free: 0, Marketing Plus: 10
    broadcast_recipient_limit = Column(Integer, default=0, nullable=False)  # Free: 0, Marketing Plus: 500
    current_month_promotions = Column(Integer, default=0, nullable=False)
    current_month_broadcasts = Column(Integer, default=0, nullable=False)  # Total recipients this month

    # Monthly usage counters (reset on 1st of month)
    current_month_invoices = Column(Integer, default=0, nullable=False)
    current_month_exports = Column(Integer, default=0, nullable=False)
    current_month_reset_at = Column(DateTime(timezone=True), nullable=True)

    # Storage tracking (cumulative, does not reset)
    storage_used_mb = Column(Numeric(10, 2), default=0, nullable=False)

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
    email_verified_at = Column(DateTime, nullable=True)  # When email was verified
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


class EmailVerificationToken(Base):
    """Email verification tokens for user email confirmation"""
    __tablename__ = "email_verification_token"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(64), nullable=False, unique=True)  # SHA-256 hash of the token
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", backref="email_verification_tokens")

    __table_args__ = (
        Index("idx_email_verification_token", "token", unique=True),
        Index("idx_email_verification_user", "user_id"),
        Index("idx_email_verification_expires", "expires_at"),
    )


class PasswordResetToken(Base):
    """Password reset tokens for forgot password flow"""
    __tablename__ = "password_reset_token"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(64), nullable=False, unique=True)  # SHA-256 hash of the token
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", backref="password_reset_tokens")

    __table_args__ = (
        Index("idx_password_reset_token", "token", unique=True),
        Index("idx_password_reset_user", "user_id"),
        Index("idx_password_reset_expires", "expires_at"),
    )


class LoginAttempt(Base):
    """Track login attempts for account lockout and security monitoring"""
    __tablename__ = "login_attempt"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False)  # Email attempted (may not exist)
    ip_address = Column(String(45), nullable=False)  # IPv4/IPv6 support
    user_agent = Column(Text, nullable=True)
    result = Column(Enum(LoginAttemptResult), nullable=False)
    failure_reason = Column(String(255), nullable=True)  # "invalid_credentials", "account_locked", etc.
    attempted_at = Column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_login_attempt_email", "email"),
        Index("idx_login_attempt_ip", "ip_address"),
        Index("idx_login_attempt_attempted_at", "attempted_at"),
        Index("idx_login_attempt_result", "result"),
        Index("idx_login_attempt_email_time", "email", "attempted_at"),  # For account lockout queries
        Index("idx_login_attempt_ip_time", "ip_address", "attempted_at"),  # For IP-based lockout
    )


class AccountLockout(Base):
    """Track account lockouts due to failed login attempts"""
    __tablename__ = "account_lockout"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=True)  # IP that triggered the lockout (optional)
    lockout_reason = Column(String(255), nullable=False)  # "too_many_failures", "security_event"
    failed_attempts_count = Column(Integer, nullable=False, default=0)
    locked_at = Column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)
    unlock_at = Column(DateTime(timezone=True), nullable=False)  # When account will auto-unlock
    unlocked_at = Column(DateTime(timezone=True), nullable=True)  # Manual unlock timestamp
    unlocked_by = Column(String(255), nullable=True)  # Admin who unlocked (if manual)

    __table_args__ = (
        Index("idx_account_lockout_email", "email"),
        Index("idx_account_lockout_unlock_at", "unlock_at"),
        Index("idx_account_lockout_active", "email", "unlocked_at"),  # For checking active lockouts
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


class Product(Base):
    """Products for inventory tracking"""
    __tablename__ = "products"
    __table_args__ = {"schema": "inventory"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    sku = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    unit_price = Column(Integer, nullable=False, default=0)  # Store in smallest currency unit (e.g., cents, riels)
    cost_price = Column(Integer, nullable=True)  # Store in smallest currency unit
    currency = Column(String(3), nullable=False, default="KHR")
    current_stock = Column(Integer, nullable=False, default=0)
    low_stock_threshold = Column(Integer, nullable=True, default=10)
    track_stock = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant", backref="products")
    stock_movements = relationship("StockMovement", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("tenant_id", "sku", name="uq_products_tenant_sku"),
        Index("idx_products_tenant", "tenant_id"),
        Index("idx_products_sku", "sku"),
        Index("idx_products_active", "is_active"),
        Index("idx_products_stock", "current_stock"),
        {"schema": "inventory"}
    )


class StockMovement(Base):
    """Stock movement tracking for products"""
    __tablename__ = "stock_movements"
    __table_args__ = {"schema": "inventory"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("inventory.products.id", ondelete="CASCADE"), nullable=False)
    movement_type = Column(Enum(MovementType), nullable=False)
    quantity = Column(Integer, nullable=False)
    reference_type = Column(String(50), nullable=True)  # 'invoice', 'manual', 'initial'
    reference_id = Column(String(255), nullable=True)  # invoice_id or other reference
    notes = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant", backref="stock_movements")
    product = relationship("Product", back_populates="stock_movements")
    created_by_user = relationship("User", backref="stock_movements")

    __table_args__ = (
        Index("idx_stock_movements_tenant", "tenant_id"),
        Index("idx_stock_movements_product", "product_id"),
        Index("idx_stock_movements_type", "movement_type"),
        Index("idx_stock_movements_reference", "reference_type", "reference_id"),
        Index("idx_stock_movements_created", "created_at"),
        {"schema": "inventory"}
    )


# =============================================
# Ads Alert Schema Models
# =============================================

class AdsAlertChat(Base):
    """Registered chat/customer for promotional broadcasts"""
    __tablename__ = "chat"
    __table_args__ = {"schema": "ads_alert"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    # Link to invoice.customer for customer-based targeting
    customer_id = Column(UUID(as_uuid=True), ForeignKey("invoice.customer.id", ondelete="CASCADE"), nullable=True)
    platform = Column(String(50), nullable=False, default="telegram")
    chat_id = Column(String(100), nullable=False)
    chat_name = Column(String(255), nullable=True)
    customer_name = Column(String(255), nullable=True)
    tags = Column(ARRAY(String(100)), nullable=True, default=[])
    subscribed = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc),
                       onupdate=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)

    # Relationships
    tenant = relationship("Tenant", backref="ads_alert_chats")


class AdsAlertPromotion(Base):
    """Promotional content for broadcasting"""
    __tablename__ = "promotion"
    __table_args__ = {"schema": "ads_alert"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    status = Column(Enum(PromotionStatus), nullable=False, default=PromotionStatus.draft)
    media_urls = Column(JSON, nullable=True, default=[])
    media_type = Column(Enum(PromotionMediaType), nullable=True, default=PromotionMediaType.text)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    target_type = Column(Enum(PromotionTargetType), nullable=True, default=PromotionTargetType.all)
    target_chat_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True, default=[])
    # Customer-based targeting (alternative to chat targeting)
    target_customer_type = Column(Enum(PromotionCustomerTargetType), nullable=False, default=PromotionCustomerTargetType.none)
    target_customer_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True, default=[])
    sent_at = Column(DateTime(timezone=True), nullable=True)
    meta = Column(JSON, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc),
                       onupdate=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)

    # Relationships
    tenant = relationship("Tenant", backref="ads_alert_promotions")
    creator = relationship("User", backref="created_promotions")


class AdsAlertPromoStatus(Base):
    """Global promotion status tracking per tenant"""
    __tablename__ = "promo_status"
    __table_args__ = {"schema": "ads_alert"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    active = Column(Boolean, nullable=False, default=False)
    last_sent = Column(DateTime(timezone=True), nullable=True)
    next_scheduled = Column(DateTime(timezone=True), nullable=True)
    meta = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc),
                       onupdate=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)

    # Relationships
    tenant = relationship("Tenant", backref="ads_alert_promo_status")


class AdsAlertMediaFolder(Base):
    """Folder structure for organizing media files"""
    __tablename__ = "media_folder"
    __table_args__ = (
        UniqueConstraint("tenant_id", "parent_id", "name", name="uq_media_folder_tenant_parent_name"),
        {"schema": "ads_alert"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("ads_alert.media_folder.id", ondelete="CASCADE"), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)

    # Relationships
    tenant = relationship("Tenant", backref="ads_alert_media_folders")
    creator = relationship("User", backref="created_media_folders")
    parent = relationship("AdsAlertMediaFolder", remote_side=[id], backref="children")


class AdsAlertMedia(Base):
    """Media files for promotional content"""
    __tablename__ = "media"
    __table_args__ = {"schema": "ads_alert"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    folder_id = Column(UUID(as_uuid=True), ForeignKey("ads_alert.media_folder.id", ondelete="SET NULL"), nullable=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)
    storage_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # MIME type
    file_size = Column(Integer, nullable=True)
    thumbnail_path = Column(String(500), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=True)  # For videos, in seconds
    meta = Column(JSON, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)

    # Relationships
    tenant = relationship("Tenant", backref="ads_alert_media")
    folder = relationship("AdsAlertMediaFolder", backref="media_files")
    creator = relationship("User", backref="uploaded_media")


class AdsAlertBroadcastLog(Base):
    """Log of broadcast attempts to individual chats"""
    __tablename__ = "broadcast_log"
    __table_args__ = {"schema": "ads_alert"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    promotion_id = Column(UUID(as_uuid=True), ForeignKey("ads_alert.promotion.id", ondelete="CASCADE"), nullable=False)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("ads_alert.chat.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(BroadcastStatus), nullable=False, default=BroadcastStatus.pending)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc), nullable=False)

    # Relationships
    tenant = relationship("Tenant", backref="ads_alert_broadcast_logs")
    promotion = relationship("AdsAlertPromotion", backref="broadcast_logs")
    chat = relationship("AdsAlertChat", backref="broadcast_logs")

