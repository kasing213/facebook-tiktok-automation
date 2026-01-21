"""
Verification Coordinator Service

This service coordinates between OCR extraction and pattern learning
to make intelligent verification decisions. It works with both the
existing scriptclient system and the new learning model.

Key Features:
- Hybrid GPT-4o + Claude Haiku OCR routing
- Pattern-based confidence scoring
- Automatic verification queue management
- Learning from manual approvals/rejections
- Multi-tenant support with complete isolation
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
import json

from .pattern_learning_service import PatternLearningService, VerificationResult
from .bank_format_recognizer import BankFormatRecognizer, BankFormatResult

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Standardized OCR result from any OCR service"""
    success: bool
    confidence: float

    # Extracted fields
    amount: Optional[float] = None
    currency: Optional[str] = None
    recipient_name: Optional[str] = None
    account_number: Optional[str] = None
    transaction_id: Optional[str] = None
    bank_name: Optional[str] = None
    transaction_date: Optional[str] = None

    # Metadata
    ocr_model: Optional[str] = None  # 'gpt-4o', 'claude-haiku'
    processing_time: Optional[float] = None
    raw_response: Optional[dict] = None
    error_message: Optional[str] = None


@dataclass
class VerificationDecision:
    """Final verification decision with reasoning"""
    status: str  # 'auto_verified', 'queued_for_review', 'manual_review_required', 'rejected'
    confidence: float
    reason: str

    # OCR results
    ocr_result: OCRResult

    # Bank format recognition results
    bank_result: Optional[BankFormatResult] = None

    # Pattern learning results
    pattern_result: Optional[VerificationResult] = None

    # Queue information (if queued)
    queue_id: Optional[str] = None

    # Additional context
    tenant_id: Optional[str] = None
    customer_id: Optional[str] = None
    invoice_id: Optional[str] = None

    # For learning system
    should_learn_from_result: bool = True


class VerificationCoordinator:
    """Coordinates OCR and pattern learning for intelligent verification"""

    def __init__(self, db, ocr_services: dict = None):
        self.db = db
        self.learning_service = PatternLearningService(db)
        self.bank_recognizer = BankFormatRecognizer(db)

        # OCR service configuration
        self.ocr_services = ocr_services or {}

        # Verification thresholds
        self.AUTO_APPROVE_THRESHOLD = 0.8    # Auto-approve above 80%
        self.REVIEW_QUEUE_THRESHOLD = 0.5    # Queue for review above 50%
        self.MANUAL_REVIEW_THRESHOLD = 0.3   # Everything else needs full review

        # Cost optimization settings
        self.USE_HAIKU_FIRST = True          # Try cheaper model first
        self.HAIKU_CONFIDENCE_THRESHOLD = 0.7  # Switch to GPT-4o if below this

    async def verify_payment(
        self,
        screenshot_data: bytes,
        invoice: dict,
        tenant_id: str,
        customer_id: str,
        invoice_id: str,
        force_ocr_model: Optional[str] = None
    ) -> VerificationDecision:
        """
        Main verification pipeline

        Args:
            screenshot_data: Raw image data
            invoice: Invoice details including expected values
            tenant_id: Tenant identifier for multi-tenant isolation
            customer_id: Customer identifier
            invoice_id: Invoice identifier
            force_ocr_model: Force specific OCR model ('gpt-4o' or 'claude-haiku')

        Returns:
            VerificationDecision with final status and reasoning
        """

        try:
            # Step 1: Bank Format Recognition (Primary - Solves cold start problem)
            bank_result = await self.bank_recognizer.extract_payment_info(screenshot_data)

            # Step 2: Fallback OCR if bank format fails
            ocr_result = None
            if bank_result.success and bank_result.confidence >= 0.7:
                # Convert bank result to OCRResult format
                ocr_result = self._convert_bank_result_to_ocr(bank_result)
                logger.info(f"Using bank format extraction: {bank_result.bank_name} "
                           f"(confidence: {bank_result.confidence:.2f})")
            else:
                # Fallback to traditional OCR
                ocr_result = await self._extract_with_smart_routing(
                    screenshot_data,
                    force_model=force_ocr_model
                )
                logger.info(f"Bank format failed, using traditional OCR "
                           f"(confidence: {ocr_result.confidence:.2f})")

            if not ocr_result.success:
                return VerificationDecision(
                    status='manual_review_required',
                    confidence=0.0,
                    reason=f'extraction_failed: {ocr_result.error_message}',
                    ocr_result=ocr_result,
                    bank_result=bank_result,
                    tenant_id=tenant_id,
                    customer_id=customer_id,
                    invoice_id=invoice_id
                )

            # Step 3: Pattern-based verification
            pattern_result = await self.learning_service.verify_with_patterns(
                tenant_id=tenant_id,
                customer_id=customer_id,
                extracted_name=ocr_result.recipient_name or '',
                extracted_account=ocr_result.account_number or '',
                extracted_amount=ocr_result.amount
            )

            # Step 4: Amount verification
            amount_match_confidence = self._verify_amount(
                extracted_amount=ocr_result.amount,
                expected_amount=invoice.get('amount'),
                tolerance_percent=5.0
            )

            # Step 5: Calculate combined confidence
            combined_confidence = self._calculate_combined_confidence(
                bank_confidence=bank_result.confidence if bank_result.success else 0.0,
                ocr_confidence=ocr_result.confidence,
                pattern_confidence=pattern_result.confidence,
                amount_confidence=amount_match_confidence
            )

            # Step 6: Make verification decision
            decision = self._make_verification_decision(
                combined_confidence=combined_confidence,
                bank_result=bank_result,
                pattern_result=pattern_result,
                ocr_result=ocr_result,
                amount_match=amount_match_confidence > 0.8,
                tenant_id=tenant_id,
                customer_id=customer_id,
                invoice_id=invoice_id
            )

            # Step 6: Handle the decision
            await self._handle_verification_decision(decision, invoice, screenshot_data)

            return decision

        except Exception as e:
            logger.error(f"Verification coordinator error: {e}")

            return VerificationDecision(
                status='manual_review_required',
                confidence=0.0,
                reason=f'verification_error: {str(e)}',
                ocr_result=OCRResult(success=False, confidence=0.0, error_message=str(e)),
                tenant_id=tenant_id,
                customer_id=customer_id,
                invoice_id=invoice_id
            )

    async def _extract_with_smart_routing(
        self,
        screenshot_data: bytes,
        force_model: Optional[str] = None
    ) -> OCRResult:
        """Smart OCR routing: try Haiku first, fallback to GPT-4o if needed"""

        if force_model:
            return await self._extract_with_model(screenshot_data, force_model)

        if not self.USE_HAIKU_FIRST:
            return await self._extract_with_model(screenshot_data, 'gpt-4o')

        # Try Claude Haiku first (cheaper, faster)
        try:
            haiku_result = await self._extract_with_model(screenshot_data, 'claude-haiku')

            if (haiku_result.success and
                haiku_result.confidence >= self.HAIKU_CONFIDENCE_THRESHOLD):
                logger.info(f"Haiku extraction successful (confidence: {haiku_result.confidence:.2f})")
                return haiku_result

            # Haiku confidence too low, try GPT-4o
            logger.info(f"Haiku confidence low ({haiku_result.confidence:.2f}), trying GPT-4o")

        except Exception as e:
            logger.warning(f"Haiku extraction failed: {e}, trying GPT-4o")

        # Fallback to GPT-4o
        return await self._extract_with_model(screenshot_data, 'gpt-4o')

    async def _extract_with_model(self, screenshot_data: bytes, model: str) -> OCRResult:
        """Extract data using specific OCR model"""

        if model not in self.ocr_services:
            return OCRResult(
                success=False,
                confidence=0.0,
                error_message=f"OCR model '{model}' not available"
            )

        try:
            start_time = datetime.now()

            # Call the appropriate OCR service
            raw_result = await self.ocr_services[model].extract(screenshot_data)

            processing_time = (datetime.now() - start_time).total_seconds()

            # Standardize the result
            return self._standardize_ocr_result(raw_result, model, processing_time)

        except Exception as e:
            return OCRResult(
                success=False,
                confidence=0.0,
                ocr_model=model,
                error_message=str(e)
            )

    def _standardize_ocr_result(
        self,
        raw_result: dict,
        model: str,
        processing_time: float
    ) -> OCRResult:
        """Convert raw OCR result to standardized format"""

        # Handle different OCR service response formats
        if model == 'gpt-4o':
            return self._parse_gpt4o_result(raw_result, processing_time)
        elif model == 'claude-haiku':
            return self._parse_haiku_result(raw_result, processing_time)
        else:
            # Generic parser
            return OCRResult(
                success=raw_result.get('success', False),
                confidence=raw_result.get('confidence', 0.0),
                amount=raw_result.get('amount'),
                currency=raw_result.get('currency'),
                recipient_name=raw_result.get('recipientName') or raw_result.get('recipient_name'),
                account_number=raw_result.get('toAccount') or raw_result.get('account_number'),
                transaction_id=raw_result.get('transactionId') or raw_result.get('transaction_id'),
                bank_name=raw_result.get('bankName') or raw_result.get('bank_name'),
                ocr_model=model,
                processing_time=processing_time,
                raw_response=raw_result
            )

    def _parse_gpt4o_result(self, raw_result: dict, processing_time: float) -> OCRResult:
        """Parse GPT-4o specific result format"""

        extracted = raw_result.get('extracted_data', {})
        verification = raw_result.get('verification', {})

        # Convert confidence string to number
        confidence_str = raw_result.get('confidence', 'low')
        confidence_map = {'high': 0.9, 'medium': 0.7, 'low': 0.5}
        confidence = confidence_map.get(confidence_str, 0.5)

        return OCRResult(
            success=raw_result.get('success', True),
            confidence=confidence,
            amount=extracted.get('amount'),
            currency=extracted.get('currency'),
            recipient_name=extracted.get('recipientName'),
            account_number=extracted.get('toAccount'),
            transaction_id=extracted.get('transactionId'),
            bank_name=extracted.get('bankName'),
            transaction_date=extracted.get('transactionDate'),
            ocr_model='gpt-4o',
            processing_time=processing_time,
            raw_response=raw_result
        )

    def _parse_haiku_result(self, raw_result: dict, processing_time: float) -> OCRResult:
        """Parse Claude Haiku specific result format"""

        # Haiku typically returns simpler, more focused results
        return OCRResult(
            success=raw_result.get('success', True),
            confidence=raw_result.get('confidence', 0.7),
            amount=raw_result.get('amount'),
            currency=raw_result.get('currency', 'KHR'),
            recipient_name=raw_result.get('recipient_name'),
            account_number=raw_result.get('account_number'),
            transaction_id=raw_result.get('transaction_id'),
            bank_name=raw_result.get('bank_name'),
            ocr_model='claude-haiku',
            processing_time=processing_time,
            raw_response=raw_result
        )

    def _verify_amount(
        self,
        extracted_amount: Optional[float],
        expected_amount: Optional[float],
        tolerance_percent: float = 5.0
    ) -> float:
        """Verify amount match with tolerance"""

        if not extracted_amount or not expected_amount:
            return 0.0

        tolerance = expected_amount * (tolerance_percent / 100)
        diff = abs(extracted_amount - expected_amount)

        if diff <= tolerance:
            # Perfect match or within tolerance
            match_quality = max(0.8, 1.0 - (diff / tolerance) * 0.2)
            return match_quality
        else:
            # Outside tolerance
            return 0.0

    def _calculate_combined_confidence(
        self,
        bank_confidence: float,
        ocr_confidence: float,
        pattern_confidence: float,
        amount_confidence: float
    ) -> float:
        """Calculate combined confidence from multiple sources"""

        # Weighted combination - bank format gets highest weight for new users
        weights = {
            'bank': 0.4,       # Bank format recognition (solves cold start)
            'pattern': 0.3,    # Pattern matching (builds over time)
            'amount': 0.2,     # Amount verification is reliable
            'ocr': 0.1         # OCR baseline confidence (fallback)
        }

        combined = (
            bank_confidence * weights['bank'] +
            pattern_confidence * weights['pattern'] +
            amount_confidence * weights['amount'] +
            ocr_confidence * weights['ocr']
        )

        # Boost for multiple positive signals
        positive_signals = sum([
            bank_confidence > 0.8,
            pattern_confidence > 0.7,
            amount_confidence > 0.8,
            ocr_confidence > 0.7
        ])

        if positive_signals >= 2:
            combined = min(0.95, combined * 1.15)  # 15% boost for multiple confirmations

        return combined

    def _make_verification_decision(
        self,
        combined_confidence: float,
        bank_result: BankFormatResult,
        pattern_result: VerificationResult,
        ocr_result: OCRResult,
        amount_match: bool,
        tenant_id: str,
        customer_id: str,
        invoice_id: str
    ) -> VerificationDecision:
        """Make final verification decision based on all factors"""

        # Enhanced auto-approve criteria (bank format enables higher auto-approval for new users)
        bank_format_success = bank_result.success and bank_result.confidence >= 0.85
        has_pattern_approval = pattern_result.should_auto_approve

        # Auto-approve if bank format is highly confident OR pattern match + amount match
        if (combined_confidence >= self.AUTO_APPROVE_THRESHOLD and
            (bank_format_success or (has_pattern_approval and amount_match))):

            reason_parts = []
            if bank_format_success:
                reason_parts.append(f"bank_format_{bank_result.bank_name}_{bank_result.confidence:.2f}")
            if has_pattern_approval:
                reason_parts.append(f"pattern_{pattern_result.reason}")
            if amount_match:
                reason_parts.append("amount_match")

            return VerificationDecision(
                status='auto_verified',
                confidence=combined_confidence,
                reason=f'auto_approved: {", ".join(reason_parts)}',
                ocr_result=ocr_result,
                bank_result=bank_result,
                pattern_result=pattern_result,
                tenant_id=tenant_id,
                customer_id=customer_id,
                invoice_id=invoice_id
            )

        # Queue for quick review
        elif combined_confidence >= self.REVIEW_QUEUE_THRESHOLD:
            reason = f'review_needed: confidence_{combined_confidence:.2f}'
            if bank_result.success:
                reason += f', bank_{bank_result.bank_name}'
            if pattern_result.confidence > 0.5:
                reason += f', pattern_{pattern_result.confidence:.2f}'

            return VerificationDecision(
                status='queued_for_review',
                confidence=combined_confidence,
                reason=reason,
                ocr_result=ocr_result,
                bank_result=bank_result,
                pattern_result=pattern_result,
                tenant_id=tenant_id,
                customer_id=customer_id,
                invoice_id=invoice_id
            )

        # Manual review required
        else:
            reason = 'low_confidence'
            if not amount_match:
                reason += '_amount_mismatch'
            if combined_confidence < self.MANUAL_REVIEW_THRESHOLD:
                reason += '_very_low_confidence'

            return VerificationDecision(
                status='manual_review_required',
                confidence=combined_confidence,
                reason=reason,
                ocr_result=ocr_result,
                bank_result=bank_result,
                pattern_result=pattern_result,
                tenant_id=tenant_id,
                customer_id=customer_id,
                invoice_id=invoice_id
            )

    async def _handle_verification_decision(
        self,
        decision: VerificationDecision,
        invoice: dict,
        screenshot_data: bytes
    ) -> None:
        """Handle the verification decision (update DB, queue, etc.)"""

        if decision.status == 'auto_verified':
            # Auto-approve: update invoice and learn from success
            await self._mark_invoice_verified(decision.invoice_id, decision.ocr_result)

            # Learn from successful verification
            if decision.should_learn_from_result:
                await self.learning_service.learn_from_verification(
                    tenant_id=decision.tenant_id,
                    customer_id=decision.customer_id,
                    customer_name=invoice.get('customer_name', ''),
                    extracted_name=decision.ocr_result.recipient_name or '',
                    extracted_account=decision.ocr_result.account_number or '',
                    was_approved=True,
                    bank_name=decision.ocr_result.bank_name
                )

        elif decision.status == 'queued_for_review':
            # Add to verification queue
            queue_id = await self._add_to_verification_queue(
                decision, invoice, screenshot_data
            )
            decision.queue_id = queue_id

        # Log decision for monitoring
        await self._log_verification_decision(decision)

    async def _mark_invoice_verified(self, invoice_id: str, ocr_result: OCRResult) -> None:
        """Mark invoice as verified in database"""
        # This will depend on your specific database schema
        # Update both the main database and any cache/index
        pass

    async def _add_to_verification_queue(
        self,
        decision: VerificationDecision,
        invoice: dict,
        screenshot_data: bytes
    ) -> str:
        """Add verification to manual review queue"""

        # Store screenshot in GridFS if not already stored
        screenshot_id = await self._store_screenshot(screenshot_data)

        # Create queue entry
        queue_entry = {
            'tenant_id': decision.tenant_id,
            'customer_id': decision.customer_id,
            'invoice_id': decision.invoice_id,
            'screenshot_id': screenshot_id,

            'ocr_extracted': asdict(decision.ocr_result),
            'pattern_result': asdict(decision.pattern_result) if decision.pattern_result else None,

            'expected_values': {
                'customer_name': invoice.get('customer_name'),
                'amount': invoice.get('amount'),
                'currency': invoice.get('currency', 'KHR')
            },

            'confidence_scores': {
                'combined': decision.confidence,
                'ocr': decision.ocr_result.confidence,
                'pattern': decision.pattern_result.confidence if decision.pattern_result else 0.0
            },

            'status': 'pending',
            'priority': self._calculate_priority(decision.confidence),
            'created_at': datetime.now(timezone.utc)
        }

        result = await self.db['verification_queue'].insert_one(queue_entry)
        return str(result.inserted_id)

    async def _store_screenshot(self, screenshot_data: bytes) -> str:
        """Store screenshot in GridFS and return file ID"""
        # Use existing GridFS implementation
        # This should integrate with your existing screenshot storage
        pass

    def _calculate_priority(self, confidence: float) -> str:
        """Calculate queue priority based on confidence"""
        if confidence >= 0.7:
            return 'low'      # High confidence, quick review
        elif confidence >= 0.4:
            return 'medium'   # Medium confidence, normal review
        else:
            return 'high'     # Low confidence, careful review

    async def _log_verification_decision(self, decision: VerificationDecision) -> None:
        """Log verification decision for monitoring and analytics"""

        log_entry = {
            'timestamp': datetime.now(timezone.utc),
            'tenant_id': decision.tenant_id,
            'customer_id': decision.customer_id,
            'invoice_id': decision.invoice_id,

            'decision': {
                'status': decision.status,
                'confidence': decision.confidence,
                'reason': decision.reason
            },

            'ocr_model': decision.ocr_result.ocr_model,
            'ocr_confidence': decision.ocr_result.confidence,
            'pattern_confidence': decision.pattern_result.confidence if decision.pattern_result else None,

            'processing_time': decision.ocr_result.processing_time
        }

        await self.db['verification_decisions_log'].insert_one(log_entry)

    # Public methods for manual queue management

    async def approve_from_queue(
        self,
        queue_id: str,
        approved_by: str,
        corrections: Optional[dict] = None
    ) -> bool:
        """Approve a verification from the manual review queue"""

        # Get queue entry
        queue_entry = await self.db['verification_queue'].find_one({'_id': queue_id})
        if not queue_entry:
            return False

        # Apply corrections if provided
        extracted_name = corrections.get('recipient_name') if corrections else None
        extracted_name = extracted_name or queue_entry['ocr_extracted']['recipient_name']

        extracted_account = corrections.get('account_number') if corrections else None
        extracted_account = extracted_account or queue_entry['ocr_extracted']['account_number']

        # Learn from approval
        await self.learning_service.learn_from_verification(
            tenant_id=queue_entry['tenant_id'],
            customer_id=queue_entry['customer_id'],
            customer_name=queue_entry['expected_values']['customer_name'],
            extracted_name=extracted_name,
            extracted_account=extracted_account,
            was_approved=True
        )

        # Update queue status
        await self.db['verification_queue'].update_one(
            {'_id': queue_id},
            {
                '$set': {
                    'status': 'approved',
                    'approved_by': approved_by,
                    'approved_at': datetime.now(timezone.utc),
                    'corrections': corrections
                }
            }
        )

        # Mark invoice as verified
        await self._mark_invoice_verified(queue_entry['invoice_id'], queue_entry['ocr_extracted'])

        return True

    async def reject_from_queue(
        self,
        queue_id: str,
        rejected_by: str,
        reason: str
    ) -> bool:
        """Reject a verification from the manual review queue"""

        # Get queue entry
        queue_entry = await self.db['verification_queue'].find_one({'_id': queue_id})
        if not queue_entry:
            return False

        # Learn from rejection (this helps avoid false positives)
        await self.learning_service.learn_from_verification(
            tenant_id=queue_entry['tenant_id'],
            customer_id=queue_entry['customer_id'],
            customer_name=queue_entry['expected_values']['customer_name'],
            extracted_name=queue_entry['ocr_extracted']['recipient_name'],
            extracted_account=queue_entry['ocr_extracted']['account_number'],
            was_approved=False
        )

        # Update queue status
        await self.db['verification_queue'].update_one(
            {'_id': queue_id},
            {
                '$set': {
                    'status': 'rejected',
                    'rejected_by': rejected_by,
                    'rejected_at': datetime.now(timezone.utc),
                    'rejection_reason': reason
                }
            }
        )

        return True

    def _convert_bank_result_to_ocr(self, bank_result: BankFormatResult) -> OCRResult:
        """Convert bank format result to standardized OCRResult"""

        return OCRResult(
            success=bank_result.success,
            confidence=bank_result.confidence,
            amount=bank_result.amount,
            currency=bank_result.currency,
            recipient_name=bank_result.recipient_name,
            account_number=bank_result.account_number,
            transaction_id=bank_result.transaction_id,
            bank_name=bank_result.bank_name,
            transaction_date=bank_result.transaction_date,
            ocr_model="bank_format_recognizer",
            processing_time=bank_result.processing_time,
            raw_response={"bank_result": bank_result.__dict__},
            error_message=bank_result.error_message
        )


# Export for use in other modules
__all__ = ['VerificationCoordinator', 'OCRResult', 'VerificationDecision']