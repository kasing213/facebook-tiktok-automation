"""
Pydantic schemas for content moderation system.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID

from app.core.models import ModerationStatus


class ViolationDetail(BaseModel):
    """Details of a specific content violation."""
    pattern: str = Field(description="The pattern that was matched")
    category: str = Field(description="Violation category (illegal_drugs, weapons, etc.)")
    severity: int = Field(ge=1, le=10, description="Severity score 1-10")
    description: str = Field(description="Human-readable description of the violation")
    matches: List[str] = Field(description="Text matches found (limited to first 5)")
    match_count: int = Field(description="Total number of matches")
    source: str = Field(description="Source of the text (text_content, image:file_0, etc.)")


class ModerationRequest(BaseModel):
    """Request for content moderation."""
    promotion_id: UUID = Field(description="ID of the promotion to moderate")
    force_recheck: bool = Field(default=False, description="Force re-moderation even if already checked")


class ModerationResult(BaseModel):
    """Result of content moderation analysis."""
    moderation_status: str = Field(description="Moderation status: pending, approved, rejected, flagged")
    moderation_score: float = Field(ge=0, le=100, description="Confidence score 0-100")
    violations: List[ViolationDetail] = Field(description="List of detected violations")
    extracted_texts: List[str] = Field(description="Text content analyzed (from content and OCR)")
    confidence_scores: List[float] = Field(description="OCR confidence scores for each image")
    recommendation: str = Field(description="Human-readable recommendation")
    requires_manual_review: bool = Field(description="Whether manual admin review is required")
    can_be_sent: bool = Field(description="Whether the content can be sent")
    timestamp: str = Field(description="When the analysis was performed")
    total_patterns_checked: int = Field(description="Number of violation patterns checked")
    analysis_details: Dict[str, int] = Field(description="Breakdown of analysis statistics")


class ModerationDecision(BaseModel):
    """Admin decision on flagged content."""
    action: str = Field(pattern="^(approve|reject)$", description="Action to take: approve or reject")
    reason: Optional[str] = Field(description="Reason for the decision")
    bypass_moderation: bool = Field(default=False, description="Skip future moderation for this promotion")


class ModerationHistoryItem(BaseModel):
    """Historical moderation record."""
    id: UUID
    promotion_id: UUID
    moderation_status: str
    moderation_score: Optional[float]
    moderated_at: datetime
    moderated_by: Optional[UUID]
    moderator_name: Optional[str]
    rejection_reason: Optional[str]
    violations_count: int
    analysis_summary: str


class ModerationQueueItem(BaseModel):
    """Item in the moderation queue for admin review."""
    promotion_id: UUID
    title: str
    content: Optional[str]
    media_type: str
    media_urls: List[str]
    moderation_status: str
    moderation_score: Optional[float]
    violations: List[ViolationDetail]
    created_at: datetime
    created_by: Optional[UUID]
    creator_name: Optional[str]
    tenant_id: UUID


class ModerationQueueResponse(BaseModel):
    """Response for moderation queue listing."""
    items: List[ModerationQueueItem]
    total: int = Field(description="Total number of items in queue")
    pending_count: int = Field(description="Number of items pending review")
    flagged_count: int = Field(description="Number of items flagged for manual review")


class ModerationStats(BaseModel):
    """Statistics for moderation system."""
    total_checked: int = Field(description="Total promotions checked")
    approved: int = Field(description="Number approved automatically")
    rejected: int = Field(description="Number rejected automatically")
    flagged: int = Field(description="Number flagged for manual review")
    pending: int = Field(description="Number pending review")
    manual_approvals: int = Field(description="Number manually approved by admin")
    manual_rejections: int = Field(description="Number manually rejected by admin")

    # Violation category breakdown
    violation_categories: Dict[str, int] = Field(description="Count of violations by category")

    # Performance metrics
    avg_processing_time: float = Field(description="Average time to process content (seconds)")
    accuracy_rate: Optional[float] = Field(description="Accuracy rate if manual feedback available")


class ModerationConfigUpdate(BaseModel):
    """Update moderation configuration."""
    enable_auto_approval: bool = Field(default=True, description="Enable automatic approval for low-risk content")
    enable_auto_rejection: bool = Field(default=True, description="Enable automatic rejection for high-risk content")
    sensitivity_threshold: float = Field(ge=0, le=10, default=6.0, description="Sensitivity threshold for flagging")
    require_ocr: bool = Field(default=True, description="Always perform OCR on images")
    whitelist_patterns: List[str] = Field(default=[], description="Patterns to always allow")
    custom_violation_patterns: List[Dict[str, Any]] = Field(default=[], description="Custom violation patterns to add")


class ModerationConfig(BaseModel):
    """Current moderation configuration."""
    enable_auto_approval: bool
    enable_auto_rejection: bool
    sensitivity_threshold: float
    require_ocr: bool
    whitelist_patterns: List[str]
    total_patterns: int = Field(description="Total number of violation patterns loaded")
    violation_categories: Dict[str, int] = Field(description="Number of patterns per category")
    last_updated: datetime
    updated_by: Optional[UUID]