"""Cloudflare integration data models."""

import uuid
import datetime as dt
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field as PydanticField, validator
from sqlalchemy import (
    Column, String, DateTime, Boolean, Integer, Text, JSON,
    ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.models import Base


# ---------------------------------------------------------------------------
# Pydantic config / request / response schemas
# ---------------------------------------------------------------------------

class CloudflareConfig(BaseModel):
    """Cloudflare configuration model."""

    domain: str
    api_token: Optional[str] = None
    email: Optional[str] = None
    api_key: Optional[str] = None
    zone_id: str
    test_mode: bool = True
    request_timeout: int = 30
    max_requests_per_minute: int = 60
    log_level: str = "INFO"
    audit_logging: bool = True
    sync_to_db: bool = True
    cache_ttl: int = 300
    auto_update_enabled: bool = False
    require_superuser: bool = True

    @validator('api_token', 'api_key')
    def validate_auth(cls, v, values):
        """Ensure either API token or email+key is provided."""
        if not v and not (values.get('email') and values.get('api_key')):
            if 'api_token' in values:
                raise ValueError('Either api_token or (email + api_key) must be provided')
        return v


class DNSRecordCreate(BaseModel):
    """DNS record creation model."""

    name: str
    type: str  # A, AAAA, CNAME, MX, TXT, etc.
    content: str
    ttl: int = 300
    proxied: bool = False
    priority: Optional[int] = None
    comment: Optional[str] = None


class DNSRecordUpdate(BaseModel):
    """DNS record update model."""

    name: Optional[str] = None
    type: Optional[str] = None
    content: Optional[str] = None
    ttl: Optional[int] = None
    proxied: Optional[bool] = None
    priority: Optional[int] = None
    comment: Optional[str] = None


class DNSRecordResponse(BaseModel):
    """DNS record API response model."""

    id: str
    zone_id: str
    zone_name: str
    name: str
    type: str
    content: str
    ttl: int
    proxied: bool
    priority: Optional[int] = None
    comment: Optional[str] = None
    created_on: Optional[dt.datetime] = None
    modified_on: Optional[dt.datetime] = None

    # Local metadata
    tenant_id: Optional[str] = None
    last_synced: Optional[dt.datetime] = None
    sync_status: str

    class Config:
        from_attributes = True


class BulkDNSOperation(BaseModel):
    """Bulk DNS operation model."""

    operation_type: str = PydanticField(..., description="Operation type: create, update, delete")
    records: List[Dict[str, Any]] = PydanticField(..., description="List of DNS records to process")
    options: Optional[Dict[str, Any]] = PydanticField(default=None, description="Additional operation options")


class CloudflareHealthStatus(BaseModel):
    """Cloudflare service health status."""

    status: str  # healthy, unhealthy, degraded
    zone_accessible: bool
    api_accessible: bool
    last_check: dt.datetime
    response_time_ms: Optional[float] = None
    errors: List[str] = []


# ---------------------------------------------------------------------------
# SQLAlchemy ORM models (using project's declarative Base)
# ---------------------------------------------------------------------------

class DNSRecord(Base):
    """DNS record database model."""

    __tablename__ = "cloudflare_dns_records"

    id = Column(String, primary_key=True)  # Cloudflare record ID
    zone_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False, index=True)  # A, AAAA, CNAME, MX, TXT, etc.
    content = Column(String, nullable=False)
    ttl = Column(Integer, default=300, nullable=False)
    proxied = Column(Boolean, default=False, nullable=False)
    priority = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)

    created_on = Column(DateTime, nullable=True)
    modified_on = Column(DateTime, nullable=True)

    # Local tracking
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow, nullable=False)
    last_synced = Column(DateTime, nullable=True)
    sync_status = Column(String, default="pending", nullable=False)  # pending, synced, error

    # Relationships
    operations = relationship("CloudflareOperation", back_populates="dns_record")


class CloudflareOperation(Base):
    """Cloudflare operation audit log."""

    __tablename__ = "cloudflare_operations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operation_type = Column(String, nullable=False, index=True)  # create, update, delete, sync
    resource_type = Column(String, nullable=False, index=True)  # dns_record, zone, etc.
    resource_id = Column(String, nullable=True, index=True)

    # Operation details
    operation_data = Column(JSON, nullable=True)
    result_data = Column(JSON, nullable=True)

    # Status tracking
    status = Column(String, nullable=False, index=True)  # pending, success, error
    error_message = Column(Text, nullable=True)

    # User and tenant context
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id"), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime, default=dt.datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    dns_record_id = Column(String, ForeignKey("cloudflare_dns_records.id"), nullable=True)
    dns_record = relationship("DNSRecord", back_populates="operations")
