"""OCR Verification Audit Trail Service."""

import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.models import User

logger = logging.getLogger(__name__)


class OCRAuditService:
    """Service for logging OCR verification audit trail."""

    # Patterns for sensitive data that should be redacted
    ACCOUNT_NUMBER_PATTERN = re.compile(r'\b\d{8,20}\b')  # Account numbers (8-20 digits)
    PHONE_NUMBER_PATTERN = re.compile(r'\b\d{3}-?\d{3}-?\d{4}\b|\b\+\d{1,3}\s?\d{8,15}\b')  # Phone numbers
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')  # Email addresses
    TRANSACTION_ID_PATTERN = re.compile(r'\b[A-Z0-9]{10,30}\b')  # Transaction IDs

    @staticmethod
    def _sanitize_ocr_response(ocr_response: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Sanitize OCR response to remove sensitive information while preserving useful data.

        This function removes:
        - Account numbers
        - Phone numbers
        - Email addresses
        - Transaction reference numbers
        - Raw extracted text that may contain sensitive data

        But preserves:
        - Verification status and confidence
        - Currency and amount (needed for audit)
        - Bank name (not sensitive)
        - Metadata about OCR processing
        """
        if not ocr_response:
            return None

        try:
            # Create a sanitized copy
            sanitized = ocr_response.copy()

            # Remove or redact sensitive fields
            sensitive_fields = [
                'raw_text',           # Raw OCR text may contain account numbers
                'extracted_account',  # Account number
                'account_number',     # Account number
                'recipient_account',  # Recipient account
                'phone_number',       # Phone number
                'email',              # Email address
                'transaction_id',     # Transaction reference
                'reference_number'    # Transaction reference
            ]

            for field in sensitive_fields:
                if field in sanitized:
                    sanitized[field] = "[REDACTED]"

            # Sanitize extracted_data sub-object if it exists
            if 'extracted_data' in sanitized and isinstance(sanitized['extracted_data'], dict):
                extracted = sanitized['extracted_data']
                for field in ['account', 'phone', 'email', 'reference']:
                    if field in extracted:
                        extracted[field] = "[REDACTED]"

                # Redact account numbers in amount strings but preserve the amount
                if 'amount' in extracted and isinstance(extracted['amount'], str):
                    # Replace account-like numbers but keep amount values
                    amount_str = extracted['amount']
                    # Only redact if it looks like an account (not a currency amount)
                    if not re.match(r'^\$?\d{1,10}(\.\d{2})?$', amount_str.replace(',', '')):
                        amount_str = OCRAuditService.ACCOUNT_NUMBER_PATTERN.sub("[REDACTED]", amount_str)
                    extracted['amount'] = amount_str

            # Redact sensitive data from any text fields
            for key, value in sanitized.items():
                if isinstance(value, str):
                    # Redact account numbers, phones, emails
                    value = OCRAuditService.ACCOUNT_NUMBER_PATTERN.sub("[REDACTED]", value)
                    value = OCRAuditService.PHONE_NUMBER_PATTERN.sub("[REDACTED]", value)
                    value = OCRAuditService.EMAIL_PATTERN.sub("[REDACTED]", value)
                    sanitized[key] = value

            # Keep safe metadata fields
            safe_fields = [
                'success',
                'confidence',
                'verification_status',
                'currency',
                'bank',
                'timestamp',
                'record_id',
                'mock_mode'
            ]

            # Log what we're keeping for audit purposes
            logger.debug(f"OCR response sanitized. Safe fields preserved: {[k for k in safe_fields if k in sanitized]}")

            return sanitized

        except Exception as e:
            logger.error(f"Error sanitizing OCR response: {e}")
            # If sanitization fails, return minimal safe data
            return {
                "sanitization_error": str(e),
                "confidence": ocr_response.get("confidence", 0),
                "success": ocr_response.get("success", False),
                "verification_status": ocr_response.get("verification_status", "unknown")
            }

    @staticmethod
    def log_verification_action(
        db: Session,
        tenant_id: UUID,
        action: str,
        new_status: str,
        verified_by: Optional[User] = None,
        invoice_id: Optional[UUID] = None,
        screenshot_id: Optional[UUID] = None,
        previous_status: Optional[str] = None,
        confidence_score: Optional[float] = None,
        verification_method: Optional[str] = None,
        ocr_response: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UUID:
        """
        Log an OCR verification action to the audit trail.

        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            action: Action type ('auto_verified', 'manual_approved', 'manual_rejected', 'manual_pending')
            new_status: New verification status
            verified_by: User who performed the action (None for auto actions)
            invoice_id: Related invoice ID
            screenshot_id: Related screenshot ID
            previous_status: Previous verification status
            confidence_score: OCR confidence score (0-100)
            verification_method: Method used ('ocr_auto', 'manual_web', 'manual_telegram')
            ocr_response: Full OCR response JSON
            notes: Additional notes or reason
            ip_address: User's IP address
            user_agent: User's browser/client

        Returns:
            UUID of the created audit log entry
        """
        try:
            # Prepare values
            verified_by_id = verified_by.id if verified_by else None
            verified_by_name = verified_by.email if verified_by else "system"

            # Convert confidence score to decimal (0-1 range for database)
            if confidence_score is not None:
                confidence_decimal = confidence_score / 100.0
            else:
                confidence_decimal = None

            # Sanitize OCR response to remove sensitive data
            sanitized_ocr_response = OCRAuditService._sanitize_ocr_response(ocr_response)

            # Execute insert query
            result = db.execute(
                text("""
                    INSERT INTO audit_sales.ocr_verification_log (
                        tenant_id, invoice_id, screenshot_id, action,
                        previous_status, new_status, confidence_score,
                        verified_by, verified_by_name, verification_method,
                        ocr_response, notes, ip_address, user_agent
                    )
                    VALUES (
                        :tenant_id, :invoice_id, :screenshot_id, :action,
                        :previous_status, :new_status, :confidence_score,
                        :verified_by, :verified_by_name, :verification_method,
                        :ocr_response, :notes, :ip_address, :user_agent
                    )
                    RETURNING id
                """),
                {
                    "tenant_id": str(tenant_id),
                    "invoice_id": str(invoice_id) if invoice_id else None,
                    "screenshot_id": str(screenshot_id) if screenshot_id else None,
                    "action": action,
                    "previous_status": previous_status,
                    "new_status": new_status,
                    "confidence_score": confidence_decimal,
                    "verified_by": str(verified_by_id) if verified_by_id else None,
                    "verified_by_name": verified_by_name,
                    "verification_method": verification_method,
                    "ocr_response": sanitized_ocr_response,
                    "notes": notes,
                    "ip_address": ip_address,
                    "user_agent": user_agent
                }
            )

            db.commit()

            log_id = result.fetchone()[0]

            logger.info(
                f"OCR audit logged: {action} for invoice {invoice_id} by {verified_by_name} "
                f"(confidence: {confidence_score}%, status: {previous_status} -> {new_status}) "
                f"[sensitive data sanitized]"
            )

            return UUID(log_id)

        except Exception as e:
            logger.error(f"Failed to log OCR audit: {e}")
            db.rollback()
            raise

    @staticmethod
    def log_auto_verification(
        db: Session,
        tenant_id: UUID,
        invoice_id: UUID,
        confidence_score: float,
        ocr_response: Dict[str, Any],
        approved: bool,
        previous_status: str = "pending",
        screenshot_id: Optional[UUID] = None
    ) -> UUID:
        """Log automatic OCR verification with screenshot reference."""
        return OCRAuditService.log_verification_action(
            db=db,
            tenant_id=tenant_id,
            action="auto_verified",
            new_status="verified" if approved else "pending",
            invoice_id=invoice_id,
            screenshot_id=screenshot_id,
            previous_status=previous_status,
            confidence_score=confidence_score,
            verification_method="ocr_auto",
            ocr_response=ocr_response,
            notes=f"Auto-{'approved' if approved else 'pending'} (confidence: {confidence_score:.1f}%)" +
                  (f" [Screenshot: {screenshot_id}]" if screenshot_id else "")
        )

    @staticmethod
    def log_manual_action(
        db: Session,
        tenant_id: UUID,
        invoice_id: UUID,
        action: str,  # 'manual_approved', 'manual_rejected', 'manual_pending'
        verified_by: User,
        notes: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        verification_method: str = "manual_web",
        previous_status: str = "pending",
        screenshot_id: Optional[UUID] = None
    ) -> UUID:
        """Log manual verification action with screenshot reference."""
        status_map = {
            "manual_approved": "verified",
            "manual_rejected": "rejected",
            "manual_pending": "pending"
        }

        new_status = status_map.get(action, "pending")

        return OCRAuditService.log_verification_action(
            db=db,
            tenant_id=tenant_id,
            action=action,
            new_status=new_status,
            verified_by=verified_by,
            invoice_id=invoice_id,
            screenshot_id=screenshot_id,
            previous_status=previous_status,
            verification_method=verification_method,
            notes=notes,
            ip_address=ip_address,
            user_agent=user_agent
        )

    @staticmethod
    def get_invoice_audit_trail(
        db: Session,
        invoice_id: UUID,
        tenant_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get audit trail for a specific invoice with screenshot references."""
        try:
            result = db.execute(
                text("""
                    SELECT
                        ol.id, ol.action, ol.previous_status, ol.new_status,
                        ol.confidence_score, ol.verified_by_name, ol.verification_method,
                        ol.notes, ol.created_at, ol.ocr_response, ol.screenshot_id,
                        s.file_url as screenshot_url, s.meta->'filename' as screenshot_filename
                    FROM audit_sales.ocr_verification_log ol
                    LEFT JOIN scriptclient.screenshot s ON ol.screenshot_id::uuid = s.id
                    WHERE ol.invoice_id = :invoice_id AND ol.tenant_id = :tenant_id
                    ORDER BY ol.created_at DESC
                """),
                {
                    "invoice_id": str(invoice_id),
                    "tenant_id": str(tenant_id)
                }
            )

            rows = result.fetchall()

            audit_entries = []
            for row in rows:
                entry = {
                    "id": str(row.id),
                    "action": row.action,
                    "previous_status": row.previous_status,
                    "new_status": row.new_status,
                    "confidence_score": float(row.confidence_score * 100) if row.confidence_score else None,
                    "verified_by_name": row.verified_by_name,
                    "verification_method": row.verification_method,
                    "notes": row.notes,
                    "created_at": row.created_at.isoformat(),
                    "ocr_response": row.ocr_response,
                    "screenshot_id": str(row.screenshot_id) if row.screenshot_id else None,
                    "screenshot_url": row.screenshot_url,
                    "screenshot_filename": row.screenshot_filename
                }
                audit_entries.append(entry)

            return audit_entries

        except Exception as e:
            logger.error(f"Failed to get audit trail for invoice {invoice_id}: {e}")
            return []

    @staticmethod
    def get_verification_stats(
        db: Session,
        tenant_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get verification statistics for the tenant."""
        try:
            result = db.execute(
                text("""
                    SELECT
                        action,
                        verification_method,
                        COUNT(*) as count,
                        AVG(confidence_score) as avg_confidence
                    FROM audit_sales.ocr_verification_log
                    WHERE tenant_id = :tenant_id
                    AND created_at >= NOW() - INTERVAL ':days days'
                    GROUP BY action, verification_method
                    ORDER BY count DESC
                """),
                {
                    "tenant_id": str(tenant_id),
                    "days": days
                }
            )

            stats = {
                "total_verifications": 0,
                "auto_verified": 0,
                "manual_actions": 0,
                "avg_confidence": 0.0,
                "actions_breakdown": []
            }

            total = 0
            confidence_sum = 0
            confidence_count = 0

            for row in result:
                count = row.count
                total += count

                if row.avg_confidence:
                    confidence_sum += row.avg_confidence * count
                    confidence_count += count

                if row.action == "auto_verified":
                    stats["auto_verified"] += count
                else:
                    stats["manual_actions"] += count

                stats["actions_breakdown"].append({
                    "action": row.action,
                    "method": row.verification_method,
                    "count": count,
                    "avg_confidence": float(row.avg_confidence * 100) if row.avg_confidence else None
                })

            stats["total_verifications"] = total
            stats["avg_confidence"] = (confidence_sum / confidence_count * 100) if confidence_count > 0 else 0

            return stats

        except Exception as e:
            logger.error(f"Failed to get verification stats for tenant {tenant_id}: {e}")
            return {"error": str(e)}

    @staticmethod
    def log_screenshot_action(
        db: Session,
        tenant_id: UUID,
        screenshot_id: UUID,
        action: str,  # 'screenshot_uploaded', 'screenshot_viewed', 'screenshot_processed'
        invoice_id: Optional[UUID] = None,
        verified_by: Optional[User] = None,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """
        Log screenshot-related actions for audit trail.

        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            screenshot_id: Screenshot ID being acted upon
            action: Action type ('screenshot_uploaded', 'screenshot_viewed', 'screenshot_processed')
            invoice_id: Related invoice ID
            verified_by: User who performed the action
            notes: Additional notes
            metadata: Additional metadata (e.g., OCR results, view context)

        Returns:
            UUID of the created audit log entry
        """
        return OCRAuditService.log_verification_action(
            db=db,
            tenant_id=tenant_id,
            action=action,
            new_status="screenshot_action",
            verified_by=verified_by,
            invoice_id=invoice_id,
            screenshot_id=screenshot_id,
            verification_method="screenshot_system",
            notes=notes,
            ocr_response=metadata
        )

    @staticmethod
    def log_telegram_verification(
        db: Session,
        tenant_id: UUID,
        invoice_id: UUID,
        screenshot_id: UUID,
        action: str,  # 'telegram_approved', 'telegram_rejected'
        verified_by: User,
        telegram_username: Optional[str] = None,
        telegram_chat_id: Optional[int] = None
    ) -> UUID:
        """
        Log Telegram-based manual verification actions.

        Args:
            db: Database session
            tenant_id: Tenant ID
            invoice_id: Invoice being verified
            screenshot_id: Screenshot being verified
            action: Verification action
            verified_by: User who performed the action
            telegram_username: Telegram username
            telegram_chat_id: Telegram chat ID

        Returns:
            UUID of the created audit log entry
        """
        notes = f"Manual verification via Telegram"
        if telegram_username:
            notes += f" by @{telegram_username}"
        if telegram_chat_id:
            notes += f" (Chat: {telegram_chat_id})"

        return OCRAuditService.log_verification_action(
            db=db,
            tenant_id=tenant_id,
            action=action,
            new_status="verified" if "approved" in action else "rejected",
            verified_by=verified_by,
            invoice_id=invoice_id,
            screenshot_id=screenshot_id,
            verification_method="manual_telegram",
            notes=notes
        )