"""
Content Moderation API routes for Ads Alert system.
Provides endpoints for content scanning, admin review queue, and moderation decisions.
"""

import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.core.db import get_db
from app.core.models import User, AdsAlertPromotion, ModerationStatus, PromotionStatus
from app.core.authorization import get_current_owner, get_current_member_or_owner
from app.schemas.moderation import (
    ModerationRequest, ModerationResult, ModerationDecision,
    ModerationQueueResponse, ModerationQueueItem, ModerationStats,
    ModerationConfigUpdate, ModerationConfig, ModerationHistoryItem
)
from app.services.content_moderation_service import content_moderation_service
from app.repositories.ads_alert import AdsAlertPromotionRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/moderation", tags=["moderation"])


@router.post("/scan/{promotion_id}", response_model=ModerationResult)
async def scan_promotion_content(
    promotion_id: UUID,
    request: ModerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_member_or_owner)
):
    """
    Scan a specific promotion for content violations.
    Can be called manually or automatically during promotion creation.
    """
    promotion_repo = AdsAlertPromotionRepository(db)

    # Get promotion and verify ownership
    promotion = promotion_repo.get_by_id_and_tenant(promotion_id, current_user.tenant_id)
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found")

    # Check if already moderated and force_recheck is False
    if (promotion.moderation_status != ModerationStatus.pending and
        not request.force_recheck):
        # Return existing moderation result
        return ModerationResult(
            moderation_status=promotion.moderation_status.value,
            moderation_score=promotion.moderation_score or 0,
            violations=promotion.moderation_result.get("violations", []) if promotion.moderation_result else [],
            extracted_texts=promotion.moderation_result.get("extracted_texts", []) if promotion.moderation_result else [],
            confidence_scores=promotion.moderation_result.get("confidence_scores", []) if promotion.moderation_result else [],
            recommendation=promotion.rejection_reason or "Previously moderated",
            requires_manual_review=promotion.moderation_status == ModerationStatus.flagged,
            can_be_sent=promotion.moderation_status in [ModerationStatus.approved, ModerationStatus.skipped],
            timestamp=promotion.moderated_at.isoformat() if promotion.moderated_at else datetime.now(timezone.utc).isoformat(),
            total_patterns_checked=0,
            analysis_details=promotion.moderation_result.get("analysis_details", {}) if promotion.moderation_result else {}
        )

    try:
        # Perform content moderation
        moderation_result = await content_moderation_service.moderate_content(
            text_content=promotion.content,
            image_urls=promotion.media_urls if promotion.media_urls else None,
            media_files=None  # Media files would need to be downloaded from URLs
        )

        # Update promotion with moderation results
        now = datetime.now(timezone.utc)
        update_data = {
            "moderation_status": ModerationStatus[moderation_result["moderation_status"]],
            "moderation_result": moderation_result,
            "moderation_score": moderation_result["moderation_score"],
            "moderated_at": now,
            "rejection_reason": moderation_result["recommendation"]
        }

        promotion_repo.update_by_tenant(promotion_id, current_user.tenant_id, **update_data)
        db.commit()

        # Convert to response format
        return ModerationResult(**moderation_result)

    except Exception as e:
        logger.error(f"Error scanning promotion {promotion_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scan content: {str(e)}"
        )


@router.get("/queue", response_model=ModerationQueueResponse)
async def get_moderation_queue(
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_owner)  # Admin only
):
    """
    Get list of promotions requiring manual moderation review.
    Admin only endpoint.
    """
    try:
        # Build filter conditions
        conditions = [AdsAlertPromotion.tenant_id == current_user.tenant_id]

        if status_filter:
            if status_filter in ["pending", "flagged", "rejected"]:
                conditions.append(AdsAlertPromotion.moderation_status == ModerationStatus[status_filter])
        else:
            # Default: show items that need review
            conditions.append(
                AdsAlertPromotion.moderation_status.in_([
                    ModerationStatus.pending,
                    ModerationStatus.flagged
                ])
            )

        # Query promotions
        query = db.query(AdsAlertPromotion).filter(and_(*conditions))
        total = query.count()

        promotions = query.order_by(desc(AdsAlertPromotion.created_at)).offset(offset).limit(limit).all()

        # Build response items
        queue_items = []
        for promo in promotions:
            violations = []
            if promo.moderation_result and "violations" in promo.moderation_result:
                violations = promo.moderation_result["violations"]

            creator_name = promo.creator.email if promo.creator else "Unknown"

            queue_items.append(ModerationQueueItem(
                promotion_id=promo.id,
                title=promo.title,
                content=promo.content,
                media_type=promo.media_type.value if promo.media_type else "text",
                media_urls=promo.media_urls or [],
                moderation_status=promo.moderation_status.value,
                moderation_score=promo.moderation_score,
                violations=violations,
                created_at=promo.created_at,
                created_by=promo.created_by,
                creator_name=creator_name,
                tenant_id=promo.tenant_id
            ))

        # Get counts for different statuses
        pending_count = db.query(AdsAlertPromotion).filter(
            AdsAlertPromotion.tenant_id == current_user.tenant_id,
            AdsAlertPromotion.moderation_status == ModerationStatus.pending
        ).count()

        flagged_count = db.query(AdsAlertPromotion).filter(
            AdsAlertPromotion.tenant_id == current_user.tenant_id,
            AdsAlertPromotion.moderation_status == ModerationStatus.flagged
        ).count()

        return ModerationQueueResponse(
            items=queue_items,
            total=total,
            pending_count=pending_count,
            flagged_count=flagged_count
        )

    except Exception as e:
        logger.error(f"Error getting moderation queue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve moderation queue"
        )


@router.post("/decide/{promotion_id}")
async def make_moderation_decision(
    promotion_id: UUID,
    decision: ModerationDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_owner)  # Admin only
):
    """
    Make an admin decision on flagged content.
    Admin only endpoint for manual approval/rejection.
    """
    promotion_repo = AdsAlertPromotionRepository(db)

    # Get promotion and verify ownership
    promotion = promotion_repo.get_by_id_and_tenant(promotion_id, current_user.tenant_id)
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found")

    # Verify promotion is in a state that can be decided
    if promotion.moderation_status not in [ModerationStatus.pending, ModerationStatus.flagged]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot make decision on promotion with status: {promotion.moderation_status.value}"
        )

    try:
        # Apply decision
        now = datetime.now(timezone.utc)
        new_status = ModerationStatus.approved if decision.action == "approve" else ModerationStatus.rejected

        if decision.bypass_moderation:
            new_status = ModerationStatus.skipped

        update_data = {
            "moderation_status": new_status,
            "moderated_at": now,
            "moderated_by": current_user.id,
            "rejection_reason": decision.reason or f"Manually {decision.action}d by admin"
        }

        # Update moderation result with admin decision
        if promotion.moderation_result:
            promotion.moderation_result["admin_decision"] = {
                "action": decision.action,
                "reason": decision.reason,
                "decided_at": now.isoformat(),
                "decided_by": str(current_user.id),
                "bypass_moderation": decision.bypass_moderation
            }
            update_data["moderation_result"] = promotion.moderation_result

        promotion_repo.update_by_tenant(promotion_id, current_user.tenant_id, **update_data)
        db.commit()

        return {
            "success": True,
            "promotion_id": str(promotion_id),
            "decision": decision.action,
            "new_status": new_status.value,
            "message": f"Promotion {decision.action}d successfully"
        }

    except Exception as e:
        logger.error(f"Error making moderation decision for {promotion_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply moderation decision: {str(e)}"
        )


@router.get("/stats", response_model=ModerationStats)
async def get_moderation_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_owner)  # Admin only
):
    """
    Get moderation statistics for the tenant.
    Admin only endpoint.
    """
    try:
        # Count promotions by moderation status
        base_query = db.query(AdsAlertPromotion).filter(
            AdsAlertPromotion.tenant_id == current_user.tenant_id
        )

        total_checked = base_query.filter(
            AdsAlertPromotion.moderation_status != ModerationStatus.pending
        ).count()

        approved = base_query.filter(
            AdsAlertPromotion.moderation_status == ModerationStatus.approved
        ).count()

        rejected = base_query.filter(
            AdsAlertPromotion.moderation_status == ModerationStatus.rejected
        ).count()

        flagged = base_query.filter(
            AdsAlertPromotion.moderation_status == ModerationStatus.flagged
        ).count()

        pending = base_query.filter(
            AdsAlertPromotion.moderation_status == ModerationStatus.pending
        ).count()

        # Count manual decisions
        manual_approvals = base_query.filter(
            and_(
                AdsAlertPromotion.moderation_status == ModerationStatus.approved,
                AdsAlertPromotion.moderated_by.is_not(None)
            )
        ).count()

        manual_rejections = base_query.filter(
            and_(
                AdsAlertPromotion.moderation_status == ModerationStatus.rejected,
                AdsAlertPromotion.moderated_by.is_not(None)
            )
        ).count()

        # Get violation categories from moderation service
        violation_categories = content_moderation_service.get_violation_categories()

        return ModerationStats(
            total_checked=total_checked,
            approved=approved,
            rejected=rejected,
            flagged=flagged,
            pending=pending,
            manual_approvals=manual_approvals,
            manual_rejections=manual_rejections,
            violation_categories=violation_categories,
            avg_processing_time=1.5,  # Placeholder - would need to track actual times
            accuracy_rate=None  # Would need manual feedback to calculate
        )

    except Exception as e:
        logger.error(f"Error getting moderation stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve moderation statistics"
        )


@router.get("/history", response_model=List[ModerationHistoryItem])
async def get_moderation_history(
    promotion_id: Optional[UUID] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_owner)  # Admin only
):
    """
    Get moderation history for promotions.
    Admin only endpoint.
    """
    try:
        query = db.query(AdsAlertPromotion).filter(
            AdsAlertPromotion.tenant_id == current_user.tenant_id,
            AdsAlertPromotion.moderated_at.is_not(None)
        )

        if promotion_id:
            query = query.filter(AdsAlertPromotion.id == promotion_id)

        promotions = query.order_by(desc(AdsAlertPromotion.moderated_at)).limit(limit).all()

        history_items = []
        for promo in promotions:
            violations_count = 0
            if promo.moderation_result and "violations" in promo.moderation_result:
                violations_count = len(promo.moderation_result["violations"])

            moderator_name = None
            if promo.moderator:
                moderator_name = promo.moderator.email

            analysis_summary = f"Score: {promo.moderation_score or 0:.1f}, Violations: {violations_count}"
            if promo.rejection_reason:
                analysis_summary += f", Reason: {promo.rejection_reason[:50]}..."

            history_items.append(ModerationHistoryItem(
                id=promo.id,
                promotion_id=promo.id,
                moderation_status=promo.moderation_status.value,
                moderation_score=promo.moderation_score,
                moderated_at=promo.moderated_at,
                moderated_by=promo.moderated_by,
                moderator_name=moderator_name,
                rejection_reason=promo.rejection_reason,
                violations_count=violations_count,
                analysis_summary=analysis_summary
            ))

        return history_items

    except Exception as e:
        logger.error(f"Error getting moderation history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve moderation history"
        )